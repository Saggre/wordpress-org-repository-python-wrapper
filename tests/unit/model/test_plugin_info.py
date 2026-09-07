"""Unit tests for the plugin record model."""

from wordpress_org_repository import Contributor, PluginInfo

from ..helpers import json_fixture


def _plugin_info() -> PluginInfo:
	return PluginInfo.from_dict(json_fixture("plugin_information.json"))


def test_from_dict_reads_scalar_fields() -> None:
	"""Strings and numbers are read with their types."""
	info = _plugin_info()

	assert info.slug == "hello-dolly"
	assert info.name == "Hello Dolly"
	assert info.version == "1.7.2"
	assert info.author_profile == "https://profiles.wordpress.org/matt/"
	assert info.homepage == "http://wordpress.org/plugins/hello-dolly/"
	assert info.download_link == "https://downloads.wordpress.org/plugin/hello-dolly.1.7.2.zip"
	assert info.requires == "4.6"
	assert info.tested == "6.9.7"
	assert info.active_installs == 600000
	assert info.rating == 88.0
	assert info.num_ratings == 177


def test_from_dict_reads_versions_map() -> None:
	"""The versions map keeps the API order."""
	versions = _plugin_info().versions

	assert list(versions) == ["1.5", "1.6", "1.7.2", "trunk"]
	assert versions["1.6"] == "https://downloads.wordpress.org/plugin/hello-dolly.1.6.zip"


def test_from_dict_reads_contributors() -> None:
	"""Contributors are keyed by username with their record fields."""
	contributors = _plugin_info().contributors

	assert list(contributors) == ["matt", "wordpressdotorg"]
	assert all(isinstance(contributor, Contributor) for contributor in contributors.values())
	assert contributors["matt"].username == "matt"
	assert contributors["matt"].display_name == "Matt Mullenweg"
	assert contributors["matt"].profile == "https://profiles.wordpress.org/matt/"
	assert contributors["matt"].avatar is not None
	assert contributors["matt"].avatar.startswith("https://secure.gravatar.com/")


def test_from_dict_parses_dates() -> None:
	"""Both date shapes the API uses become UTC datetimes."""
	info = _plugin_info()

	assert info.last_updated is not None
	assert info.added is not None
	assert info.last_updated.isoformat(timespec="seconds") == "2025-10-24T04:13:00+00:00"
	assert info.added.isoformat(timespec="seconds") == "2008-07-06T00:00:00+00:00"


def test_from_dict_keeps_raw_payload() -> None:
	"""Sections and the whole payload stay reachable."""
	info = _plugin_info()

	assert info.sections["description"] == "<p>Only the smallest of plugins.</p>"
	assert info.raw["support_url"] == "https://wordpress.org/support/plugin/hello-dolly/"


def test_from_dict_reads_false_fields_as_empty() -> None:
	"""Fields the API reports as false or an empty list become None or empty."""
	info = _plugin_info()

	assert info.requires_php is None
	assert info.tags == {}


def test_from_dict_reads_trimmed_record() -> None:
	"""A record with nothing but a slug is valid."""
	info = PluginInfo.from_dict({"slug": "hello-dolly"})

	assert info.slug == "hello-dolly"
	assert info.name is None
	assert info.last_updated is None
	assert info.active_installs is None
	assert info.rating is None
	assert info.contributors == {}
	assert info.versions == {}
	assert info.sections == {}


def test_contributor_from_dict_reads_profile_string() -> None:
	"""The plugins/info/1.0 endpoint reports a contributor as a bare profile URL."""
	contributor = Contributor.from_dict("matt", "https://profiles.wordpress.org/matt/")

	assert contributor.username == "matt"
	assert contributor.profile == "https://profiles.wordpress.org/matt/"
	assert contributor.display_name is None
