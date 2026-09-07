"""Functional tests for the plugin download client, against the live distribution host."""

import pytest

from wordpress_org_repository import ClientException, PluginDownloadClient

pytestmark = pytest.mark.network


@pytest.fixture
def client() -> PluginDownloadClient:
	"""Build a client for the live WordPress.org distribution host."""
	return PluginDownloadClient()


def test_get_zip_downloads_an_exact_version(client: PluginDownloadClient) -> None:
	"""A tagged release downloads as a zip archive."""
	zip_file = client.get_zip("hello-dolly", "1.7.2")

	assert zip_file.startswith(b"PK")
	assert len(zip_file) > 500


def test_get_zip_downloads_the_current_release(client: PluginDownloadClient) -> None:
	"""Without a version the current release downloads."""
	assert client.get_zip("hello-dolly").startswith(b"PK")


def test_get_zip_stream_downloads_an_exact_version(client: PluginDownloadClient) -> None:
	"""A release can be read as a stream."""
	with client.get_zip_stream("hello-dolly", "1.7.2") as stream:
		assert stream.readable()
		assert stream.read().startswith(b"PK")


def test_get_zip_throws_on_withdrawn_release(client: PluginDownloadClient) -> None:
	"""A release the host no longer serves raises with a 404."""
	with pytest.raises(ClientException) as error:
		client.get_zip("hello-dolly", "0.0.1")

	assert error.value.status == 404
