"""Unit tests for the plugin query result page."""

from wordpress_org_repository import PluginInfo, PluginQueryResult

from ..helpers import json_fixture


def test_from_dict_reads_page() -> None:
	"""The page numbers and the plugins on the page are read."""
	result = PluginQueryResult.from_dict(json_fixture("query_plugins.json"))

	assert result.page == 1
	assert result.pages == 23931
	assert result.results == 71793
	assert len(result.plugins) == 3
	assert all(isinstance(plugin, PluginInfo) for plugin in result.plugins)


def test_from_dict_reads_plugins() -> None:
	"""Each plugin on the page is a full record."""
	plugin = PluginQueryResult.from_dict(json_fixture("query_plugins.json")).plugins[0]

	assert plugin.slug == "immowp-gestion-immobiliere"
	assert plugin.version == "2.0.3"
	assert plugin.last_updated is not None
	assert plugin.last_updated.isoformat(timespec="seconds") == "2026-09-07T16:21:00+00:00"
	assert list(plugin.contributors) == ["immowp"]
	assert "real-estate" in plugin.tags


def test_from_dict_reads_empty_page() -> None:
	"""A page past the end has no plugins but keeps its number."""
	result = PluginQueryResult.from_dict({"info": {"page": 2, "pages": 0, "results": 0}, "plugins": []})

	assert result.plugins == []
	assert result.page == 2
	assert result.results == 0
