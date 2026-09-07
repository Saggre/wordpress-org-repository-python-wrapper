"""Change types reported for a path in an SVN log entry."""

from enum import Enum


class LogPathAction(str, Enum):
	"""How a path changed in a revision, using the letters SVN reports."""

	ADDED = "A"
	MODIFIED = "M"
	DELETED = "D"
	REPLACED = "R"
