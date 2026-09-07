"""Base configuration class for the WordPress.org SVN repository clients."""

from .base_client_config import BaseClientConfig


class RepositoryClientConfig(BaseClientConfig):
	"""Adds the slug and version of a plugin or theme to the base configuration."""

	def __init__(self, slug: str, version: str, base_url: str, user_agent: str) -> None:
		"""Raise ValueError when the slug or the version is empty."""
		if not slug:
			raise ValueError("Slug cannot be empty.")

		if not version:
			raise ValueError("Version cannot be empty.")

		super().__init__(base_url, user_agent)

		self._slug = slug
		self._version = version

	@property
	def slug(self) -> str:
		"""The slug of the plugin or theme."""
		return self._slug

	@property
	def version(self) -> str:
		"""The version of the plugin or theme."""
		return self._version
