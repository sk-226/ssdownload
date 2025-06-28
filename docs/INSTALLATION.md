# Installation Guide

This guide covers all installation methods for the SuiteSparse Matrix Collection Downloader.

## Prerequisites

- **Python 3.12+** - Required for full compatibility
- **uv** (recommended) or **pip** for package management

## Development Installation (Current)

> **Note**: This package is currently in development and not yet published to PyPI.

### Option 1: Using uv (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd ssdownload

# 2. Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies and set up development environment
uv sync

# 4. Test the installation
uv run ssdl --help
```

### Option 2: Using pip

```bash
# 1. Clone the repository
git clone <repository-url>
cd ssdownload

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Test the installation
ssdl --help
```

## Future PyPI Installation

Once published to PyPI, installation will be simplified to:

```bash
# Standard installation
pip install ssdownload

# With development dependencies
pip install ssdownload[dev]
```

## Configuration

### Environment Variables

Set `SSDL_CACHE_DIR` to change the default cache directory:

```bash
export SSDL_CACHE_DIR=/path/to/cache
```

### Cache Directory

By default, matrices are downloaded to the current working directory. You can specify custom directories:

```bash
# CLI: specify output directory for single command
ssdl download ct20stif --output ./my_matrices

# Environment variable: applies to all commands
export SSDL_CACHE_DIR=./my_matrices
ssdl download ct20stif
```

## Verification

Test your installation with these commands:

```bash
# Check CLI is working
uv run ssdl --help  # or just `ssdl --help` with pip

# Test basic functionality
uv run ssdl groups  # List available matrix groups

# Test download (small file)
uv run ssdl info ct20stif  # Get matrix information
```

## Development Setup

If you plan to contribute to the project:

```bash
# Install with development dependencies
uv sync  # Installs all dev dependencies

# Install pre-commit hooks
uv run pre-commit install

# Run tests to verify setup
uv run pytest

# Check code quality tools
uv run ruff check src tests
uv run mypy src
```

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python --version  # Should be 3.12+

# If using pyenv
pyenv install 3.12
pyenv local 3.12
```

### uv Installation Issues

```bash
# Manual uv installation
pip install uv

# Alternative installation methods
# See: https://docs.astral.sh/uv/getting-started/installation/
```

### Permission Issues

```bash
# If you get permission errors
pip install --user -e .

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install -e .
```

### Network Issues

If you're behind a corporate firewall:

```bash
# Configure pip/uv to use your proxy
export HTTPS_PROXY=https://your-proxy:port
export HTTP_PROXY=http://your-proxy:port

# Or configure in pip.conf/uv.toml
```

## Advanced Configuration

### Custom Downloader Settings

```python
from ssdownload import SuiteSparseDownloader

# Custom configuration
downloader = SuiteSparseDownloader(
    cache_dir="./matrices",     # Custom cache directory
    workers=8,                  # Max concurrent downloads
    timeout=120.0,              # HTTP timeout in seconds
    verify_checksums=True       # Enable MD5 verification
)
```

### Integration with Jupyter

```bash
# Install Jupyter support
uv add jupyter ipykernel

# Use in notebooks
import asyncio
from ssdownload import SuiteSparseDownloader

downloader = SuiteSparseDownloader()
path = await downloader.download_by_name("ct20stif")
```

## Docker Installation

If you prefer containerized deployment:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync
CMD ["uv", "run", "ssdl", "--help"]
```

```bash
# Build and run
docker build -t ssdownload .
docker run -v $(pwd)/matrices:/app/matrices ssdownload uv run ssdl download ct20stif
```
