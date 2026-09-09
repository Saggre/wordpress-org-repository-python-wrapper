# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-09-09

Mirrors `wordpress-org-repository-php-wrapper` 1.2.0.

### Added

- `BaseClient.get_changed_paths()`, which reads a revision range and can scope it to a subtree of the plugin or theme.
- `PluginClient.get_tag_revisions()`, which maps every published version to the revision that created its tag, ordered
  by revision rather than by version string.
- `PluginClient.diff_versions()`, which lists the files that changed between two published versions in a single request
  instead of downloading and comparing two complete trees.
- `TagNotFoundException`, raised when a version was published without ever being tagged.
- `text_mods` and `prop_mods` on `LogPath`, which separate content changes from property only ones.

### Changed

- Repository requests now negotiate gzip, which is worth more than an order of magnitude on commit logs.
- `util.log_report.create_request_body()` takes a path to scope the revisions to, and rejects a negative or inverted
  revision range before the request is sent. `get_log()` and `get_repository_log()` therefore raise `ValueError` on
  such a range instead of sending it.
- The protected `BaseClient._get_log_for_path()` takes the report target first and a path to scope the revisions last.

## [1.1.0] - 2026-09-07

Mirrors `wordpress-org-repository-php-wrapper` 1.1.0.

### Added

- `PluginApiClient` for the WordPress.org plugin API: `query_plugins()` enumerates the directory with browse modes,
  paging and response field toggles, `get_plugin_information()` reads a single plugin record including its versions
  map, and `get_plugin_status()` reports whether a plugin has been closed.
- `PluginDownloadClient` for downloading plugin releases from the distribution host, as bytes or as a stream.
- `BaseClient.get_log()` and `BaseClient.get_repository_log()`, which read commit logs over the SVN `REPORT` method.
- `BaseClient.export()`, which writes the tree of the configured version to a local directory.
- A `deep` argument on `BaseClient.get_directory()` for listing subdirectories.
- `ClientException`, raised by the new clients, carrying the HTTP status of the failed response, and raised without
  a status when a host cannot be reached.
- A shared `HttpClient` transport that every client accepts through `http_client=` for testing.

### Changed

- `BaseClientConfig` now only holds the base URL and the user agent. The slug and version moved to the new
  `RepositoryClientConfig`, which `PluginClientConfig` and `ThemeClientConfig` extend.
- The `path` argument of `BaseClient.get_directory()` defaults to the plugin or theme root.

## [1.0.0] - 2026-09-07

### Added

- Initial Python port of `wordpress-org-repository-php-wrapper` 1.0.0.

[Unreleased]: https://github.com/Saggre/wordpress-org-repository-python-wrapper/compare/1.2.0...HEAD
[1.2.0]: https://github.com/Saggre/wordpress-org-repository-python-wrapper/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/Saggre/wordpress-org-repository-python-wrapper/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/Saggre/wordpress-org-repository-python-wrapper/releases/tag/1.0.0
