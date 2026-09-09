"""Functional tests for the plugin client, against the live repository."""

import pathlib

import pytest

from wordpress_org_repository import (
	DirectoryAttributes,
	LogEntry,
	LogPath,
	LogPathAction,
	PluginClient,
	PluginClientConfig,
	TagNotFoundException,
	UnableToListContents,
)

from .helpers import by_path, expected_directory_listing, expected_file_content

pytestmark = pytest.mark.network

GET_FILE_CASES = [
	("woocommerce", "9.6.2", "includes/class-wc-privacy-exporters.php"),
	("wordpress-seo", "25.5", "wpml-config.xml"),
]

GET_DIRECTORY_CASES = [
	("woocommerce", "9.6.2", "/i18n"),
	("wordpress-seo", "25.5", "/"),
]


@pytest.mark.parametrize(("slug", "version", "path"), GET_FILE_CASES)
def test_get_file(slug: str, version: str, path: str) -> None:
	"""The file content matches the snapshot byte for byte."""
	client = PluginClient(PluginClientConfig(slug, version))

	assert client.get_file(path) == expected_file_content(slug, version, path)


@pytest.mark.parametrize(("slug", "version", "path"), GET_FILE_CASES)
def test_get_file_stream(slug: str, version: str, path: str) -> None:
	"""The streamed file content matches the snapshot byte for byte."""
	client = PluginClient(PluginClientConfig(slug, version))

	with client.get_file_stream(path) as file_stream:
		assert file_stream.readable()
		assert file_stream.read() == expected_file_content(slug, version, path)


@pytest.mark.parametrize(("slug", "version", "path"), GET_DIRECTORY_CASES)
def test_get_directory(slug: str, version: str, path: str) -> None:
	"""The directory listing matches the snapshot, regardless of server order."""
	directory = [entry.json_serialize() for entry in PluginClient(PluginClientConfig(slug, version)).get_directory(path)]

	assert by_path(directory) == by_path(expected_directory_listing(slug, version, path))


def test_get_tags_directory_returns_version_list() -> None:
	"""Every tag is a directory carrying a last modified timestamp."""
	client = PluginClient(PluginClientConfig("akismet"))
	versions = list(client.get_tags_directory())

	assert versions
	assert all(isinstance(version, DirectoryAttributes) for version in versions)

	for directory in versions:
		assert directory.last_modified is not None, f"Tag {directory.path} missing last_modified"


def test_get_directory_is_lazy() -> None:
	"""Requesting a listing does not touch the repository until it is iterated."""
	client = PluginClient(PluginClientConfig("woocommerce", "9.6.2"))

	client.get_directory("/invalid/path")


def test_get_directory_invalid_path() -> None:
	"""Listing a missing directory raises on iteration, with the reason from the server."""
	client = PluginClient(PluginClientConfig("woocommerce", "9.6.2"))
	listing = client.get_directory("/invalid/path")

	with pytest.raises(UnableToListContents) as error:
		listing.to_array()

	assert str(error.value) == ("Unable to list contents for 'woocommerce/tags/9.6.2/invalid/path', shallow listing\n\nReason: Not Found")


def test_get_directory_deep_lists_subdirectories() -> None:
	"""A deep listing includes the contents of subdirectories."""
	client = PluginClient(PluginClientConfig("classic-editor", "1.6.7"))

	shallow = client.get_directory().to_array()
	deep = client.get_directory(deep=True).to_array()
	paths = [entry.path for entry in deep]

	assert len(shallow) == 5
	assert len(deep) == 8
	assert "classic-editor/tags/1.6.7/scripts/post.js" in paths


def test_export_writes_the_tree(tmp_path: pathlib.Path) -> None:
	"""Export writes every file of the version, nested directories included."""
	client = PluginClient(PluginClientConfig("classic-editor", "1.6.7"))

	files = client.export(tmp_path)

	assert files == 6
	assert (tmp_path / "scripts" / "post.js").read_bytes() == client.get_file("scripts/post.js")
	assert (tmp_path / "classic-editor.php").read_bytes() == client.get_file("classic-editor.php")


