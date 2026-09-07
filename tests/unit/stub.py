"""A transport that records requests and replays canned responses."""

import io
from email.message import Message
from http import HTTPStatus

from wordpress_org_repository import HttpClient, HttpRequest, HttpResponse


class HttpClientStub(HttpClient):
	"""Stands in for the network in unit tests."""

	def __init__(self, *responses: HttpResponse) -> None:
		"""Queue the responses to replay, in order."""
		super().__init__("TestUserAgent/1.0")
		self.responses = list(responses)
		self.requests: list[HttpRequest] = []

	@classmethod
	def respond_with(cls, status: int, body: str | bytes) -> "HttpClientStub":
		"""Build a stub replaying a single response."""
		encoded = body.encode("utf-8") if isinstance(body, str) else body

		return cls(HttpResponse(status, HTTPStatus(status).phrase, Message(), io.BytesIO(encoded)))

	def send(self, request: HttpRequest) -> HttpResponse:
		"""Record the request and return the next queued response."""
		self.requests.append(request)

		return self.responses.pop(0)

	@property
	def last_url(self) -> str:
		"""The URL of the request sent last."""
		return self.requests[-1].url
