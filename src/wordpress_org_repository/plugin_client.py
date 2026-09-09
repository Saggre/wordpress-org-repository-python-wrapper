"""WordPress.org plugin client."""

import posixpath

from .base_client import BaseClient
from .config.plugin_client_config import PluginClientConfig
from .exceptions import TagNotFoundException
from .filesystem.listing import DirectoryListing
from .model.log_entry import LogEntry
from .model.log_path import LogPath
from .model.log_path_action import LogPathAction
from .util.path import Path


class PluginClient(BaseClient[PluginClientConfig]):
	"""Reads the files of a plugin from the WordPress.org plugin repository."""

	def get_tags_directory(self) -> DirectoryListing:
		"""List every tagged version of the plugin.

		Each entry is a DirectoryAttributes whose last_modified comes from the
		WebDAV getlastmodified property.
		"""
		tags_path = Path("/").join(self.config.slug, "tags")

		return self.get_filesystem().list_contents(tags_path)

	def get_tag_revisions(self, limit: int = 0) -> dict[str, LogEntry]:
		"""Map every published version to the revision that created its tag.

		Reads the tag history in one request, so without a limit the cost grows
		with the number of releases. A caller that only needs the newest releases
		can cap the revisions read, which is the whole cost of a diff for a plugin
		with a long history. A tag is a directory copy, so the entry also carries
		the trunk revision the release was cut from, in the copy_from_revision of
		its path.

		Ordered by revision, oldest release first. Version strings cannot be sorted
		as text, where '1.10.4' lands between '1.1.9' and '1.2.0', but revision
		numbers are monotonic.

		limit is the maximum number of tag revisions to read, newest first, and 0
		means no limit. A release usually takes one revision, but retagging a
		release and editing a file inside a tag take their own, so the window can
		hold fewer versions.

		Raises ClientException on a repository read error.
		"""
		tags_path = f"{self._get_root_path()}/tags"
		revisions: dict[str, LogEntry] = {}
		deleted: set[str] = set()

		for entry in self._get_log_for_path(self._get_root_path(), limit, None, 0, "tags"):
			for path in entry.paths:
				if path.node_kind != "dir" or path.action is LogPathAction.MODIFIED or posixpath.dirname(path.path) != tags_path:
					continue

				version = posixpath.basename(path.path)

				# The log runs newest first, so the newest event wins: a tag whose newest event is
				# a deletion no longer exists, and a recreated tag resolves to the copy the
				# repository actually holds.
				if version in revisions or version in deleted:
					continue

				if path.action is LogPathAction.DELETED:
					deleted.add(version)
				else:
					revisions[version] = entry

		return dict(reversed(revisions.items()))

	def diff_versions(self, old: str, new: str, limit: int = 0) -> dict[str, LogPath]:
		"""Return the files that changed between two published versions, keyed by path.

		Resolves both tags, then reads the revision range between them in a single
		request, which is the cheap alternative to downloading and comparing two
		complete trees.

		Vendors commonly commit the same edit to trunk and to the new tag, so both
		trees are read and deduplicated. The tag directory itself is a copy rather
		than a file change and is left out, as is anything committed to an unrelated
		tag in the same range. A deleted or copied directory is listed in place of
		the files it removed or brought along, since the log does not name them.

		Resolving the tags is the expensive half for a plugin with a long history,
		since it reads the whole tag log to find two revisions. A caller diffing
		consecutive releases can cap that read with limit, at the price of a
		TagNotFoundException for a version tagged before the window.

		Raises TagNotFoundException when either version has no tag in the revisions
		read, ValueError when the old version was not tagged before the new one,
		and ClientException on a repository read error.
		"""
		tags = self.get_tag_revisions(limit)

		for version in (old, new):
			if version not in tags:
				scope = f"the newest {limit} revisions of its tags" if limit > 0 else "the repository"

				raise TagNotFoundException(f'Version "{version}" of "{self.config.slug}" has no tag in {scope}.')

		if tags[old].revision >= tags[new].revision:
			raise ValueError(f'Version "{old}" was not tagged before version "{new}".')

		# The revision that creates a tag also fills it from trunk, so it belongs to the older
		# release rather than to the range between the two.
		log = self.get_changed_paths(tags[new].revision, tags[old].revision + 1)

		return self._normalize_paths(log, new)

	def _normalize_paths(self, log: list[LogEntry], version: str) -> dict[str, LogPath]:
		"""Reduce the paths of a revision range to one entry per file of the plugin tree."""
		root = self._get_root_path()
		prefixes = (f"{root}/trunk/", f"{root}/tags/{version}/")
		paths: dict[str, LogPath] = {}

		for entry in log:
			for path in entry.paths:
				# A plain directory add lists its files separately, but a deleted or copied
				# directory is the only trace of the files it removed or brought along.
				if path.node_kind == "dir" and path.action is not LogPathAction.DELETED and path.copy_from_path is None:
					continue

				relative = self._strip_prefix(path.path, prefixes)

				if relative is None:
					continue

				# A property only change in one tree must not hide a content change in the other,
				# but nothing older than a deletion can bring a path back.
				if relative in paths and (not path.text_mods or paths[relative].action is LogPathAction.DELETED):
					continue

				paths[relative] = LogPath(
					path=relative,
					action=path.action,
					node_kind=path.node_kind,
					copy_from_path=path.copy_from_path,
					copy_from_revision=path.copy_from_revision,
					text_mods=path.text_mods,
					prop_mods=path.prop_mods,
				)

		return {key: paths[key] for key in sorted(paths)}

	@staticmethod
	def _strip_prefix(path: str, prefixes: tuple[str, ...]) -> str | None:
		"""Strip the trunk or tag prefix from a repository absolute path, or None when it lies outside every tree."""
		for prefix in prefixes:
			if path.startswith(prefix):
				return path[len(prefix) :]

		return None
