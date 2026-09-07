"""Configuration class for the WordPress.org plugin API client."""

from .base_client_config import DEFAULT_USER_AGENT, BaseClientConfig

DEFAULT_BASE_URL = "https://api.wordpress.org"


class PluginApiClientConfig(BaseClientConfig):
	"""Configuration for :class:`~wordpress_org_repository.plugin_api_client.PluginApiClient`."""

	def __init__(self, base_url: str = DEFAULT_BASE_URL, user_agent: str = DEFAULT_USER_AGENT) -> None:
		"""Configure a plugin API client, defaulting to the WordPress.org API host."""
		super().__init__(base_url, user_agent)
