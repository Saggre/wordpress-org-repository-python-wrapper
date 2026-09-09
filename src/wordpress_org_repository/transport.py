"""Shared HTTP transport, built on urllib, used by every client."""

import gzip
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from email.message import Message
from http import HTTPStatus
from typing import IO, TYPE_CHECKING, cast

from .exceptions import ClientException

if TYPE_CHECKING:
	import http.client


@dataclass(frozen=True)
class HttpRequest:
	"""An HTTP request to send."""

	method: str
	url: str
	headers: dict[str, str] = field(default_factory=dict)
	body: bytes | None = None


@dataclass(frozen=True)
class HttpResponse:
	"""An HTTP response whose body is still unread."""

	status: int
	reason: str
	headers: Message
	stream: IO[bytes]

	@property
	def ok(self) -> bool:
		"""Whether the status is below 400."""
		return self.status < HTTPStatus.BAD_REQUEST

	def read(self) -> bytes:
		"""Read the whole body and close the stream."""
		with self.stream as stream:
			return stream.read()


class HttpClient:
	"""Sends requests and hands back every response, whatever its status.

	Error statuses are returned rather than raised, because the WordPress.org
	APIs put meaningful bodies on them. Transport failures, such as a DNS or
	connection error, raise ClientException without a status.
	"""

	def __init__(self, user_agent: str, timeout: float = 30.0) -> None:
		"""Build a client identifying itself with the given user agent."""
		self.user_agent = user_agent
		self.timeout = timeout

	def send(self, request: HttpRequest) -> HttpResponse:
		"""Send a request and return the response, error statuses included."""
		prepared = urllib.request.Request(  # noqa: S310
			request.url,
			data=request.body,
			method=request.method,
			headers={"User-Agent": self.user_agent, **request.headers},
		)

		try:
			# The URL is built from a client's configured base URL, never from user input.
			response: http.client.HTTPResponse = urllib.request.urlopen(prepared, timeout=self.timeout)  # noqa: S310
		except urllib.error.HTTPError as error:
			return HttpResponse(error.code, error.reason, error.headers, self._decode(error.headers, error))
		except urllib.error.URLError as error:
			raise ClientException(f'Unable to reach "{request.url}": {error.reason}') from error

		return HttpResponse(response.status, response.reason, response.headers, self._decode(response.headers, response))

	@staticmethod
	def _decode(headers: Message, stream: IO[bytes]) -> IO[bytes]:
		"""Wrap a gzip encoded body so callers read it decompressed.

		urllib never negotiates an encoding of its own, so a body only arrives
		compressed when a caller asked for it.
		"""
		if headers.get("Content-Encoding", "").lower() != "gzip":
			return stream

		# GzipFile reads as a binary stream, which typeshed types as BufferedIOBase rather than IO.
		return cast("IO[bytes]", gzip.GzipFile(fileobj=stream))
