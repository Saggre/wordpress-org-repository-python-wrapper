"""Encoding and decoding of the SVN log-report protocol used by the REPORT method."""

from xml.etree import ElementTree

from ..exceptions import ClientException
from ..model.log_entry import LogEntry
from ..model.log_path import LogPath
from ..model.log_path_action import LogPathAction
from .date import parse

NAMESPACE_SVN = "svn:"
NAMESPACE_DAV = "DAV:"


def _svn(name: str) -> str:
	return f"{{{NAMESPACE_SVN}}}{name}"


def _dav(name: str) -> str:
	return f"{{{NAMESPACE_DAV}}}{name}"


# Paths of a log item, by the element the server reports them under.
PATH_ELEMENTS = {
	_svn("added-path"): LogPathAction.ADDED,
	_svn("modified-path"): LogPathAction.MODIFIED,
	_svn("deleted-path"): LogPathAction.DELETED,
	_svn("replaced-path"): LogPathAction.REPLACED,
}


def create_request_body(limit: int, start_revision: int | None = None, end_revision: int = 0) -> str:
	"""Build the request body of a log-report.

	Revisions are returned newest first, starting from start_revision or the
	youngest revision when it is None, and stopping at end_revision.
	"""
	lines = [
		'<?xml version="1.0" encoding="utf-8"?>',
		f'<S:log-report xmlns:S="{NAMESPACE_SVN}" xmlns:D="{NAMESPACE_DAV}">',
	]

	if start_revision is not None:
		lines.append(f"<S:start-revision>{start_revision}</S:start-revision>")

	lines.extend(
		[
			f"<S:end-revision>{end_revision}</S:end-revision>",
			f"<S:limit>{limit}</S:limit>",
			"<S:discover-changed-paths/>",
			"<S:revprop>svn:author</S:revprop>",
			"<S:revprop>svn:date</S:revprop>",
			"<S:revprop>svn:log</S:revprop>",
			"<S:path></S:path>",
			"</S:log-report>",
		]
	)

	return "\n".join(lines)


def parse_response(body: bytes | str) -> list[LogEntry]:
	"""Parse the response body of a log-report into log entries, newest revision first.

	Raises ClientException on an unparseable response body.
	"""
	try:
		# The repository is a known endpoint, so the response is not treated as hostile XML.
		root = ElementTree.fromstring(body)  # noqa: S314
	except ElementTree.ParseError as error:
		raise ClientException("Unable to parse the SVN log report response.") from error

	return [
		LogEntry(
			revision=int(item.findtext(_dav("version-name")) or 0),
			author=item.findtext(_dav("creator-displayname")),
			date=parse(item.findtext(_svn("date"))),
			message=item.findtext(_dav("comment")),
			paths=_paths(item),
		)
		for item in root.iter(_svn("log-item"))
	]


def _paths(item: ElementTree.Element) -> list[LogPath]:
	"""Read the changed paths of a log item, in the order the server reports them."""
	paths = []

	for element in item:
		action = PATH_ELEMENTS.get(element.tag)

		if action is None:
			continue

		copy_from_revision = element.get("copyfrom-rev")

		paths.append(
			LogPath(
				path=element.text or "",
				action=action,
				node_kind=element.get("node-kind") or None,
				copy_from_path=element.get("copyfrom-path") or None,
				copy_from_revision=int(copy_from_revision) if copy_from_revision else None,
			)
		)

	return paths
