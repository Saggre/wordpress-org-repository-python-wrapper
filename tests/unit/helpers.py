"""Helpers for reading the fixtures the unit tests are built on."""

import json
import pathlib
from typing import Any

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
	"""Return the raw content of a fixture file."""
	path = FIXTURES_DIR / name

	if not path.is_file():
		pytest.fail(f"Fixture {path} does not exist.")

	return path.read_text(encoding="utf-8")


def json_fixture(name: str) -> dict[str, Any]:
	"""Return the decoded content of a JSON fixture file."""
	data: dict[str, Any] = json.loads(fixture(name))

	return data
