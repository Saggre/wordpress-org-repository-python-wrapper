"""WordPress.org plugin distribution client."""

import urllib.parse
from typing import IO

from . import version
from .config.plugin_download_client_config import PluginDownloadClientConfig
from .exceptions import ClientException
from .transport import HttpClient, HttpRequest, HttpResponse


class PluginDownloadClient:
	"""Downloads plugin releases from the WordPress.org distribution host.

	Only the current release is available without a version. Withdrawn releases
	are no longer served here even when they still exist in the SVN repository.
	"""

	CLIENT_VERSION = version.CLIENT_VERSION

	def __init__(self, config: PluginDownloadClientConfig | None = None, *, http_client: HttpClient | None = None) -> None:
		"""Build a client for the distribution host the config points at."""
		self.config = config or PluginDownloadClientConfig()
		self._http_client = http_client or HttpClient(self.config.user_agent)

	def get_zip_url(self, slug: str, version: str | None = None) -> str:
		"""Build the download URL of a plugin release, or of the current release when version is None."""
		suffix = "" if version is None else f".{urllib.parse.quote(version, safe='')}"

		return f"{self.config.base_url}/plugin/{urllib.parse.quote(slug, safe='')}{suffix}.zip"

	def get_zip(self, slug: str, version: str | None = None) -> bytes:
		"""Download a plugin release as bytes.

		Raises ClientException when the release is not available.
		"""
		return self._download(slug, version).read()

	def get_zip_stream(self, slug: str, version: str | None = None) -> IO[bytes]:
		"""Download a plugin release as a stream the caller closes.

		Raises ClientException when the release is not available.
		"""
		return self._download(slug, version).stream

	def _download(self, slug: str, version: str | None) -> HttpResponse:
		url = self.get_zip_url(slug, version)
		response = self._http_client.send(HttpRequest("GET", url))

		if not response.ok:
			response.stream.close()

			raise ClientException(f'Unable to download "{url}".', response.status)

		return response
