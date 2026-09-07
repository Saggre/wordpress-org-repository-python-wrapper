"""Minimal WebDAV filesystem over the WordPress.org SVN repositories."""

import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from email.utils import parsedate_to_datetime
from typing import IO
from xml.etree import ElementTree

from .attributes import DirectoryAttributes, FileAttributes, StorageAttributes
from .exceptions import UnableToListContents, UnableToReadFile
from .listing import DirectoryListing

DAV_NAMESPACE = "DAV:"

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

	Only the two verbs the repository needs are implemented: GET for file
	contents and PROPFIND with Depth 1 for a shallow directory listing.
	"""

	def __init__(self, base_url: str, user_agent: str, timeout: float = 30.0) -> None:
		"""Build a filesystem rooted at the repository base URL."""
		self.base_url = base_url.rstrip("/")
		self.user_agent = user_agent
		self.timeout = timeout

	def read(self, path: str) -> bytes:
		"""Return the content of a file."""
		with self.read_stream(path) as stream:
			return stream.read()

	def read_stream(self, path: str) -> IO[bytes]:
		"""Return the content of a file as a readable stream."""
		location = self._normalize_path(path)
		request = urllib.request.Request(self._url(location), headers={"User-Agent": self.user_agent})  # noqa: S310

		try:
			# The URL is built from the base URL the client was configured with, never from user input.
			response: IO[bytes] = urllib.request.urlopen(request, timeout=self.timeout)  # noqa: S310
		except urllib.error.URLError as error:
			raise UnableToReadFile.from_location(location, str(error.reason)) from error

		return response

	def list_contents(self, path: str, *, deep: bool = False) -> DirectoryListing:
		"""Return a lazy listing of a directory."""
		return DirectoryListing(self._iterate_contents(self._normalize_path(path), deep=deep))

	def _iterate_contents(self, location: str, *, deep: bool) -> Iterator[StorageAttributes]:
		try:
			body = self._propfind(location, deep=deep)
		except urllib.error.URLError as error:
			raise UnableToListContents.at_location(location, str(error.reason), deep=deep) from error

		# The repository is a known endpoint, so the response is not treated as hostile XML.
		responses = ElementTree.fromstring(body).findall(_tag("response"))  # noqa: S314

		# The first response describes the requested directory itself.
		for response in responses[1:]:
			yield self._to_attributes(response)

	def _propfind(self, location: str, *, deep: bool) -> bytes:
		request = urllib.request.Request(  # noqa: S310
			self._url(location, trailing_slash=True),
			data=PROPFIND_BODY,
			method="PROPFIND",
			headers={
				"User-Agent": self.user_agent,
				"Content-Type": 'application/xml; charset="utf-8"',
				"Depth": "infinity" if deep else "1",
			},
		)

		# The URL is built from the base URL the client was configured with, never from user input.
		with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310
			body: bytes = response.read()

		return body

	@staticmethod
	def _normalize_path(path: str) -> str:
		return path.strip("/")

	def _url(self, location: str, *, trailing_slash: bool = False) -> str:
		url = f"{self.base_url}/{urllib.parse.quote(location)}"

		if trailing_slash and not url.endswith("/"):
			url = f"{url}/"

		return url

	def _to_attributes(self, response: ElementTree.Element) -> StorageAttributes:
		href = response.findtext(_tag("href"), default="")
		path = urllib.parse.unquote(urllib.parse.urlparse(href).path).strip("/")
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
