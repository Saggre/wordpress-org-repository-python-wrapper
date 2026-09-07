# A WordPress.org Repository API wrapper for Python

Use cases: Plugin and theme directory data, update checks, analysis.

[![codecov](https://img.shields.io/codecov/c/github/Saggre/wordpress-org-repository-python-wrapper)](https://codecov.io/gh/Saggre/wordpress-org-repository-python-wrapper)

This library provides a simple way to access the WordPress.org [plugins](https://wordpress.org/plugins/)
and [themes](https://wordpress.org/themes/) repositories. It allows you to retrieve raw plugin and theme files, list
directories, read commit logs, query the plugin directory and download releases.

It is a port of [wordpress-org-repository-php-wrapper](https://github.com/Saggre/wordpress-org-repository-php-wrapper)
and has no runtime dependencies.

## Installation

```bash
pip install wordpress-org-repository-python-wrapper
```

Or, with [uv](https://docs.astral.sh/uv/):

```bash
uv add wordpress-org-repository-python-wrapper
```

## Usage examples

### Configuring the client

#### Plugin client

```python
from wordpress_org_repository import PluginClient, PluginClientConfig

# Client for the latest version (trunk) of the WooCommerce plugin
config = PluginClientConfig("woocommerce", "trunk")
client = PluginClient(config)
```

#### Theme client

```python
from wordpress_org_repository import ThemeClient, ThemeClientConfig

# Client for version 1.2 of the Twenty Twenty-Five theme
config = ThemeClientConfig("twentytwentyfive", "1.2")
client = ThemeClient(config)
```

### Client methods

#### Get plugin or theme file contents

Contents are returned as bytes, so binary files such as screenshots work too.

```python
content = client.get_file("readme.txt").decode("utf-8")

"""
=== WooCommerce ===
Contributors: automattic, woocommerce
Tags: online store, ecommerce, shop, shopping cart, sell online
...
"""
```

#### Get plugin or theme file contents as a stream

The stream is a file-like object. Close it when you are done, or use it as a context manager.

```python
with client.get_file_stream("readme.txt") as file:
	content = file.read().decode("utf-8")

"""
=== WooCommerce ===
Contributors: automattic, woocommerce
Tags: online store, ecommerce, shop, shopping cart, sell online
...
"""
```

#### List plugin or theme directory contents

The listing is lazy, so the repository is contacted when you iterate it. Pass `deep=True` to list the
contents of subdirectories as well.

```python
directory = [entry.json_serialize() for entry in client.get_directory()]

"""
[
    ...
    {
        'type': 'file',
        'path': 'woocommerce/trunk/woocommerce.php',
        'file_size': 1851,
        'visibility': None,
        'last_modified': 1753778097,
        'mime_type': 'text/xml; charset="utf-8"',
        'extra_metadata': {},
    },
    ...
]
"""
```

#### List a plugin's tagged versions

```python
tags = PluginClient(PluginClientConfig("akismet")).get_tags_directory()

# ['1.5', '1.6', '1.7.2']
versions = [tag.path.rpartition("/")[2] for tag in tags]
```

#### Read the commit log

`get_log()` reads the history of the configured plugin or theme, `get_repository_log()` the history of every
plugin or theme at once. Both return the newest revision first, and both accept a revision range.

```python
for entry in client.get_log(limit=10):
	print(f"r{entry.revision} by {entry.author} at {entry.date:%c}: {entry.message}")

	for path in entry.paths:
		# Tags are copies, so a copied path resolves the release a version was cut from.
		print(f"  [{path.action.value}] {path.path} {path.copy_from_path}")
```

#### Export a tagged version

Writes the whole tree of the configured version to a local directory, which recovers releases that are no
longer served by the distribution host.

```python
files = client.export("/tmp/hello-dolly-1.7.2")
```

### Plugin API client

Reads plugin metadata from the WordPress.org plugin API.

```python
from wordpress_org_repository import PluginApiClient

client = PluginApiClient()
```

#### Enumerate plugins

Switch off the bulky prose and switch on the contributors to keep a page of results small.

```python
from wordpress_org_repository import PluginBrowse, PluginQuery

result = client.query_plugins(
	PluginQuery(
		browse=PluginBrowse.UPDATED,
		page=1,
		per_page=250,
		fields={
			"sections": False,
			"description": False,
			"screenshots": False,
			"icons": False,
			"contributors": True,
		},
	)
)

# 71793 plugins on 288 pages, newest last_updated first
print(f"{result.results} plugins on {result.pages} pages")

for plugin in result.plugins:
	print(plugin.slug, plugin.version, plugin.last_updated)
```

#### Read one plugin's record

```python
info = client.get_plugin_information("hello-dolly")

# {'1.5': 'https://downloads.wordpress.org/plugin/hello-dolly.1.5.zip', ...}
versions = info.versions
```

#### Check whether a plugin is closed

```python
status = client.get_plugin_status("hana-flv-player")

if status.closed:
	# security-issue as of 2021-06-21
	print(f"{status.reason} as of {status.closed_date:%Y-%m-%d}")
```

### Plugin download client

Downloads plugin releases from the WordPress.org distribution host. Only the current release is available without
a version, and withdrawn releases are no longer served even when they still exist in SVN.

```python
from wordpress_org_repository import PluginDownloadClient

client = PluginDownloadClient()

zip_file = client.get_zip("hello-dolly", "1.7.2")

with client.get_zip_stream("hello-dolly") as stream:
	...
```

### Error handling

File and directory reads raise `FilesystemException`. Because directory listings are lazy, `UnableToListContents`
is raised when the listing is iterated, not when it is requested. Everything else, including the commit log,
raises `ClientException`, whose `status` is the HTTP status of the failed response, or `None` when the host could
not be reached.

```python
from wordpress_org_repository import ClientException, FilesystemException

try:
	content = client.get_file("does-not-exist.txt")
except FilesystemException as error:
	print(error)

try:
	info = PluginApiClient().get_plugin_information("does-not-exist")
except ClientException as error:
	print(error.status, error)
```

## API reference

### `PluginClient` and `ThemeClient`

Every method reads the slug and version held by the client's config. `get_tags_directory()` is plugin only, since the
theme repository has no `tags` directory.

| Method                                                      | Returns            | Description                                                            |
|-------------------------------------------------------------|--------------------|------------------------------------------------------------------------|
| `get_file(path)`                                            | `bytes`            | Contents of a file.                                                    |
| `get_file_stream(path)`                                     | `IO[bytes]`        | Contents of a file as a stream.                                        |
| `get_directory(path="", *, deep=False)`                     | `DirectoryListing` | Directory contents, optionally including subdirectories.               |
| `get_tags_directory()`                                      | `DirectoryListing` | One entry per published version tag, with `last_modified` populated.   |
| `export(destination)`                                       | `int`              | Writes the tree to a local directory and returns the number of files.  |
| `get_log(limit=100, start_revision=None, end_revision=0)`   | `list[LogEntry]`   | Commit log of this plugin or theme, newest revision first.             |
| `get_repository_log(limit=100, start_revision=None, end_revision=0)` | `list[LogEntry]` | Commit log of every plugin or theme at once.                  |
| `get_filesystem()`                                          | `WebDavFilesystem` | The underlying filesystem, for anything the client does not do.        |

### `PluginApiClient`

| Method                                          | Returns             | Description                                              |
|-------------------------------------------------|---------------------|----------------------------------------------------------|
| `query_plugins(query)`                          | `PluginQueryResult` | One page of the plugin directory.                        |
| `get_plugin_information(slug, fields=None)`     | `PluginInfo`        | Full record of one plugin, including its versions map.   |
| `get_plugin_status(slug)`                       | `PluginStatus`      | Whether a plugin is closed, and why.                     |

### `PluginDownloadClient`

| Method                                | Returns     | Description                      |
|---------------------------------------|-------------|----------------------------------|
| `get_zip_url(slug, version=None)`     | `str`       | Download URL of a release.       |
| `get_zip(slug, version=None)`         | `bytes`     | Contents of the release archive. |
| `get_zip_stream(slug, version=None)`  | `IO[bytes]` | Release archive as a stream.     |

Every client accepts an `http_client` keyword argument, so a stub transport can stand in for the network in tests.

## Running tests

```bash
# Clone the repository
git clone git@github.com:Saggre/wordpress-org-repository-python-wrapper.git

# Go to the cloned repository
cd wordpress-org-repository-python-wrapper

# Install dependencies
uv sync

# Run the full suite
uv run pytest

# Run only the offline tests
uv run pytest -m "not network"
```

The functional tests read live WordPress.org endpoints and compare the responses against the snapshots in
`tests/functional/expected/`.

## Documentation

```bash
uv run pdoc wordpress_org_repository -o docs
```

## License

LGPL-3.0-only. See [LICENSE.md](./LICENSE.md).
