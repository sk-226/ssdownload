# Installation Guide

How to install the SuiteSparse Matrix Collection Downloader CLI.

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — install and update uv using the official documentation

## Install the CLI

```bash
uv tool install ssdownload
uv tool update-shell   # First time only, if ssdl is not on PATH
ssdl --help
```

The CLI is installed in an isolated tool environment (similar to pipx), not into your system Python site-packages.

Upgrade after a new release:

```bash
uv tool upgrade ssdownload
```

## Verify

```bash
ssdl --help
ssdl groups
ssdl info ct20stif
```

## Development

To work from a git clone, see the [Development Guide](DEVELOPMENT.md).

## Configuration

### Environment variables

Set `SSDOWNLOAD_CACHE_DIR` to override the default cache location:

```bash
export SSDOWNLOAD_CACHE_DIR=/path/to/cache
```

On Windows (PowerShell):

```powershell
$env:SSDOWNLOAD_CACHE_DIR = "C:\path\to\cache"
```

### Download directory

By default, matrix files are written under the current working directory unless you pass `--output`:

```bash
ssdl download ct20stif --output ./my_matrices
```

## Troubleshooting

See [Troubleshooting Guide](TROUBLESHOOTING.md). For `ssdl: command not found`, run `uv tool update-shell` and open a new terminal.
