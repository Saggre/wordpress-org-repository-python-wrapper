# A WordPress.org Repository API wrapper for Python

Use cases: Plugin and theme directory data, update checks, analysis.

This library provides a simple way to access the WordPress.org [plugins](https://wordpress.org/plugins/)
and [themes](https://wordpress.org/themes/) repositories. It allows you to retrieve raw plugin and theme files and list
directories.

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

The listing is lazy, so the repository is contacted when you iterate it.

```python
directory = [entry.json_serialize() for entry in client.get_directory("/")]

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

#### List every tagged version of a plugin

```python
for tag in PluginClient(PluginClientConfig("akismet")).get_tags_directory():
	print(tag.path, tag.last_modified)
```

### Error handling

Every read error subclasses `FilesystemException`. Because directory listings are lazy,
`UnableToListContents` is raised when the listing is iterated, not when it is requested.

```python
from wordpress_org_repository import FilesystemException

try:
	content = client.get_file("does-not-exist.txt")
except FilesystemException as error:
	print(error)
```

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

The functional tests read live WordPress.org SVN endpoints and compare the responses against the
snapshots in `tests/functional/expected/`.

## Documentation

```bash
uv run pdoc wordpress_org_repository -o docs
```

## License

LGPL-3.0-only. See [LICENSE.md](./LICENSE.md).
