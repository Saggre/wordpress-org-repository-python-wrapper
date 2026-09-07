"""Configuration class for the WordPress.org plugin client."""

from .base_client_config import DEFAULT_USER_AGENT
from .repository_client_config import RepositoryClientConfig

DEFAULT_BASE_URL = "https://plugins.svn.wordpress.org"


class PluginClientConfig(RepositoryClientConfig):
	"""Configuration for :class:`~wordpress_org_repository.plugin_client.PluginClient`."""

	def __init__(
		self,
		slug: str,
		version: str = "trunk",
		base_url: str = DEFAULT_BASE_URL,
		user_agent: str = DEFAULT_USER_AGENT,
	) -> None:
		"""Configure a plugin client, defaulting to trunk on the WordPress.org plugin repository."""
		super().__init__(slug, version, base_url, user_agent)
