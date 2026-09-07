"""Parsing of the date formats used by WordPress.org."""

import re
from datetime import datetime, timezone

# The plugin API reports '2025-10-24 4:13am GMT' and bare '2008-07-06' dates, SVN reports
# ISO 8601 with fractional seconds and a Z suffix. Explicit offsets are honoured.
FORMATS = (
	"%Y-%m-%d %H:%M:%S",
	"%Y-%m-%d",
	"%Y-%m-%dT%H:%M:%S.%f%z",
	"%Y-%m-%dT%H:%M:%S%z",
	"%Y-%m-%d %H:%M:%S %z",
)

# strptime's %p depends on the host locale, so the 12-hour API form is rewritten to 24-hour first.
MERIDIEM = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{1,2}):(\d{2})(am|pm) GMT$", re.IGNORECASE)


def parse(value: str | None) -> datetime | None:
	"""Parse an API date string into an aware UTC datetime.

	WordPress.org reports times in UTC. Values that carry no zone of their own
	are read as UTC rather than as the host timezone, so the parsed instant does
	not depend on the environment. Returns None when the value is empty or
	cannot be parsed.
	"""
	if not value:
		return None

	match = MERIDIEM.match(value)

	if match:
		date, hour, minute, meridiem = match.groups()
		value = f"{date} {int(hour) % 12 + (12 if meridiem.lower() == 'pm' else 0):02d}:{minute}:00"

	for pattern in FORMATS:
		try:
			parsed = datetime.strptime(value, pattern)  # noqa: DTZ007
		except ValueError:
			continue

		if parsed.tzinfo is None:
			return parsed.replace(tzinfo=timezone.utc)

		return parsed.astimezone(timezone.utc)

	return None
