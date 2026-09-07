"""Unit tests for the plugin download client, against a stubbed transport."""

import pytest

from wordpress_org_repository import ClientException, PluginDownloadClient

from .stub import HttpClientStub


@pytest.mark.parametrize(
	("expected", "slug", "version"),
	[
		("https://downloads.wordpress.org/plugin/hello-dolly.zip", "hello-dolly", None),
		("https://downloads.wordpress.org/plugin/hello-dolly.1.7.2.zip", "hello-dolly", "1.7.2"),
		("https://downloads.wordpress.org/plugin/woo%2Fcommerce.zip", "woo/commerce", None),
	],
)
def test_get_zip_url(expected: str, slug: str, version: str | None) -> None:
	"""The URL names the release, and escapes the slug fully."""
	assert PluginDownloadClient().get_zip_url(slug, version) == expected


def test_get_zip_downloads_the_release() -> None:
	"""An exact version is requested and returned as bytes."""
	http = HttpClientStub.respond_with(200, "PK zip contents")

	zip_file = PluginDownloadClient(http_client=http).get_zip("hello-dolly", "1.7.2")

	assert zip_file == b"PK zip contents"
	assert http.last_url == "https://downloads.wordpress.org/plugin/hello-dolly.1.7.2.zip"


def test_get_zip_downloads_the_current_release() -> None:
	"""Without a version the current release is requested."""
	http = HttpClientStub.respond_with(200, "PK zip contents")

	PluginDownloadClient(http_client=http).get_zip("hello-dolly")

	assert http.last_url == "https://downloads.wordpress.org/plugin/hello-dolly.zip"


def test_get_zip_stream_returns_a_stream() -> None:
	"""The release can be read as a stream."""
	http = HttpClientStub.respond_with(200, "PK zip contents")

	with PluginDownloadClient(http_client=http).get_zip_stream("hello-dolly", "1.7.2") as stream:
		assert stream.read() == b"PK zip contents"


def test_get_zip_throws_on_withdrawn_release() -> None:
	"""A release the host no longer serves raises with the URL and the status."""
	http = HttpClientStub.respond_with(404, "Not Found")

	with pytest.raises(
		ClientException,
		match=r'^Unable to download "https://downloads\.wordpress\.org/plugin/hello-dolly\.0\.0\.1\.zip"\.$',
	) as error:
		PluginDownloadClient(http_client=http).get_zip("hello-dolly", "0.0.1")

	assert error.value.status == 404
