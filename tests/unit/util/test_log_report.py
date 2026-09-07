"""Unit tests for the SVN log-report encoding and decoding."""

from xml.etree import ElementTree

import pytest

from wordpress_org_repository import ClientException, LogEntry, LogPathAction
from wordpress_org_repository.util.log_report import create_request_body, parse_response

from ..helpers import fixture


def _entries() -> list[LogEntry]:
	return parse_response(fixture("log_report.xml"))


def test_create_request_body_without_start_revision() -> None:
	"""Without a start revision the report starts at the youngest revision."""
	body = create_request_body(10)

	assert '<S:log-report xmlns:S="svn:" xmlns:D="DAV:">' in body
	assert "start-revision" not in body
	assert "<S:end-revision>0</S:end-revision>" in body
	assert "<S:limit>10</S:limit>" in body
	assert "<S:discover-changed-paths/>" in body


def test_create_request_body_with_revision_range() -> None:
	"""Both ends of a revision range are sent."""
	body = create_request_body(5, 3383710, 3289318)

	assert "<S:start-revision>3383710</S:start-revision>" in body
	assert "<S:end-revision>3289318</S:end-revision>" in body


def test_create_request_body_is_valid_xml() -> None:
	"""The body parses as XML."""
	assert ElementTree.fromstring(create_request_body(1, 2, 3)).tag == "{svn:}log-report"  # noqa: S314


def test_create_request_body_exact() -> None:
	"""The body is byte-identical to the one the PHP original sends."""
	assert create_request_body(5, 3383710, 3289318) == (
		'<?xml version="1.0" encoding="utf-8"?>\n'
		'<S:log-report xmlns:S="svn:" xmlns:D="DAV:">\n'
		"<S:start-revision>3383710</S:start-revision>\n"
		"<S:end-revision>3289318</S:end-revision>\n"
		"<S:limit>5</S:limit>\n"
		"<S:discover-changed-paths/>\n"
		"<S:revprop>svn:author</S:revprop>\n"
		"<S:revprop>svn:date</S:revprop>\n"
		"<S:revprop>svn:log</S:revprop>\n"
		"<S:path></S:path>\n"
		"</S:log-report>"
	)


def test_parse_response_reads_revisions() -> None:
	"""Every log item becomes an entry, newest first."""
	entries = _entries()

	assert len(entries) == 2
	assert all(isinstance(entry, LogEntry) for entry in entries)
	assert [entry.revision for entry in entries] == [3383710, 3289318]
	assert [entry.author for entry in entries] == ["dd32", "Otto42"]


def test_parse_response_reads_revision_details() -> None:
	"""The date and message of an entry are read."""
	entry = _entries()[1]

	assert entry.date is not None
	assert entry.date.isoformat(timespec="seconds") == "2025-05-07T16:50:12+00:00"
	assert entry.message == "Update tested up to value."


def test_parse_response_reads_changed_paths() -> None:
	"""Changed paths keep their order, action and node kind."""
	paths = _entries()[0].paths

	assert len(paths) == 3
	assert paths[0].path == "/hello-dolly/tags/1.7.2/readme.txt"
	assert paths[0].action is LogPathAction.MODIFIED
	assert paths[0].node_kind == "file"
	assert paths[1].path == "/hello-dolly/tags/1.7.3"
	assert paths[1].action is LogPathAction.DELETED
	assert paths[1].node_kind == "dir"
	assert paths[1].copy_from_path is None
	assert paths[1].copy_from_revision is None


def test_parse_response_reads_copied_paths() -> None:
	"""A copied path resolves where it was copied from."""
	body = (
		'<?xml version="1.0" encoding="utf-8"?>\n'
		'<S:log-report xmlns:S="svn:" xmlns:D="DAV:">\n'
		"<S:log-item>\n"
		'<S:added-path node-kind="dir" copyfrom-path="/hello-dolly/trunk"\n'
		'copyfrom-rev="2995208">/hello-dolly/tags/1.7.3</S:added-path>\n'
		"<D:version-name>2995248</D:version-name>\n"
		"</S:log-item>\n"
		"</S:log-report>"
	)

	path = parse_response(body)[0].paths[0]

	assert path.action is LogPathAction.ADDED
	assert path.copy_from_path == "/hello-dolly/trunk"
	assert path.copy_from_revision == 2995208


def test_parse_response_reads_empty_report() -> None:
	"""A report without log items gives no entries."""
	body = '<?xml version="1.0" encoding="utf-8"?>\n<S:log-report xmlns:S="svn:" xmlns:D="DAV:"></S:log-report>'

	assert parse_response(body) == []


def test_parse_response_throws_on_invalid_xml() -> None:
	"""A body that is not XML, such as an error page, raises."""
	with pytest.raises(ClientException, match=r"^Unable to parse the SVN log report response\.$"):
		parse_response("<html><body>Service unavailable")
