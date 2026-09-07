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
repositories for plugins and themes via WebDAV. It is a port of
`wordpress-org-repository-php-wrapper`.

**Transport layer:** `filesystem/webdav.py` holds `WebDavFilesystem`, a small stand-in for the PHP
version's SabreDAV client and League Flysystem filesystem. It speaks only the two verbs the library
needs: `GET` for file contents and `PROPFIND` with `Depth: 1` for a shallow directory listing, both
built on `urllib.request`. Listings are parsed with `xml.etree.ElementTree` into `FileAttributes`
and `DirectoryAttributes`, whose `json_serialize()` output matches Flysystem's key for key.

**Clients:** `BaseClient` reads through the filesystem. `PluginClient` and `ThemeClient` add nothing
beyond their config and, for plugins, `get_tags_directory()`.

**Config:** `PluginClientConfig` and `ThemeClientConfig` extend `BaseClientConfig`. They hold `slug`,
`version`, `base_url` and `user_agent`. Version `'trunk'` maps to the trunk path; any other value
maps to `tags/<version>` for plugins. Themes have no tags directory, so `ThemeClient` overrides
`_get_path`.

**Path construction:** `BaseClient._get_path()` uses `util.Path` to build the full SVN path:
`/<slug>/<version>/<file>` for trunk or `/<slug>/tags/<version>/<file>` for tagged plugin releases.

**Laziness:** `get_directory()` and `get_tags_directory()` return a `DirectoryListing` wrapping a
generator, so the request is only made once the listing is iterated. `UnableToListContents` is
therefore raised on iteration, not on the call, matching Flysystem.

**Tests:** `tests/unit/` covers pure logic; `tests/functional/` hits the live WordPress.org SVN
endpoints and is marked with the `network` marker. Functional tests compare against snapshots in
`tests/functional/expected/<slug>/<version>/`. Directory listings are stored as `index.json`; file
snapshots are stored byte for byte.

## Conventions

The quality pipeline is `ruff check`, `ruff format`, `mypy --strict`, then `pytest`, and CI runs all
four. Ruff runs with every rule enabled; each exception is listed in `pyproject.toml` with the reason
next to it. Indentation is tabs, matching the global `.editorconfig`, so the tab-indentation rules
are off and `ruff format` is configured with `indent-style = "tab"`.

`version.py` is the single source of the version. Hatchling reads `__version__` from it, so
`pyproject.toml` declares the version as dynamic rather than repeating it.

Snapshot files must keep LF endings. `.gitattributes` disables end-of-line conversion under `tests/functional/expected/`, and file
snapshots are compared as bytes rather than text so a CRLF checkout cannot corrupt them.

## Differences from the PHP original

- `get_file()` returns `bytes` rather than a string, so binary files work unchanged.
- `InvalidArgumentException` becomes `ValueError`.
- PHP's `empty()` treats the string `'0'` as empty, so a slug or version of `'0'` is rejected there
  and accepted here. The same applies to `Path`, which drops a `'0'` segment in PHP but keeps it
  here.
- The directory-listing snapshots use Flysystem's real `snake_case` keys. Two of the PHP snapshots
  still carry stale `camelCase` keys, which its tests do not catch because
  `assertEqualsCanonicalizing` sorts the keys away.
