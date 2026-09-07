"""A single path changed by an SVN revision."""

from dataclasses import dataclass

from .log_path_action import LogPathAction


@dataclass(frozen=True)
class LogPath:
	"""A path touched by a revision, with where it was copied from when it is a copy.

	Tags are copies, so copy_from_path resolves the trunk a version was cut from.
	"""

	path: str
	action: LogPathAction
	node_kind: str | None = None
	copy_from_path: str | None = None
	copy_from_revision: int | None = None
