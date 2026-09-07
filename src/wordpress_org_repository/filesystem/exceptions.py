"""Exceptions raised by the filesystem layer.

The names mirror the League Flysystem exceptions the PHP original raises, so
`FilesystemException` stays the single type to catch for any read error.
"""


class FilesystemException(Exception):  # noqa: N818
	"""Base class for every error raised while reading the repository."""


class UnableToReadFile(FilesystemException):
	"""A file could not be read."""

	@classmethod
	def from_location(cls, location: str, reason: str) -> "UnableToReadFile":
		"""Build the error for a file that could not be read."""
		return cls(f"Unable to read file from location: {location}. {reason}")


class UnableToListContents(FilesystemException):
	"""A directory could not be listed."""

	@classmethod
	def at_location(cls, location: str, reason: str, *, deep: bool) -> "UnableToListContents":
		"""Build the error for a directory that could not be listed."""
		listing = "deep" if deep else "shallow"

		return cls(f"Unable to list contents for '{location}', {listing} listing\n\nReason: {reason}")
