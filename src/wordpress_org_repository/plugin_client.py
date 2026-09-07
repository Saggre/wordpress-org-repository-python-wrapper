"""WordPress.org plugin client."""

from .base_client import BaseClient
from .config.plugin_client_config import PluginClientConfig
from .filesystem.listing import DirectoryListing
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
