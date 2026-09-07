"""Configuration class for the WordPress.org plugin download client."""

from .base_client_config import DEFAULT_USER_AGENT, BaseClientConfig

DEFAULT_BASE_URL = "https://downloads.wordpress.org"


class PluginDownloadClientConfig(BaseClientConfig):
	"""Configuration for :class:`~wordpress_org_repository.plugin_download_client.PluginDownloadClient`."""

	def __init__(self, base_url: str = DEFAULT_BASE_URL, user_agent: str = DEFAULT_USER_AGENT) -> None:
		"""Configure a plugin download client, defaulting to the WordPress.org distribution host."""
		super().__init__(base_url, user_agent)
