"""Configuration class for the WordPress.org theme client."""

from .base_client_config import DEFAULT_USER_AGENT
from .repository_client_config import RepositoryClientConfig

DEFAULT_BASE_URL = "https://themes.svn.wordpress.org"


class ThemeClientConfig(RepositoryClientConfig):
	"""Configuration for :class:`~wordpress_org_repository.theme_client.ThemeClient`."""

	def __init__(
		self,
		slug: str,
		version: str = "trunk",
		base_url: str = DEFAULT_BASE_URL,
		user_agent: str = DEFAULT_USER_AGENT,
	) -> None:
		"""Configure a theme client, defaulting to trunk on the WordPress.org theme repository."""
		super().__init__(slug, version, base_url, user_agent)
