"""Exception raised by the WordPress.org API, download and log clients."""


class ClientException(Exception):  # noqa: N818
	"""Raised when a WordPress.org endpoint responds with an error or cannot be reached.

	The HTTP status of the response, when there is one, is exposed as status.
	"""

	def __init__(self, message: str, status: int | None = None) -> None:
		"""Build the exception with the message and, where there is one, the HTTP status."""
		super().__init__(message)
		self.status = status
