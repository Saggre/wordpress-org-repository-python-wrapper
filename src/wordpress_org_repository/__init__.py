"""A WordPress.org Repository API wrapper for Python."""

from .base_client import BaseClient
from .config import BaseClientConfig, PluginClientConfig, ThemeClientConfig
from .filesystem import (
	DirectoryAttributes,
	DirectoryListing,
	FileAttributes,
	FilesystemException,
	StorageAttributes,
	UnableToListContents,
	UnableToReadFile,
	WebDavFilesystem,
)
from .plugin_client import PluginClient
from .theme_client import ThemeClient
from .version import CLIENT_VERSION, __version__

__all__ = [
	"CLIENT_VERSION",
	"BaseClient",
	"BaseClientConfig",
	"DirectoryAttributes",
	"DirectoryListing",
	"FileAttributes",
	"FilesystemException",
	"PluginClient",
	"PluginClientConfig",
	"StorageAttributes",
	"ThemeClient",
	"ThemeClientConfig",
	"UnableToListContents",
	"UnableToReadFile",
	"WebDavFilesystem",
	"__version__",
]
