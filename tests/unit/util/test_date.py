"""Unit tests for WordPress.org date parsing."""

import pytest

from wordpress_org_repository.util.date import parse


@pytest.mark.parametrize(
	("expected", "value"),
	[
		("2025-10-24T04:13:00+00:00", "2025-10-24 4:13am GMT"),
		("2008-07-06T00:00:00+00:00", "2008-07-06"),
		("2025-10-24T04:13:10+00:00", "2025-10-24T04:13:10.489435Z"),
		("2025-10-24T02:13:00+00:00", "2025-10-24 04:13:00 +02:00"),
	],
)
def test_parse(expected: str, value: str) -> None:
	"""Every date shape WordPress.org uses is read as a UTC instant, never as host time."""
	parsed = parse(value)

	assert parsed is not None
	assert parsed.isoformat(timespec="seconds") == expected


@pytest.mark.parametrize("value", [None, "", "not a date"])
def test_parse_invalid(value: str | None) -> None:
	"""Empty and unparseable values give None."""
	assert parse(value) is None
