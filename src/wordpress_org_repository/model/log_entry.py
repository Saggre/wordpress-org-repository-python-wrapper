"""A single revision of the WordPress.org SVN repository."""

from dataclasses import dataclass, field
from datetime import datetime

from .log_path import LogPath


@dataclass(frozen=True)
class LogEntry:
	"""A commit, with the paths it changed."""

	revision: int
	author: str | None = None
	date: datetime | None = None
	message: str | None = None
	paths: list[LogPath] = field(default_factory=list)
