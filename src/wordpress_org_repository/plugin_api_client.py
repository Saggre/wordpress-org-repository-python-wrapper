"""WordPress.org plugin API client."""

import json
import urllib.parse
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from . import version
from .config.plugin_api_client_config import PluginApiClientConfig
from .exceptions import ClientException
from .model.plugin_info import PluginInfo
from .model.plugin_query import PluginQuery, encode_fields
from .model.plugin_query_result import PluginQueryResult
from .model.plugin_status import PluginStatus
from .transport import HttpClient, HttpRequest


class PluginApiClient:
	"""Reads plugin metadata from the WordPress.org plugin API."""

	CLIENT_VERSION = version.CLIENT_VERSION

	def __init__(self, config: PluginApiClientConfig | None = None, *, http_client: HttpClient | None = None) -> None:
		"""Build a client for the API host the config points at."""
		self.config = config or PluginApiClientConfig()
		self._http_client = http_client or HttpClient(self.config.user_agent)

	def query_plugins(self, query: PluginQuery) -> PluginQueryResult:
		"""Query the plugin directory for a single page of plugins.

		Raises ClientException on an API error.
		"""
		status, data = self._get(self._get_query_url("query_plugins", query.to_request_parameters()))

		self._assert_success(data, status, "plugin query")

		return PluginQueryResult.from_dict(data)

	def get_plugin_information(self, slug: str, fields: dict[str, bool] | None = None) -> PluginInfo:
		"""Read the full record of a single plugin, including its versions map.

		fields toggles response sections on or off, e.g. {"sections": False}.
		Raises ClientException on an API error, including closed and unknown plugins.
		"""
		request: dict[str, Any] = {"slug": slug}

		if fields:
			request["fields"] = encode_fields(fields)

		status, data = self._get(self._get_query_url("plugin_information", request))

		self._assert_success(data, status, slug)

		return PluginInfo.from_dict(data)

	def get_plugin_status(self, slug: str) -> PluginStatus:
		"""Check whether a plugin is still available in the plugin directory.

		A closed plugin is reported with a non-2xx status, so the response body
		is the answer. Raises ClientException on any other API error, including
		unknown plugins.
		"""
		status, data = self._get(self._get_status_url(slug))

		if data.get("error") != "closed":
			self._assert_success(data, status, slug)

		return PluginStatus.from_dict(slug, data)

	def _get_query_url(self, action: str, request: dict[str, Any]) -> str:
		"""Build the URL of a plugins/info/1.2 request, with the parameters nested under request[...]."""
		query = urllib.parse.urlencode(_build_query({"action": action, "request": request}))

		return f"{self.config.base_url}/plugins/info/1.2/?{query}"

	def _get_status_url(self, slug: str) -> str:
		"""Build the URL of a plugins/info/1.0 request."""
		return f"{self.config.base_url}/plugins/info/1.0/{urllib.parse.quote(slug, safe='')}.json"

	def _get(self, url: str) -> tuple[int, dict[str, Any]]:
		"""Send a GET request and decode its JSON body, whatever the status.

		Raises ClientException when the body is not a JSON object.
		"""
		response = self._http_client.send(HttpRequest("GET", url))

		try:
			data = json.loads(response.read())
		except ValueError:
			data = None

		if not isinstance(data, dict):
			raise ClientException(f'Unable to decode the response of "{url}".', response.status)

		return response.status, data

	@staticmethod
	def _assert_success(data: dict[str, Any], status: int, subject: str) -> None:
		"""Raise when the API reported an error for the plugin slug or request named by subject."""
		error = data.get("error")

		if not error and status < HTTPStatus.BAD_REQUEST:
			return

		raise ClientException(f'Plugin API error for "{subject}": {error or f"HTTP {status}"}', status)


def _build_query(parameters: Mapping[str, Any], prefix: str = "") -> list[tuple[str, str]]:
	"""Flatten nested parameters the way PHP's http_build_query does, e.g. request[fields][sections]."""
	pairs: list[tuple[str, str]] = []

	for key, value in parameters.items():
		name = f"{prefix}[{key}]" if prefix else str(key)

		if isinstance(value, Mapping):
			pairs.extend(_build_query(value, name))
		else:
			pairs.append((name, str(value)))

	return pairs
