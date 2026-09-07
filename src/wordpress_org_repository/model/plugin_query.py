"""Parameters for a plugin query API request."""

from dataclasses import dataclass, field
from typing import Any

from .plugin_browse import PluginBrowse


@dataclass(frozen=True)
class PluginQuery:
	"""One page of the plugin directory to ask for.

	The API caps per_page at 250. fields toggles response sections on or off,
	e.g. {"sections": False, "contributors": True}.
	"""

	browse: PluginBrowse | None = None
	search: str | None = None
	tag: str | None = None
	author: str | None = None
	page: int = 1
	per_page: int = 250
	fields: dict[str, bool] = field(default_factory=dict)

	def to_request_parameters(self) -> dict[str, Any]:
		"""Build the parameters sent as request[...] in the query string."""
		parameters: dict[str, Any] = {"page": self.page, "per_page": self.per_page}

		if self.browse is not None:
			parameters["browse"] = self.browse.value

		filters = (("search", self.search), ("tag", self.tag), ("author", self.author))
		parameters.update({key: value for key, value in filters if value is not None})

		if self.fields:
			parameters["fields"] = encode_fields(self.fields)

		return parameters


def encode_fields(fields: dict[str, bool]) -> dict[str, str]:
	"""Encode the section toggles the way the API expects them, as "1" and "0"."""
	return {name: "1" if enabled else "0" for name, enabled in fields.items()}
