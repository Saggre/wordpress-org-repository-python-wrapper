"""Readers for the loosely typed fields of a plugin API payload."""

from typing import Any


def to_string(data: dict[str, Any], key: str) -> str | None:
	"""Read a field the API returns either as a string or as false when it is not set."""
	value = data.get(key)

	return str(value) if value else None


def to_int(data: dict[str, Any], key: str) -> int | None:
	"""Read a numeric field, or None when it is absent."""
	value = data.get(key)

	return None if value is None else int(value)


def to_float(data: dict[str, Any], key: str) -> float | None:
	"""Read a numeric field, or None when it is absent."""
	value = data.get(key)

	return None if value is None else float(value)


def to_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
	"""Read a field the API returns either as a map or as false or an empty list when it is empty."""
	value = data.get(key)

	return dict(value) if isinstance(value, dict) else {}
