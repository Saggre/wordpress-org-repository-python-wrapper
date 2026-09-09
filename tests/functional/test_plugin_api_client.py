"""Functional tests for the plugin API client, against the live API."""

from datetime import datetime, timedelta, timezone

import pytest

from wordpress_org_repository import ClientException, PluginApiClient, PluginBrowse, PluginInfo, PluginQuery

pytestmark = pytest.mark.network


@pytest.fixture
def client() -> PluginApiClient:
	"""Build a client for the live WordPress.org plugin API."""
	return PluginApiClient()


def test_query_plugins_enumerates_recently_updated_plugins(client: PluginApiClient) -> None:
	"""The updated browse mode lists plugins released in the last day."""
	result = client.query_plugins(PluginQuery(browse=PluginBrowse.UPDATED, page=1, per_page=3))

	assert result.page == 1
	assert result.pages > 0
	assert result.results > 0
	assert len(result.plugins) == 3
	assert all(isinstance(plugin, PluginInfo) for plugin in result.plugins)

	timestamps = [plugin.last_updated for plugin in result.plugins if plugin.last_updated is not None]

	assert len(timestamps) == 3, "A plugin of the page has no parsed last update."

	# The head of this list is eventually consistent, so entries settle into place over the
	# following minutes and their order is not asserted. The newest entry still dates the page
	# and separates this browse mode from the others, whose newest release is days old.
	assert max(timestamps) > datetime.now(timezone.utc) - timedelta(days=1), "The page is not of recent updates."


def test_query_plugins_trims_and_enriches_the_payload(client: PluginApiClient) -> None:
	"""Field toggles switch bulky sections off and contributors on."""
	result = client.query_plugins(
		PluginQuery(
			browse=PluginBrowse.UPDATED,
			per_page=1,
			fields={
				"sections": False,
				"description": False,
				"screenshots": False,
				"icons": False,
				"contributors": True,
			},
		),
	)
	plugin = result.plugins[0]

	assert plugin.sections == {}
	assert "description" not in plugin.raw
	assert "screenshots" not in plugin.raw
	assert "icons" not in plugin.raw
	assert plugin.contributors
	assert plugin.author_profile is not None
	assert plugin.short_description is not None


def test_get_plugin_information_reads_the_versions_map(client: PluginApiClient) -> None:
	"""A plugin record carries its full versions map."""
	info = client.get_plugin_information("hello-dolly")

	assert info.slug == "hello-dolly"
	assert info.name == "Hello Dolly"
	assert info.added is not None
	assert info.added.strftime("%Y-%m-%d") == "2008-07-06"
	assert "matt" in info.contributors
	assert "1.5" in info.versions
	assert "1.7.2" in info.versions
	assert info.versions["1.7.2"] == "https://downloads.wordpress.org/plugin/hello-dolly.1.7.2.zip"


def test_get_plugin_information_trims_the_payload(client: PluginApiClient) -> None:
	"""Sections can be switched off without losing the versions map."""
	info = client.get_plugin_information("hello-dolly", {"sections": False})

	assert info.sections == {}
	assert info.versions


def test_get_plugin_information_throws_on_unknown_plugin(client: PluginApiClient) -> None:
	"""An unknown slug raises with a 404."""
	with pytest.raises(ClientException) as error:
		client.get_plugin_information("saggre-wordpress-org-repository-php-wrapper-unknown")

	assert error.value.status == 404


def test_get_plugin_status_reads_an_open_plugin(client: PluginApiClient) -> None:
	"""An open plugin is not closed."""
	status = client.get_plugin_status("hello-dolly")

	assert status.slug == "hello-dolly"
	assert status.closed is False
	assert status.closed_date is None


def test_get_plugin_status_reads_a_closed_plugin(client: PluginApiClient) -> None:
	"""A closed plugin reports when and why it was closed."""
	status = client.get_plugin_status("hana-flv-player")

	assert status.closed is True
	assert status.name == "Hana Flv Player"
	assert status.closed_date is not None
	assert status.closed_date.strftime("%Y-%m-%d") == "2021-06-21"
	assert status.reason == "security-issue"
	assert status.reason_text == "Security Issue"


def test_get_plugin_status_throws_on_unknown_plugin(client: PluginApiClient) -> None:
	"""An unknown slug raises with a 404."""
	with pytest.raises(ClientException) as error:
		client.get_plugin_status("saggre-wordpress-org-repository-php-wrapper-unknown")

	assert error.value.status == 404
