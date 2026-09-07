"""Base configuration class for WordPress.org clients."""

from ..version import CLIENT_VERSION

DEFAULT_USER_AGENT = f"wordpress-org-repository-python-wrapper/{CLIENT_VERSION}"


class BaseClientConfig:
	"""Holds the base URL and user agent every client needs.

	Repository clients add a slug and a version through RepositoryClientConfig.
	"""

	def __init__(self, base_url: str, user_agent: str) -> None:
		"""Store the base URL requests go to, without a trailing slash, and the user agent they carry."""
		self._base_url = base_url.rstrip("/")
		self._user_agent = user_agent

	@property
	def base_url(self) -> str:
		"""The base URL the client sends its requests to."""
		return self._base_url

	@property
	def user_agent(self) -> str:
		"""The user agent sent with every request."""
		return self._user_agent
