"""Unit tests for the plugin client's tag history and version diffing, against a stubbed transport."""

import pytest

from wordpress_org_repository import (
	ClientException,
	LogEntry,
	LogPath,
	LogPathAction,
	PluginClient,
	PluginClientConfig,
	TagNotFoundException,
)

from .helpers import fixture
from .stub import HttpClientStub, response


def _client(*responses: tuple[int, str]) -> tuple[PluginClient, HttpClientStub]:
	"""Build a client replaying the queued responses, with the stub it talks to."""
	http = HttpClientStub(*[response(status, body) for status, body in responses])

	return PluginClient(PluginClientConfig("demo-plugin"), http_client=http), http


def _diff_client() -> tuple[PluginClient, HttpClientStub]:
	"""Build a client replaying the tag history, then the diff of a version range."""
	return _client((200, fixture("tag_revisions.xml")), (200, fixture("version_diff.xml")))


def _body(http: HttpClientStub, index: int) -> str:
	request_body = http.requests[index].body

	assert request_body is not None

	return request_body.decode("utf-8")


def test_get_changed_paths_requests_the_revision_range() -> None:
	"""The range, the limit and the scope all reach the request body."""
	client, http = _client((200, fixture("version_diff.xml")))

	log = client.get_changed_paths(120, 115, "trunk/includes", 10)
	body = _body(http, 0)

	assert len(http.requests) == 1
	assert http.requests[0].method == "REPORT"
	assert http.requests[0].url == "https://plugins.svn.wordpress.org/demo-plugin"
	assert "<S:start-revision>120</S:start-revision>" in body
	assert "<S:end-revision>115</S:end-revision>" in body
	assert "<S:limit>10</S:limit>" in body
	assert "<S:path>trunk/includes</S:path>" in body
	assert [entry.revision for entry in log] == [120, 115, 112]


def test_get_changed_paths_rejects_an_inverted_range_before_sending() -> None:
	"""An inverted range never reaches the network."""
	client, http = _client()

	with pytest.raises(ValueError, match=r"^The start revision 115 is older than the end revision 120\.$"):
		client.get_changed_paths(115, 120)

	assert http.requests == []


def test_get_changed_paths_reports_failed_requests() -> None:
	"""An error status raises with the target path and the status."""
	client, _ = _client((404, "Not Found"))

	with pytest.raises(ClientException, match=r'^Unable to read the commit log of "/demo-plugin"\.$') as error:
		client.get_changed_paths(120, 115)

	assert error.value.status == 404


def test_get_tag_revisions_maps_versions_to_their_revisions() -> None:
	"""Every tag resolves to the revision that created it, scoped to the tags subtree."""
	client, http = _client((200, fixture("tag_revisions.xml")))

	tags = client.get_tag_revisions()

	assert all(isinstance(entry, LogEntry) for entry in tags.values())
	assert list(tags) == ["1.2.0", "1.9.0", "1.10.4", "1.1.9"]
	assert tags["1.10.4"].revision == 120
	assert "<S:path>tags</S:path>" in _body(http, 0)


def test_get_tag_revisions_orders_a_version_series_by_revision() -> None:
	"""Ordering by revision keeps 1.10.4 after 1.9.0, which sorting as text would not."""
	client, _ = _client((200, fixture("tag_revisions.xml")))

	versions = list(client.get_tag_revisions())

	assert versions.index("1.10.4") > versions.index("1.9.0"), "Versions are sorted as text, so 1.10.4 lands before 1.9.0."


def test_get_tag_revisions_resolves_a_recreated_tag_to_its_latest_copy() -> None:
	"""A tag that was deleted and cut again resolves to the copy the repository holds."""
	client, _ = _client((200, fixture("tag_revisions.xml")))

	tag = client.get_tag_revisions()["1.1.9"]

	assert tag.revision == 130
	assert tag.paths[0].copy_from_revision == 129
	assert tag.paths[0].copy_from_path == "/demo-plugin/trunk"


def test_get_tag_revisions_caps_the_history_it_reads() -> None:
	"""A limit caps the tag revisions the report returns, newest first."""
	client, http = _client((200, fixture("tag_revisions.xml")))

	client.get_tag_revisions(5)

	assert "<S:limit>5</S:limit>" in _body(http, 0)


def test_diff_versions_reads_the_range_between_two_tags() -> None:
	"""The diff costs one report beyond the tag history, over the range between the tags."""
	client, http = _diff_client()

	client.diff_versions("1.9.0", "1.10.4")
	body = _body(http, 1)

	assert len(http.requests) == 2, "The diff took more than one report beyond the tags."
	assert "<S:start-revision>120</S:start-revision>" in body
	assert "<S:end-revision>111</S:end-revision>" in body


def test_diff_versions_rejects_versions_tagged_out_of_order() -> None:
	"""An old version tagged after the new one raises before the range is requested."""
	client, http = _diff_client()

	with pytest.raises(ValueError, match=r'^Version "1\.10\.4" was not tagged before version "1\.9\.0"\.$'):
		client.diff_versions("1.10.4", "1.9.0")

	assert len(http.requests) == 1, "The range request reached the network."


def test_diff_versions_deduplicates_trunk_and_tag_paths() -> None:
	"""Paths come back relative to the plugin root, sorted and deduplicated across both trees."""
	client, _ = _diff_client()

	paths = client.diff_versions("1.9.0", "1.10.4")

	assert all(isinstance(path, LogPath) for path in paths.values())
	assert list(paths) == [
		"admin/settings.php",
		"includes/legacy",
		"includes/new-feature.php",
		"includes/old.php",
		"readme.txt",
		"style.css",
	]
	assert paths["readme.txt"].path == "readme.txt"


def test_diff_versions_keeps_a_deletion_over_an_older_edit() -> None:
	"""Nothing older than a deletion brings a path back, and a deleted directory is kept."""
	client, _ = _diff_client()

	paths = client.diff_versions("1.9.0", "1.10.4")

	assert paths["includes/old.php"].action is LogPathAction.DELETED, "The r112 edit revived the file."
	assert paths["includes/legacy"].action is LogPathAction.DELETED
	assert paths["includes/legacy"].node_kind == "dir"


def test_diff_versions_keeps_the_content_change_of_a_duplicated_path() -> None:
	"""A property only change in one tree does not hide the content change in the other."""
	client, _ = _diff_client()

	paths = client.diff_versions("1.9.0", "1.10.4")

	assert paths["style.css"].text_mods, "The property only tag copy hid the trunk edit."
	assert not paths["includes/old.php"].text_mods


def test_diff_versions_throws_on_an_untagged_version() -> None:
	"""A version that was never tagged raises rather than comparing the wrong pair."""
	client, _ = _diff_client()

	with pytest.raises(TagNotFoundException, match=r'^Version "1\.9\.1" of "demo-plugin" has no tag in the repository\.$'):
		client.diff_versions("1.9.1", "1.10.4")


def test_diff_versions_reports_a_version_tagged_before_its_limit() -> None:
	"""A version tagged before the capped window names the window rather than the repository."""
	client, http = _diff_client()
	message = r'^Version "1\.9\.1" of "demo-plugin" has no tag in the newest 2 revisions of its tags\.$'

	with pytest.raises(TagNotFoundException, match=message):
		client.diff_versions("1.9.1", "1.10.4", 2)

	assert "<S:limit>2</S:limit>" in _body(http, 0)
