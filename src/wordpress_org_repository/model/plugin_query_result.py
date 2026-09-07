"""A single page of plugin query API results."""

from dataclasses import dataclass
from typing import Any

from .plugin_info import PluginInfo


@dataclass(frozen=True)
class PluginQueryResult:
	"""The plugins on one page, with the size of the whole result set."""

	plugins: list[PluginInfo]
	page: int
	pages: int
	results: int

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> "PluginQueryResult":
		"""Build a result page from a decoded API payload."""
		info = data.get("info") or {}

		return cls(
			plugins=[PluginInfo.from_dict(plugin) for plugin in data.get("plugins") or []],
			page=int(info.get("page", 1)),
			pages=int(info.get("pages", 0)),
			results=int(info.get("results", 0)),
		)
