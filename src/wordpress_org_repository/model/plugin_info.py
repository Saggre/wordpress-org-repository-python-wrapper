"""A plugin record as returned by the plugin API."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..util.date import parse
from .contributor import Contributor
from .payload import to_dict, to_float, to_int, to_string


@dataclass(frozen=True)
class PluginInfo:
	"""A plugin record.

	Fields the API omits, either because the plugin has none or because they
	were switched off through PluginQuery.fields, are None or empty. The
	complete decoded payload is available in raw.
	"""

	slug: str
	name: str | None = None
	version: str | None = None
	author: str | None = None
	author_profile: str | None = None
	homepage: str | None = None
	donate_link: str | None = None
	short_description: str | None = None
	download_link: str | None = None
	requires: str | None = None
	requires_php: str | None = None
	tested: str | None = None
	last_updated: datetime | None = None
	added: datetime | None = None
	active_installs: int | None = None
	downloaded: int | None = None
	rating: float | None = None
	num_ratings: int | None = None
	contributors: dict[str, Contributor] = field(default_factory=dict)
	tags: dict[str, str] = field(default_factory=dict)
	versions: dict[str, str] = field(default_factory=dict)
	sections: dict[str, str] = field(default_factory=dict)
	raw: dict[str, Any] = field(default_factory=dict)

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> "PluginInfo":
		"""Build a plugin record from a decoded API payload."""
		contributors = {str(username): Contributor.from_dict(str(username), contributor) for username, contributor in to_dict(data, "contributors").items()}

		return cls(
			slug=str(data["slug"]),
			name=to_string(data, "name"),
			version=to_string(data, "version"),
			author=to_string(data, "author"),
			author_profile=to_string(data, "author_profile"),
			homepage=to_string(data, "homepage"),
			donate_link=to_string(data, "donate_link"),
			short_description=to_string(data, "short_description"),
			download_link=to_string(data, "download_link"),
			requires=to_string(data, "requires"),
			requires_php=to_string(data, "requires_php"),
			tested=to_string(data, "tested"),
			last_updated=parse(to_string(data, "last_updated")),
			added=parse(to_string(data, "added")),
			active_installs=to_int(data, "active_installs"),
			downloaded=to_int(data, "downloaded"),
			rating=to_float(data, "rating"),
			num_ratings=to_int(data, "num_ratings"),
			contributors=contributors,
			tags=to_dict(data, "tags"),
			versions=to_dict(data, "versions"),
			sections=to_dict(data, "sections"),
			raw=data,
		)
