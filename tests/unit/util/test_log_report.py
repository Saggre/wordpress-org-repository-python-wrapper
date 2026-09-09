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
	assert ElementTree.fromstring(create_request_body(1, 3, 2)).tag == "{svn:}log-report"  # noqa: S314


@pytest.mark.parametrize(
	("limit", "start_revision", "end_revision"),
	[
		(10, None, 0),
		(10, 3383710, 0),
		(0, 3383710, 3289318),
	],
)
def test_create_request_body_always_sends_an_end_revision(limit: int, start_revision: int | None, end_revision: int) -> None:
	"""The server answers 200 with an empty report when the end revision is missing, so every request carries one."""
	body = create_request_body(limit, start_revision, end_revision)

	assert f"<S:end-revision>{end_revision}</S:end-revision>" in body


def test_create_request_body_rejects_a_negative_end_revision() -> None:
	"""A negative end revision raises rather than reading as an empty history."""
	with pytest.raises(ValueError, match=r"^The end revision cannot be negative\.$"):
		create_request_body(10, None, -1)


def test_create_request_body_rejects_an_inverted_range() -> None:
	"""A start revision older than the end revision raises, since the server would answer oldest first."""
	with pytest.raises(ValueError, match=r"^The start revision 100 is older than the end revision 200\.$"):
		create_request_body(10, 100, 200)


def test_create_request_body_scopes_to_a_path() -> None:
	"""A path restricts the revisions the report selects."""
	assert "<S:path>trunk/admin</S:path>" in create_request_body(10, None, 0, "trunk/admin")


def test_create_request_body_escapes_the_path() -> None:
	"""A path carrying XML syntax is escaped, so the body stays parseable."""
	body = create_request_body(10, None, 0, "trunk/a&b")

	assert "<S:path>trunk/a&amp;b</S:path>" in body
	assert ElementTree.fromstring(body).tag == "{svn:}log-report"  # noqa: S314


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


def test_parse_response_reads_the_modification_flags() -> None:
	"""A content change is separated from a property only one."""
	paths = _entries()[0].paths

	assert paths[0].text_mods
	assert not paths[0].prop_mods
	assert not paths[1].text_mods


def test_parse_response_defaults_missing_modification_flags_to_false() -> None:
	"""A path reported without the flags reads as neither content nor property change."""
	body = (
		'<?xml version="1.0" encoding="utf-8"?>\n'
		'<S:log-report xmlns:S="svn:" xmlns:D="DAV:"><S:log-item>'
		'<S:deleted-path node-kind="file">/hello-dolly/trunk/gone.txt</S:deleted-path>'
		"<D:version-name>1</D:version-name></S:log-item></S:log-report>"
	)

	path = parse_response(body)[0].paths[0]

	assert not path.text_mods
	assert not path.prop_mods


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
