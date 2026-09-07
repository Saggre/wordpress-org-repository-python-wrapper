"""Browse modes supported by the plugin query API."""

from enum import Enum


class PluginBrowse(str, Enum):
	"""Ordering of the plugin directory a query can ask for."""

	FEATURED = "featured"
	POPULAR = "popular"
	NEW = "new"
	UPDATED = "updated"
