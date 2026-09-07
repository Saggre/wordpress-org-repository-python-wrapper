"""Functional tests for the plugin client, against the live repository."""

import pytest

from wordpress_org_repository import (
	DirectoryAttributes,
	PluginClient,
	PluginClientConfig,
	UnableToListContents,
)

from .helpers import by_path, expected_directory_listing, expected_file_content

pytestmark = pytest.mark.network

GET_FILE_CASES = [
	("woocommerce", "9.6.2", "includes/class-wc-privacy-exporters.php"),
	("wordpress-seo", "25.5", "wpml-config.xml"),
]

GET_DIRECTORY_CASES = [
	("woocommerce", "9.6.2", "/i18n"),
	("wordpress-seo", "25.5", "/"),
]


@pytest.mark.parametrize(("slug", "version", "path"), GET_FILE_CASES)
def test_get_file(slug: str, version: str, path: str) -> None:
	"""The file content matches the snapshot byte for byte."""
	client = PluginClient(PluginClientConfig(slug, version))

	assert client.get_file(path) == expected_file_content(slug, version, path)


@pytest.mark.parametrize(("slug", "version", "path"), GET_FILE_CASES)
def test_get_file_stream(slug: str, version: str, path: str) -> None:
	"""The streamed file content matches the snapshot byte for byte."""
	client = PluginClient(PluginClientConfig(slug, version))

	with client.get_file_stream(path) as file_stream:
		assert file_stream.readable()
		assert file_stream.read() == expected_file_content(slug, version, path)


@pytest.mark.parametrize(("slug", "version", "path"), GET_DIRECTORY_CASES)
def test_get_directory(slug: str, version: str, path: str) -> None:
	"""The directory listing matches the snapshot, regardless of server order."""
	directory = [entry.json_serialize() for entry in PluginClient(PluginClientConfig(slug, version)).get_directory(path)]

	assert by_path(directory) == by_path(expected_directory_listing(slug, version, path))


def test_get_tags_directory_returns_version_list() -> None:
	"""Every tag is a directory carrying a last modified timestamp."""
	client = PluginClient(PluginClientConfig("akismet"))
	versions = list(client.get_tags_directory())

	assert versions
	assert all(isinstance(version, DirectoryAttributes) for version in versions)

	for directory in versions:
		assert directory.last_modified is not None, f"Tag {directory.path} missing last_modified"


def test_get_directory_is_lazy() -> None:
	"""Requesting a listing does not touch the repository until it is iterated."""
	client = PluginClient(PluginClientConfig("woocommerce", "9.6.2"))

	client.get_directory("/invalid/path")


def test_get_directory_invalid_path() -> None:
	"""Listing a missing directory raises on iteration, with the reason from the server."""
	client = PluginClient(PluginClientConfig("woocommerce", "9.6.2"))
	listing = client.get_directory("/invalid/path")

	with pytest.raises(UnableToListContents) as error:
		listing.to_array()

	assert str(error.value) == ("Unable to list contents for 'woocommerce/tags/9.6.2/invalid/path', shallow listing\n\nReason: Not Found")
