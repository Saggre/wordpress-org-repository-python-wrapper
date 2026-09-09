"""Minimal WebDAV filesystem over the WordPress.org SVN repositories."""

import urllib.parse
from collections.abc import Iterator
from email.utils import parsedate_to_datetime
from typing import IO
from xml.etree import ElementTree

from ..exceptions import ClientException
from ..transport import HttpClient, HttpRequest, HttpResponse
from .attributes import DirectoryAttributes, FileAttributes, StorageAttributes
from .exceptions import UnableToListContents, UnableToReadFile
from .listing import DirectoryListing

DAV_NAMESPACE = "DAV:"

# Commit logs are large XML documents that compress by more than an order of magnitude.
REQUEST_HEADERS = {"Accept-Encoding": "gzip"}

PROPFIND_BODY = (
	b'<?xml version="1.0" encoding="utf-8"?>'
	b'<d:propfind xmlns:d="DAV:"><d:prop>'
	b"<d:displayname/><d:getcontentlength/><d:getcontenttype/>"
	b"<d:getlastmodified/><d:resourcetype/>"
	b"</d:prop></d:propfind>"
)


def _tag(name: str) -> str:
	"""Return a DAV property name qualified with its namespace."""
	return f"{{{DAV_NAMESPACE}}}{name}"


class WebDavFilesystem:
	"""Reads files and lists directories over WebDAV.

	Three verbs are implemented: GET for file contents, PROPFIND for directory
	listings, and REPORT for the SVN log the repository exposes on top of DAV.
	"""

	def __init__(self, base_url: str, user_agent: str, timeout: float = 30.0, *, http_client: HttpClient | None = None) -> None:
		"""Build a filesystem rooted at the repository base URL.

		An injected http_client takes precedence over user_agent and timeout.
		"""
		self.base_url = base_url.rstrip("/")
		self._base_path = urllib.parse.unquote(urllib.parse.urlparse(self.base_url).path).strip("/")
		self._http_client = http_client or HttpClient(user_agent, timeout)

	def read(self, path: str) -> bytes:
		"""Return the content of a file."""
		with self.read_stream(path) as stream:
			return stream.read()

	def read_stream(self, path: str) -> IO[bytes]:
		"""Return the content of a file as a readable stream."""
		location = self._normalize_path(path)

		try:
			response = self._http_client.send(HttpRequest("GET", self._url(location), headers=dict(REQUEST_HEADERS)))
		except ClientException as error:
			raise UnableToReadFile.from_location(location, str(error)) from error

		if not response.ok:
			response.stream.close()

			raise UnableToReadFile.from_location(location, response.reason)

		return response.stream

	def list_contents(self, path: str, *, deep: bool = False) -> DirectoryListing:
		"""Return a lazy listing of a directory, including subdirectories when deep."""
		return DirectoryListing(self._iterate_contents(self._normalize_path(path), deep=deep))

	def report(self, path: str, body: str) -> HttpResponse:
		"""Send an SVN REPORT request to a repository path and return the response as is."""
		request = HttpRequest(
			"REPORT",
			self._url(self._normalize_path(path)),
			headers={**REQUEST_HEADERS, "Content-Type": "text/xml"},
			body=body.encode("utf-8"),
		)

		return self._http_client.send(request)

	def _iterate_contents(self, location: str, *, deep: bool) -> Iterator[StorageAttributes]:
		"""Yield the entries of a directory, descending into subdirectories when deep.

		The repository refuses a PROPFIND of infinite depth, so a deep listing is
		one shallow listing per directory, the way Flysystem's WebDAV adapter does it.
		"""
		try:
			response = self._propfind(location)
		except ClientException as error:
			raise UnableToListContents.at_location(location, str(error), deep=deep) from error

		if not response.ok:
			response.stream.close()

			raise UnableToListContents.at_location(location, response.reason, deep=deep)

		# The repository is a known endpoint, so the response is not treated as hostile XML.
		responses = ElementTree.fromstring(response.read()).findall(_tag("response"))  # noqa: S314

		# The first response describes the requested directory itself.
		for entry in responses[1:]:
			attributes = self._to_attributes(entry)

			yield attributes

			if deep and attributes.is_dir():
				yield from self._iterate_contents(attributes.path, deep=True)

	def _propfind(self, location: str) -> HttpResponse:
		request = HttpRequest(
			"PROPFIND",
			self._url(location, trailing_slash=True),
			headers={
				**REQUEST_HEADERS,
				"Content-Type": 'application/xml; charset="utf-8"',
				"Depth": "1",
			},
			body=PROPFIND_BODY,
		)

		return self._http_client.send(request)

	@staticmethod
	def _normalize_path(path: str) -> str:
		return path.strip("/")

	def _relative_path(self, path: str) -> str:
		"""Strip the path of the base URL from an href path, so entries can be passed back to read_stream."""
		if not self._base_path:
			return path

		if path == self._base_path:
			return ""

		return path.removeprefix(f"{self._base_path}/")

	def _url(self, location: str, *, trailing_slash: bool = False) -> str:
		url = f"{self.base_url}/{urllib.parse.quote(location)}"

		if trailing_slash and not url.endswith("/"):
			url = f"{url}/"

		return url

	def _to_attributes(self, response: ElementTree.Element) -> StorageAttributes:
		href = response.findtext(_tag("href"), default="")
		path = self._relative_path(urllib.parse.unquote(urllib.parse.urlparse(href).path).strip("/"))
		properties = self._properties(response)

		last_modified = self._to_timestamp(self._text(properties, "getlastmodified"))
		resource_type = properties.get("resourcetype")

		if resource_type is not None and resource_type.find(_tag("collection")) is not None:
			return DirectoryAttributes(path=path, last_modified=last_modified)

		file_size = self._text(properties, "getcontentlength")

		return FileAttributes(
			path=path,
			file_size=int(file_size) if file_size is not None else None,
			last_modified=last_modified,
			mime_type=self._text(properties, "getcontenttype"),
		)

	@staticmethod
	def _properties(response: ElementTree.Element) -> dict[str, ElementTree.Element]:
		"""Map local property names to their elements, ignoring failed propstat blocks."""
		properties: dict[str, ElementTree.Element] = {}

		for propstat in response.findall(_tag("propstat")):
			if " 200 " not in propstat.findtext(_tag("status"), default=""):
				continue

			prop = propstat.find(_tag("prop"))

			if prop is None:
				continue

			for element in prop:
				properties[element.tag.rpartition("}")[2]] = element

		return properties

	@staticmethod
	def _text(properties: dict[str, ElementTree.Element], name: str) -> str | None:
		element = properties.get(name)

		return element.text if element is not None else None

	@staticmethod
	def _to_timestamp(value: str | None) -> int | None:
		if value is None:
			return None

		return int(parsedate_to_datetime(value).timestamp())
