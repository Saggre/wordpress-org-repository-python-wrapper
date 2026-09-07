"""Unit tests for the plugin query parameters."""

from wordpress_org_repository import PluginBrowse, PluginQuery


def test_to_request_parameters_defaults() -> None:
	"""A bare query asks for the first full page."""
	assert PluginQuery().to_request_parameters() == {"page": 1, "per_page": 250}


def test_to_request_parameters_enumerates_recently_updated_plugins() -> None:
	"""The browse mode is sent by its API value."""
	query = PluginQuery(browse=PluginBrowse.UPDATED, page=3, per_page=250)

	assert query.to_request_parameters() == {"page": 3, "per_page": 250, "browse": "updated"}


def test_to_request_parameters_toggles_fields() -> None:
	"""Field toggles are sent as the strings 1 and 0."""
	query = PluginQuery(
		fields={
			"sections": False,
			"description": False,
			"screenshots": False,
			"icons": False,
			"contributors": True,
		},
	)

	assert query.to_request_parameters()["fields"] == {
		"sections": "0",
		"description": "0",
		"screenshots": "0",
		"icons": "0",
		"contributors": "1",
	}


def test_to_request_parameters_omits_unused_filters() -> None:
	"""Filters left at None are not sent."""
	parameters = PluginQuery(search="seo").to_request_parameters()

	assert parameters["search"] == "seo"
	assert "tag" not in parameters
	assert "author" not in parameters
	assert "browse" not in parameters
	assert "fields" not in parameters


def test_to_request_parameters_includes_all_filters() -> None:
	"""Every filter set is sent."""
	query = PluginQuery(
		browse=PluginBrowse.POPULAR,
		search="cache",
		tag="performance",
		author="automattic",
		page=2,
		per_page=10,
	)

	assert query.to_request_parameters() == {
		"page": 2,
		"per_page": 10,
		"browse": "popular",
		"search": "cache",
		"tag": "performance",
		"author": "automattic",
	}
