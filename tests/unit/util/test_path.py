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
	],
)
def test_explode(expected: list[str], separator: str, path: str) -> None:
	"""Splitting drops the empty leading part."""
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
	],
)
def test_join(expected: str, separator: str, parts: list[str | None]) -> None:
	"""Empty parts are skipped and a leading separator is kept."""
	assert Path(separator).join(*parts) == expected
