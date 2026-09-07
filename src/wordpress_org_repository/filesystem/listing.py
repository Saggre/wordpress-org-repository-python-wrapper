"""Lazy listing of directory contents."""

from collections.abc import Iterable, Iterator

from .attributes import StorageAttributes


class DirectoryListing(Iterable[StorageAttributes]):
	"""Wraps the entries of a directory.

	The listing is lazy: the repository is only contacted once the listing is
	iterated, so read errors surface there rather than on construction.
	"""

	def __init__(self, entries: Iterable[StorageAttributes]) -> None:
		"""Wrap the entries the repository returned."""
		self._entries = entries

	def __iter__(self) -> Iterator[StorageAttributes]:
		"""Iterate the entries, contacting the repository on the first step."""
		return iter(self._entries)

	def to_array(self) -> list[StorageAttributes]:
		"""Return every entry as a list."""
		return list(self)
