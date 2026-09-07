"""Unit tests for the repository client configuration."""

import pytest

from wordpress_org_repository import RepositoryClientConfig


class _Config(RepositoryClientConfig):
	"""Concrete subclass, standing in for the anonymous class the PHP test builds."""


def test_constructor_invalid_slug() -> None:
	"""An empty slug is rejected."""
	with pytest.raises(ValueError, match=r"^Slug cannot be empty\.$"):
		_Config("", "1.0.0", "https://example.com", "TestUserAgent/1.0")


def test_constructor_invalid_version() -> None:
	"""An empty version is rejected."""
	with pytest.raises(ValueError, match=r"^Version cannot be empty\.$"):
		_Config("test-plugin", "", "https://example.com", "TestUserAgent/1.0")
