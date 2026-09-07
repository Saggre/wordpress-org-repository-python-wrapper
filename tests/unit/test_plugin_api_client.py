"""Unit tests for the plugin API client, against a stubbed transport."""

from urllib.parse import unquote_plus

import pytest

from wordpress_org_repository import ClientException, PluginApiClient, PluginBrowse, PluginQuery

from .helpers import fixture
from .stub import HttpClientStub


def test_query_plugins_requests_the_query_endpoint() -> None:
	"""The query is sent nested under request[...] to the 1.2 endpoint."""
	http = HttpClientStub.respond_with(200, fixture("query_plugins.json"))

	PluginApiClient(http_client=http).query_plugins(
		PluginQuery(browse=PluginBrowse.UPDATED, page=2, per_page=250, fields={"sections": False, "contributors": True}),
	)

	url = unquote_plus(http.last_url)

	assert url.startswith("https://api.wordpress.org/plugins/info/1.2/?")
	assert "action=query_plugins" in url
	assert "request[browse]=updated" in url
	assert "request[page]=2" in url
	assert "request[per_page]=250" in url
	assert "request[fields][sections]=0" in url
	assert "request[fields][contributors]=1" in url


def test_query_plugins_returns_result_page() -> None:
	"""The response becomes a result page."""
	http = HttpClientStub.respond_with(200, fixture("query_plugins.json"))

	result = PluginApiClient(http_client=http).query_plugins(PluginQuery(browse=PluginBrowse.UPDATED))

	assert result.results == 71793
	assert len(result.plugins) == 3
	assert result.plugins[0].slug == "immowp-gestion-immobiliere"


def test_query_plugins_throws_on_api_error() -> None:
	"""An error body raises with the API message and the status."""
	http = HttpClientStub.respond_with(400, '{"error":"Invalid request."}')

	with pytest.raises(ClientException, match=r'^Plugin API error for "plugin query": Invalid request\.$') as error:
		PluginApiClient(http_client=http).query_plugins(PluginQuery())

	assert error.value.status == 400


def test_get_plugin_information_requests_the_slug() -> None:
	"""The slug and field toggles are sent nested under request[...]."""
	http = HttpClientStub.respond_with(200, fixture("plugin_information.json"))

	info = PluginApiClient(http_client=http).get_plugin_information("hello-dolly", {"sections": False})
	url = unquote_plus(http.last_url)

	assert "action=plugin_information" in url
	assert "request[slug]=hello-dolly" in url
	assert "request[fields][sections]=0" in url
	assert info.slug == "hello-dolly"
	assert "1.7.2" in info.versions


def test_get_plugin_information_throws_on_unknown_plugin() -> None:
	"""An unknown slug raises with the API message and a 404."""
	http = HttpClientStub.respond_with(404, '{"error":"Plugin not found."}')

	with pytest.raises(ClientException, match=r'^Plugin API error for "not-a-plugin": Plugin not found\.$') as error:
		PluginApiClient(http_client=http).get_plugin_information("not-a-plugin")

	assert error.value.status == 404


def test_get_plugin_information_throws_on_closed_plugin() -> None:
	"""A closed plugin has no record to read, so it raises."""
	http = HttpClientStub.respond_with(404, fixture("plugin_status_closed.json"))

	with pytest.raises(ClientException, match=r'^Plugin API error for "hana-flv-player": closed$'):
		PluginApiClient(http_client=http).get_plugin_information("hana-flv-player")


def test_get_plugin_status_requests_the_status_endpoint() -> None:
	"""The status comes from the 1.0 endpoint."""
	http = HttpClientStub.respond_with(200, fixture("plugin_status_open.json"))

	status = PluginApiClient(http_client=http).get_plugin_status("akismet")

	assert http.last_url == "https://api.wordpress.org/plugins/info/1.0/akismet.json"
	assert status.closed is False


def test_get_plugin_status_reads_the_body_of_a_non_success_response() -> None:
	"""A closed plugin is reported with a 404 whose body is the answer."""
	http = HttpClientStub.respond_with(404, fixture("plugin_status_closed.json"))

	status = PluginApiClient(http_client=http).get_plugin_status("hana-flv-player")

	assert status.closed is True
	assert status.reason == "security-issue"


def test_get_plugin_status_throws_on_unknown_plugin() -> None:
	"""Any error other than closed raises."""
	http = HttpClientStub.respond_with(404, '{"error":"Plugin not found."}')

	with pytest.raises(ClientException, match=r'^Plugin API error for "not-a-plugin": Plugin not found\.$'):
		PluginApiClient(http_client=http).get_plugin_status("not-a-plugin")


def test_throws_on_undecodable_response() -> None:
	"""A body that is not JSON raises with the status."""
	http = HttpClientStub.respond_with(503, "<html><body>Service Unavailable</body></html>")

	with pytest.raises(ClientException, match=r"^Unable to decode the response of") as error:
		PluginApiClient(http_client=http).get_plugin_information("hello-dolly")

	assert error.value.status == 503
