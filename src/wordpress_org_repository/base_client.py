"""Base class for WordPress.org plugin and theme clients."""

import os
import pathlib
import shutil
from typing import IO, Generic, TypeVar

from . import version
from .config.repository_client_config import RepositoryClientConfig
from .exceptions import ClientException
from .filesystem.listing import DirectoryListing
from .filesystem.webdav import WebDavFilesystem
from .model.log_entry import LogEntry
from .transport import HttpClient
from .util.log_report import create_request_body, parse_response
from .util.path import Path

ConfigT = TypeVar("ConfigT", bound=RepositoryClientConfig)


class BaseClient(Generic[ConfigT]):
	"""Reads files, directories and commit logs of a plugin or theme from WordPress.org.

	Subclassed by PluginClient and ThemeClient, which differ only in the config
	they take and in how they lay out a version in the repository path.
	"""

	CLIENT_VERSION = version.CLIENT_VERSION

	def __init__(self, config: ConfigT, *, http_client: HttpClient | None = None) -> None:
		"""Build a client reading through the repository the config points at.

		An http_client can be injected to replace the default urllib transport.
		"""
		self.config = config
		self._http_client = http_client
		self._filesystem = self._create_filesystem()

	def _create_filesystem(self) -> WebDavFilesystem:
		return WebDavFilesystem(self.config.base_url, self.config.user_agent, http_client=self._http_client)

	def get_filesystem(self) -> WebDavFilesystem:
		"""Return the filesystem the client reads through."""
		return self._filesystem

	def _get_path(self, path: str) -> str:
		"""Build the repository path of a plugin or theme file."""
		return Path("/").join(
			self.config.slug,
			None if self.config.version == "trunk" else "tags",
			self.config.version,
			path,
		)

	def get_file(self, path: str) -> bytes:
		"""Return the content of a file, relative to the plugin or theme root.

		Raises FilesystemException on a repository read error.
		"""
		return self.get_filesystem().read(self._get_path(path))

	def get_file_stream(self, path: str) -> IO[bytes]:
		"""Return the content of a file as a stream, relative to the plugin or theme root.

		Raises FilesystemException on a repository read error.
		"""
		return self.get_filesystem().read_stream(self._get_path(path))

	def get_directory(self, path: str = "", *, deep: bool = False) -> DirectoryListing:
		"""Return a listing of a directory, relative to the plugin or theme root.

		With deep, the contents of subdirectories are listed as well. The listing
		is lazy, so UnableToListContents is raised on iteration.
		"""
		return self.get_filesystem().list_contents(self._get_path(path), deep=deep)

	def export(self, destination: str | os.PathLike[str]) -> int:
		"""Write the tree of the configured version to a local directory.

		The repository equivalent of an svn export, which retrieves builds that
		are no longer available on the distribution host. The destination is
		created if it does not exist. Returns the number of files written.

		Raises ClientException when the destination cannot be written to, and
		FilesystemException on a repository read error.
		"""
		root = pathlib.Path(destination)
		remote = Path("/")
		base = len(self._get_path("").strip("/"))
		files = 0

		self._create_directory(root)

		for item in self.get_directory("", deep=True):
			parts = remote.explode(item.path.strip("/")[base:])

			if ".." in parts:
				continue

			target = root.joinpath(*parts)

			if item.is_dir():
				self._create_directory(target)

				continue

			self._write_file(target, self.get_filesystem().read_stream(item.path))
			files += 1

		return files

	def get_log(self, limit: int = 100, start_revision: int | None = None, end_revision: int = 0) -> list[LogEntry]:
		"""Return the commit log of the configured plugin or theme, newest revision first.

		start_revision defaults to the youngest revision. Raises ClientException
		on a repository read error.
		"""
		return self._get_log_for_path(Path("/").join("/", self.config.slug), limit, start_revision, end_revision)

	def get_repository_log(self, limit: int = 100, start_revision: int | None = None, end_revision: int = 0) -> list[LogEntry]:
		"""Return the commit log of the whole repository, newest revision first.

		A single revision spans every plugin or theme changed by that commit.
		start_revision defaults to the youngest revision. Raises ClientException
		on a repository read error.
		"""
		return self._get_log_for_path("/", limit, start_revision, end_revision)

	def _get_log_for_path(self, path: str, limit: int, start_revision: int | None, end_revision: int) -> list[LogEntry]:
		"""Run an SVN log-report against a repository absolute path."""
		response = self.get_filesystem().report(path, create_request_body(limit, start_revision, end_revision))

		if not response.ok:
			response.stream.close()

			raise ClientException(f'Unable to read the commit log of "{path}".', response.status)

		return parse_response(response.read())

	@staticmethod
	def _create_directory(path: pathlib.Path) -> None:
		try:
			path.mkdir(parents=True, exist_ok=True)
		except OSError as error:
			raise ClientException(f'Unable to create the directory "{path}".') from error

	@staticmethod
	def _write_file(path: pathlib.Path, stream: IO[bytes]) -> None:
		# The stream is entered first so it is closed even when the local file cannot be opened.
		try:
			with stream, path.open("wb") as handle:
				shutil.copyfileobj(stream, handle)
		except OSError as error:
			raise ClientException(f'Unable to write the file "{path}".') from error
