"""A plugin contributor as returned by the plugin API."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Contributor:
	"""One entry of a plugin's contributors map, keyed by WordPress.org username."""

	username: str
	display_name: str | None = None
	profile: str | None = None
	avatar: str | None = None

	@classmethod
	def from_dict(cls, username: str, data: dict[str, Any] | str) -> "Contributor":
		"""Build a contributor from a single entry of the API contributors map.

		The plugins/info/1.0 endpoint reports each contributor as a bare profile
		URL rather than a record, so a string is read as the profile.
		"""
		if isinstance(data, str):
			return cls(username, profile=data)

		return cls(
			username,
			display_name=data.get("display_name"),
			profile=data.get("profile"),
			avatar=data.get("avatar"),
		)
