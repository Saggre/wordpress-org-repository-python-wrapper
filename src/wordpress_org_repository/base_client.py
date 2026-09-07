"""Base class for WordPress.org plugin and theme clients."""

from typing import IO, Generic, TypeVar

from . import version
from .config.base_client_config import BaseClientConfig
from .filesystem.listing import DirectoryListing
from .filesystem.webdav import WebDavFilesystem
from .util.path import Path

ConfigT = TypeVar("ConfigT", bound=BaseClientConfig)


class BaseClient(Generic[ConfigT]):
	"""Reads files and directories of a plugin or theme from WordPress.org.

	Subclassed by PluginClient and ThemeClient, which differ only in the config
	they take and in how they lay out a version in the repository path.
	"""

	CLIENT_VERSION = version.CLIENT_VERSION

	def __init__(self, config: ConfigT) -> None:
		"""Build a client reading through the repository the config points at."""
		self.config = config
		self._filesystem = self._create_filesystem()

	def _create_filesystem(self) -> WebDavFilesystem:
		return WebDavFilesystem(self.config.base_url, self.config.user_agent)

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

	def get_directory(self, path: str) -> DirectoryListing:
		"""Return a listing of a directory, relative to the plugin or theme root.

		The listing is lazy, so UnableToListContents is raised on iteration.
		"""
		return self.get_filesystem().list_contents(self._get_path(path))
