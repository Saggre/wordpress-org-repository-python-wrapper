"""Unit tests for the repository client's commit log, against a stubbed transport."""

import pytest

from wordpress_org_repository import ClientException, PluginClient, PluginClientConfig
from wordpress_org_repository.util.log_report import create_request_body

from .helpers import fixture
from .stub import HttpClientStub


def test_get_log_sends_a_log_report() -> None:
	"""The log is read with a REPORT request against the plugin's path."""
	http = HttpClientStub.respond_with(200, fixture("log_report.xml"))

	log = PluginClient(PluginClientConfig("hello-dolly"), http_client=http).get_log(3)
	request = http.requests[-1]

	assert request.method == "REPORT"
	assert request.url == "https://plugins.svn.wordpress.org/hello-dolly"
	assert request.headers["Content-Type"] == "text/xml"
	assert request.body == create_request_body(3).encode("utf-8")
	assert [entry.revision for entry in log] == [3383710, 3289318]


def test_get_log_throws_on_error_status() -> None:
	"""An error status raises with the path and the status."""
	http = HttpClientStub.respond_with(404, "")

	with pytest.raises(ClientException, match=r'^Unable to read the commit log of "/hello-dolly"\.$') as error:
		PluginClient(PluginClientConfig("hello-dolly"), http_client=http).get_log()

	assert error.value.status == 404


def test_get_repository_log_targets_the_root() -> None:
	"""The repository log is read against the repository root."""
	http = HttpClientStub.respond_with(200, fixture("log_report.xml"))

	PluginClient(PluginClientConfig("hello-dolly"), http_client=http).get_repository_log(2)

	assert http.last_url == "https://plugins.svn.wordpress.org/"
