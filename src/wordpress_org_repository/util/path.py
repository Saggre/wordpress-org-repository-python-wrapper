"""Utility class for handling file paths."""

import os


class Path:
	"""Joins and normalizes path strings around a configurable separator."""

	def __init__(self, separator: str = os.sep) -> None:
		"""Build a path helper joining around the given separator."""
		self.separator = separator

	def normalize(self, path: str) -> str:
		"""Normalize a path string to use the configured directory separator."""
		return path.replace("/", self.separator).replace("\\", self.separator)

	def explode(self, path: str) -> list[str]:
		"""Split a path string into its non-empty parts."""
		return [part for part in self.normalize(path).split(self.separator) if part]

	def join(self, *paths: str | None) -> str:
		"""Join two or more path strings into a canonical path.

		Empty and None parts are skipped. The result keeps a leading separator
		only when the first argument starts with one.
		"""
		parts: list[str] = []

		for path in paths:
			if not path:
				continue

			parts.extend(self.explode(path))

		result = self.separator.join(parts)

		if paths and paths[0] and self._starts_with_separator(paths[0]):
			result = self.separator + result.lstrip(self.separator)

		return result

	def _starts_with_separator(self, path: str) -> bool:
		return self.normalize(path).startswith(self.separator)
