"""Attributes describing a file or a directory in the repository."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class StorageAttributes(ABC):
	"""Attributes every entry of a directory listing carries."""

	TYPE_FILE: ClassVar[str] = "file"
	TYPE_DIRECTORY: ClassVar[str] = "dir"

	type: ClassVar[str]

	path: str
	visibility: str | None = None
	last_modified: int | None = None
	extra_metadata: dict[str, Any] = field(default_factory=dict)

	def is_file(self) -> bool:
		"""Whether the entry is a file."""
		return self.type == self.TYPE_FILE

	def is_dir(self) -> bool:
		"""Whether the entry is a directory."""
		return self.type == self.TYPE_DIRECTORY

	@abstractmethod
	def json_serialize(self) -> dict[str, Any]:
		"""Return the entry as a plain dictionary."""


@dataclass(frozen=True)
class FileAttributes(StorageAttributes):
	"""Attributes of a file."""

	type: ClassVar[str] = StorageAttributes.TYPE_FILE

	file_size: int | None = None
	mime_type: str | None = None

	def json_serialize(self) -> dict[str, Any]:
		"""Return the entry as a plain dictionary."""
		return {
			"type": self.type,
			"path": self.path,
			"file_size": self.file_size,
			"visibility": self.visibility,
			"last_modified": self.last_modified,
			"mime_type": self.mime_type,
			"extra_metadata": dict(self.extra_metadata),
		}


@dataclass(frozen=True)
class DirectoryAttributes(StorageAttributes):
	"""Attributes of a directory."""

	type: ClassVar[str] = StorageAttributes.TYPE_DIRECTORY

	def json_serialize(self) -> dict[str, Any]:
		"""Return the entry as a plain dictionary."""
		return {
			"type": self.type,
			"path": self.path,
			"visibility": self.visibility,
			"last_modified": self.last_modified,
			"extra_metadata": dict(self.extra_metadata),
		}
