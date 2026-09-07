"""Base configuration class for WordPress.org plugin and theme clients."""

from ..version import CLIENT_VERSION

DEFAULT_USER_AGENT = f"wordpress-org-repository-python-wrapper/{CLIENT_VERSION}"


class BaseClientConfig:
	"""Holds the slug, version, base URL and user agent a client needs.

	Subclassed by PluginClientConfig and ThemeClientConfig, which supply the
	defaults of their respective repository.
	"""

	def __init__(self, slug: str, version: str, base_url: str, user_agent: str) -> None:
		"""Raise ValueError when the slug or the version is empty."""
		if not slug:
			raise ValueError("Slug cannot be empty.")

		if not version:
			raise ValueError("Version cannot be empty.")

		self._slug = slug
		self._version = version
		self._base_url = base_url
		self._user_agent = user_agent

	@property
	def slug(self) -> str:
		"""The slug of the plugin or theme."""
		return self._slug

	@property
	def version(self) -> str:
		"""The version of the plugin or theme."""
		return self._version

	@property
	def base_url(self) -> str:
		"""The base URL of the repository."""
		return self._base_url

	@property
	def user_agent(self) -> str:
		"""The user agent sent with every request."""
		return self._user_agent
