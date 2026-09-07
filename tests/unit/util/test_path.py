"""Unit tests for the path helper."""

import pytest

from wordpress_org_repository.util.path import Path


@pytest.mark.parametrize(
	("expected", "separator", "path"),
	[
		("foo/bar/baz", "/", "foo\\bar\\baz"),
		("foo/bar/baz", "/", "foo/bar/baz"),
		("foo\\bar\\baz", "\\", "foo/bar/baz"),
		("\\foo\\bar\\baz", "\\", "\\foo\\bar\\baz"),
	],
)
def test_normalize(expected: str, separator: str, path: str) -> None:
	"""Both separators are rewritten to the configured one."""
	assert Path(separator).normalize(path) == expected


@pytest.mark.parametrize(
	("expected", "separator", "path"),
	[
		(["foo", "bar", "baz"], "/", "foo/bar/baz"),
		(["foo", "bar", "baz"], "/", "foo\\bar\\baz"),
		(["foo", "bar", "baz"], "\\", "foo/bar/baz"),
		(["foo", "bar", "baz"], "\\", "\\foo\\bar\\baz"),
		(["0", "foo"], "/", "0/foo"),
	],
)
def test_explode(expected: list[str], separator: str, path: str) -> None:
	"""Splitting drops the empty leading part but keeps a zero segment."""
	assert Path(separator).explode(path) == expected


@pytest.mark.parametrize(
	("expected", "separator", "parts"),
	[
		("foo/bar/baz", "/", ["foo", "bar", "baz"]),
		("/foo/bar/baz", "/", ["/foo/bar", "baz"]),
		("foo\\bar\\baz", "\\", ["foo", "bar", "baz"]),
		("\\foo\\bar\\baz", "\\", ["\\foo\\bar", "baz"]),
		("foo/bar/baz", "/", ["foo", None, "bar", "baz"]),
		("foo/baz", "/", ["foo", "", "baz"]),
		("foo/0/bar", "/", ["foo", "0", "bar"]),
	],
)
def test_join(expected: str, separator: str, parts: list[str | None]) -> None:
	"""Empty parts are skipped, zero segments are kept, and a leading separator is kept."""
	assert Path(separator).join(*parts) == expected
