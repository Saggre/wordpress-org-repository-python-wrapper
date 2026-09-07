"""WordPress.org theme client."""

from .base_client import BaseClient
from .config.theme_client_config import ThemeClientConfig
from .util.path import Path


class ThemeClient(BaseClient[ThemeClientConfig]):
	"""Reads the files of a theme from the WordPress.org theme repository."""

	def _get_path(self, path: str) -> str:
		"""Theme versions live directly under the slug, with no tags directory."""
		return Path("/").join(self.config.slug, self.config.version, path)
