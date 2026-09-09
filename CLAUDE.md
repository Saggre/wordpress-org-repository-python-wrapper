# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test suite
uv run pytest tests/unit
uv run pytest tests/functional

# Skip the tests that hit the network
uv run pytest -m "not network"

# Run a single test file
uv run pytest tests/unit/util/test_path.py

# Lint, format and type check
uv run ruff check .
uv run ruff format .
uv run mypy

# Generate docs
uv run pdoc wordpress_org_repository -o docs
```

## Architecture

This is a general Python library with no runtime dependencies. It wraps the WordPress.org SVN
repositories for plugins and themes via WebDAV, the plugin API, and the plugin distribution host. It
is a port of `wordpress-org-repository-php-wrapper` and tracks its releases.

**Transport layer:** `transport.py` holds `HttpClient`, a thin `urllib` wrapper whose `send()` returns
every response as an `HttpResponse`, error statuses included, because the WordPress.org APIs put
meaningful bodies on them. A transport failure, such as a DNS or connection error, raises
`ClientException` with no `status`. Every client accepts an `http_client` keyword argument, which is
the seam the unit tests use to inject `tests/unit/stub.py`. A gzip encoded body is decompressed
transparently; only the repository requests ask for one, since commit logs compress by more than an
order of magnitude.

**Repository filesystem:** `filesystem/webdav.py` holds `WebDavFilesystem`, a small stand-in for the
PHP version's SabreDAV client and League Flysystem filesystem, built on `HttpClient`. It speaks
`GET` for file contents, `PROPFIND` with `Depth: 1` for directory listings, and `REPORT` for the SVN
log. A deep listing is one shallow listing per subdirectory, the way Flysystem does it, because the
repository refuses `Depth: infinity`. Listings are parsed with `xml.etree.ElementTree` into
`FileAttributes` and `DirectoryAttributes`, whose `json_serialize()` output matches Flysystem's key
for key.

**Repository clients:** `BaseClient` reads files and directories through the filesystem, exports a
version to a local directory, and reads commit logs through `util/log_report.py`, which builds the
`REPORT` body and parses the response into `LogEntry` and `LogPath`. `get_changed_paths()` scopes a
revision range to a subtree; the server only answers a `REPORT` at the repository root or a plugin
root, so the narrower scope goes into the request body rather than the target. `PluginClient` adds
`get_tags_directory()`, `get_tag_revisions()`, which reads the whole tag history in one request and
keys it by version in revision order, and `diff_versions()`, which reads the range between two tags
and reduces it to one entry per file with `_normalize_paths()`. `ThemeClient` adds nothing beyond its
config.

**API clients:** `plugin_api_client.py` reads plugin metadata from `api.wordpress.org` into the
`model/` value objects (`PluginInfo`, `PluginQueryResult`, `PluginStatus`). Query parameters are
nested under `request[...]` the way PHP's `http_build_query` does it. A closed plugin comes back as
a 404 whose body is the answer, so `get_plugin_status()` reads it while `get_plugin_information()`
raises. `plugin_download_client.py` downloads release archives from `downloads.wordpress.org`.
Both raise `ClientException`, whose `status` is the HTTP status of the failed response.

**Config:** `BaseClientConfig` holds `base_url` and `user_agent`. `RepositoryClientConfig` adds
`slug` and `version` and is what `PluginClientConfig` and `ThemeClientConfig` extend. Version
`'trunk'` maps to the trunk path; any other value maps to `tags/<version>` for plugins. Themes have
no tags directory, so `ThemeClient` overrides `_get_path`. `PluginApiClientConfig` and
`PluginDownloadClientConfig` extend `BaseClientConfig` directly.

**Dates:** `util/date.py` parses every date shape WordPress.org uses. Values without a zone are read
as UTC, never as host time, so results do not depend on the environment.

**Path construction:** `BaseClient._get_path()` uses `util.Path` to build the full SVN path:
`/<slug>/<version>/<file>` for trunk or `/<slug>/tags/<version>/<file>` for tagged plugin releases.

**Laziness:** `get_directory()` and `get_tags_directory()` return a `DirectoryListing` wrapping a
generator, so the request is only made once the listing is iterated. `UnableToListContents` is
therefore raised on iteration, not on the call, matching Flysystem.

**Tests:** `tests/unit/` covers pure logic and the clients against a stubbed transport, with API
payloads under `tests/unit/fixtures/`. `tests/functional/` hits the live WordPress.org endpoints and
is marked with the `network` marker. Functional repository tests compare against snapshots in
`tests/functional/expected/<slug>/<version>/`. Directory listings are stored as `index.json`; file
snapshots are stored byte for byte.

## Conventions

The quality pipeline is `ruff check`, `ruff format`, `mypy --strict`, then `pytest`, and CI runs all
four. Ruff runs with every rule enabled; each exception is listed in `pyproject.toml` with the reason
next to it. Indentation is tabs, matching the global `.editorconfig`, so the tab-indentation rules
are off and `ruff format` is configured with `indent-style = "tab"`.

`version.py` is the single source of the version. Hatchling reads `__version__` from it, so
`pyproject.toml` declares the version as dynamic rather than repeating it.

Snapshot files must keep LF endings. `.gitattributes` disables end-of-line conversion under
`tests/functional/expected/`, and file snapshots are compared as bytes rather than text so a CRLF
checkout cannot corrupt them.

Exception messages are copied from the PHP original word for word, so a port of a PHP test can
assert on them unchanged.

## Differences from the PHP original

- `get_file()` returns `bytes` rather than a string, so binary files work unchanged.
- `InvalidArgumentException` becomes `ValueError`.
- PHP's `empty()` treats the string `'0'` as empty, so a slug or version of `'0'` is rejected there
  and accepted here.
- `ClientException` exposes the HTTP status as `status`, where PHP uses the exception code.
- `get_tag_revisions()` returns a `dict` and `diff_versions()` a `dict[str, LogPath]`, both relying on
  insertion order the way the PHP arrays do.
- `Contributor.from_dict()` reads a bare profile URL string, which the plugins/info/1.0 endpoint
  returns, as the profile. PHP casts it to an array and drops it.
- The directory-listing snapshots use Flysystem's real `snake_case` keys. Two of the PHP snapshots
  still carry stale `camelCase` keys, which its tests do not catch because
  `assertEqualsCanonicalizing` sorts the keys away.
