"""Functional tests for the theme client, against the live repository."""

import pytest

from wordpress_org_repository import ThemeClient, ThemeClientConfig, UnableToListContents

from .helpers import by_path, expected_directory_listing, expected_file_content

pytestmark = pytest.mark.network

GET_FILE_CASES = [
	("twentytwentyfive", "1.2", "theme.json"),
]

GET_DIRECTORY_CASES = [
	("twentytwentyfive", "1.2", "/"),
]


@pytest.mark.parametrize(("slug", "version", "path"), GET_FILE_CASES)
def test_get_file(slug: str, version: str, path: str) -> None:
	"""The file content matches the snapshot byte for byte."""
	client = ThemeClient(ThemeClientConfig(slug, version))

	assert client.get_file(path) == expected_file_content(slug, version, path)


@pytest.mark.parametrize(("slug", "version", "path"), GET_FILE_CASES)
def test_get_file_stream(slug: str, version: str, path: str) -> None:
	"""The streamed file content matches the snapshot byte for byte."""
	client = ThemeClient(ThemeClientConfig(slug, version))

	with client.get_file_stream(path) as file_stream:
		assert file_stream.readable()
		assert file_stream.read() == expected_file_content(slug, version, path)


@pytest.mark.parametrize(("slug", "version", "path"), GET_DIRECTORY_CASES)
def test_get_directory(slug: str, version: str, path: str) -> None:
	"""The directory listing matches the snapshot, regardless of server order."""
	directory = [entry.json_serialize() for entry in ThemeClient(ThemeClientConfig(slug, version)).get_directory(path)]

	assert by_path(directory) == by_path(expected_directory_listing(slug, version, path))


def test_get_directory_invalid_path() -> None:
	"""Listing a missing directory raises on iteration, with the reason from the server."""
	client = ThemeClient(ThemeClientConfig("twentytwentyfive", "0.0.1"))
	listing = client.get_directory("/invalid/path")

	with pytest.raises(UnableToListContents) as error:
		listing.to_array()

	assert str(error.value) == ("Unable to list contents for 'twentytwentyfive/0.0.1/invalid/path', shallow listing\n\nReason: Not Found")
