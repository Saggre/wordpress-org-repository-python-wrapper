"""Unit tests for the plugin status model."""

from wordpress_org_repository import PluginStatus

from ..helpers import json_fixture


def test_from_dict_reads_closed_plugin() -> None:
	"""A closed plugin carries the date and reason it was closed."""
	status = PluginStatus.from_dict("hana-flv-player", json_fixture("plugin_status_closed.json"))

	assert status.slug == "hana-flv-player"
	assert status.closed is True
	assert status.name == "Hana Flv Player"
	assert status.closed_date is not None
	assert status.closed_date.strftime("%Y-%m-%d") == "2021-06-21"
	assert status.reason == "security-issue"
	assert status.reason_text == "Security Issue"


def test_from_dict_reads_open_plugin() -> None:
	"""An open plugin has no closing details."""
	status = PluginStatus.from_dict("akismet", json_fixture("plugin_status_open.json"))

	assert status.slug == "akismet"
	assert status.closed is False
	assert status.name is not None
	assert "Akismet" in status.name
	assert status.closed_date is None
	assert status.reason is None
	assert status.reason_text is None
