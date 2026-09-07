"""Availability of a plugin in the plugin directory."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..util.date import parse
from .payload import to_string


@dataclass(frozen=True)
class PluginStatus:
	"""Whether a plugin is closed, and why.

	A closed plugin keeps its record in the API, but is no longer downloadable.
	"""

	slug: str
	closed: bool
	name: str | None = None
	closed_date: datetime | None = None
	reason: str | None = None
	reason_text: str | None = None

	@classmethod
	def from_dict(cls, slug: str, data: dict[str, Any]) -> "PluginStatus":
		"""Build a status from a decoded plugins/info/1.0 payload."""
		return cls(
			slug=slug,
			closed=bool(data.get("closed")),
			name=to_string(data, "name"),
			closed_date=parse(to_string(data, "closed_date")),
			reason=to_string(data, "reason"),
			reason_text=to_string(data, "reason_text"),
		)
