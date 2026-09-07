"""Helpers for reading the snapshots the functional tests compare against."""

import json
import pathlib
from typing import Any

import pytest

EXPECTED_DIR = pathlib.Path(__file__).parent / "expected"


def expected_content_path(slug: str, version: str, path: str) -> pathlib.Path:
	"""Return the snapshot path of a plugin or theme file."""
	return EXPECTED_DIR.joinpath(slug, version, *path.strip("/").split("/"))


def expected_file_content(slug: str, version: str, path: str) -> bytes:
	"""Return the snapshot content of a plugin or theme file."""
	expected_path = expected_content_path(slug, version, path)

	if not expected_path.is_file():
		pytest.fail(f"File {expected_path} does not exist.")

	return expected_path.read_bytes()


def expected_directory_listing(slug: str, version: str, path: str) -> list[dict[str, Any]]:
	"""Return the snapshot listing of a plugin or theme directory."""
	expected_path = expected_content_path(slug, version, path)

	if not expected_path.is_dir():
		pytest.fail(f"Directory {expected_path} does not exist.")

	index = expected_path / "index.json"

	if not index.is_file():
		pytest.fail(f"Expected index.json file does not exist in {expected_path}.")

	listing: list[dict[str, Any]] = json.loads(index.read_text(encoding="utf-8"))

	return listing


def by_path(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""Sort entries by path, so listings compare independently of server order."""
	return sorted(entries, key=lambda entry: entry["path"])