def test_get_log_reads_plugin_history() -> None:
	"""The log lists the plugin's revisions newest first, each with its paths."""
	client = PluginClient(PluginClientConfig("hello-dolly"))
	log = client.get_log(3)

	assert log
	assert len(log) <= 3
	assert all(isinstance(entry, LogEntry) for entry in log)

	revisions = [entry.revision for entry in log]

	assert revisions == sorted(revisions, reverse=True), "Revisions are not ordered newest first."

	for entry in log:
		assert entry.author
		assert entry.date is not None
		assert entry.paths
		assert all(isinstance(path, LogPath) for path in entry.paths)
		assert all(path.path.startswith("/hello-dolly/") for path in entry.paths)


def test_get_log_reads_a_revision_range() -> None:
	"""A single revision resolves the trunk a tag was copied from."""
	client = PluginClient(PluginClientConfig("hello-dolly"))
	log = client.get_log(1, 2995248, 2995248)

	assert len(log) == 1
	assert log[0].revision == 2995248
	assert log[0].author == "priethor"

	tag = log[0].paths[0]

	assert tag.path == "/hello-dolly/tags/1.7.3"
	assert tag.action is LogPathAction.ADDED
	assert tag.node_kind == "dir"
	assert tag.copy_from_path == "/hello-dolly/trunk"
	assert tag.copy_from_revision == 2995208


def test_get_repository_log_reads_every_plugin() -> None:
	"""The repository log spans every plugin, newest first."""
	client = PluginClient(PluginClientConfig("hello-dolly"))
	log = client.get_repository_log(2)

	assert len(log) == 2
	assert log[0].revision > log[1].revision

	for entry in log:
		assert entry.paths


def test_get_changed_paths_scopes_to_a_subtree() -> None:
	"""Scoping to the tags subtree selects only the revisions that touched it."""
	client = PluginClient(PluginClientConfig("hello-dolly"))
	log = client.get_changed_paths(2995248, 2995248, "tags")

	assert len(log) == 1
	assert log[0].paths[0].path == "/hello-dolly/tags/1.7.3"


def test_get_tag_revisions_resolves_published_versions() -> None:
	"""Every published version maps to the revision that created its tag."""
	client = PluginClient(PluginClientConfig("gdpr-cookie-consent"))
	tags = client.get_tag_revisions()

	assert tags["4.4.3"].revision == 3679495
	assert tags["4.4.4"].revision == 3686273

	# A tag is a directory copy, so it also names the trunk revision the release was cut from.
	copy = next(path for path in tags["4.4.4"].paths if path.path == "/gdpr-cookie-consent/tags/4.4.4")

	assert copy.action is LogPathAction.ADDED
	assert copy.node_kind == "dir"
	assert copy.copy_from_path == "/gdpr-cookie-consent/trunk"
	assert copy.copy_from_revision == 3686084


def test_get_tag_revisions_orders_a_version_series_by_revision() -> None:
	"""Ordering by revision keeps 1.10.0 after 1.9.4, which sorting as text would not."""
	client = PluginClient(PluginClientConfig("wp-super-cache"))
	versions = list(client.get_tag_revisions())

	assert versions.index("1.10.0") > versions.index("1.9.4"), "Releases are sorted as text, where 1.10.0 precedes 1.9.4."
	assert versions.index("1.9.4") > versions.index("1.1.1")


def test_diff_versions_finds_the_changed_files() -> None:
	"""The diff of two releases lists their changed files, relative to the plugin root."""
	client = PluginClient(PluginClientConfig("gdpr-cookie-consent"))
	paths = client.diff_versions("4.4.3", "4.4.4")
	php = [path for path in paths if path.endswith(".php")]

	# Matches a byte comparison of the two extracted trees.
	assert len(php) == 11
	assert "gdpr-cookie-consent.php" in php
	assert "admin/views/wizard.php" in php

	for key, path in paths.items():
		assert path.path == key, "Paths are keyed by something other than themselves."
		assert path.node_kind == "file", "The tag copy is reported as a change."
		assert not path.path.startswith("/"), "The repository prefix was not stripped."
		assert "tags/4.4.4" not in path.path


def test_diff_versions_throws_on_an_untagged_version() -> None:
	"""A version that was never tagged raises rather than comparing the wrong pair."""
	client = PluginClient(PluginClientConfig("gdpr-cookie-consent"))

	with pytest.raises(
		TagNotFoundException,
		match=r'^Version "99\.99\.99" of "gdpr-cookie-consent" has no tag in the repository\.$',
	):
		client.diff_versions("4.4.3", "99.99.99")
