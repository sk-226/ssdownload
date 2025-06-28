# SuiteSparse Matrix Collection Downloader

**Modern Python tool for downloading sparse matrices from the [SuiteSparse Matrix Collection](https://sparse.tamu.edu/)**

> ⚠️ **This project is under active development.** APIs and features may change without notice.

A command-line tool and Python library that makes it easy to discover, download, and work with sparse matrices from the world's largest collection of sparse matrix data.

## ✨ Features

- 🔍 **Smart Matrix Discovery** - Search by size, sparsity, mathematical properties, and more
- 📦 **Multiple Formats** - Download MAT-files, Matrix Market, or Rutherford-Boeing formats
- ⚡ **Concurrent Downloads** - Up to 8 parallel downloads with progress tracking
- 🔄 **Resume Support** - Interrupted downloads continue automatically
- ✅ **Integrity Verification** - MD5 checksum validation ensures data accuracy
- 🧠 **Smart Caching** - Skip re-downloads of existing files
- 🎨 **Rich CLI** - Beautiful progress bars and colored output
- 🔧 **Type Safety** - Full type hints for better IDE support

## 🚀 Quick Start

### Installation

```bash
# Clone and install (not yet on PyPI)
git clone <repository-url>
cd ssdownload
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
uv sync                                           # Install dependencies
```

### Basic Usage

```bash
# Download a matrix (auto-detects group)
uv run ssdl download ct20stif

# Download in Matrix Market format
uv run ssdl download ct20stif --format mm

# Search matrices with filters
uv run ssdl list --spd --size 1000:10000 --field real

# Bulk download SPD matrices
uv run ssdl bulk --spd --max-files 10

# Bulk download real SPD matrices in size range
uv run ssdl bulk --spd --field real --size 100:1000 --max-files 5
```

<details>
<summary>Python API Example</summary>

```python
from ssdownload import SuiteSparseDownloader, Filter

# Simple download
downloader = SuiteSparseDownloader()
path = await downloader.download_by_name("ct20stif")

# Filtered bulk download
filter_obj = Filter(spd=True, n_rows=(1000, 10000))
paths = await downloader.bulk_download(filter_obj, max_files=5)
```

</details>

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command-line options
- **[Python API](docs/API_REFERENCE.md)** - Full API documentation
- **[Examples](docs/EXAMPLES.md)** - Usage examples and tutorials
- **[Development](docs/DEVELOPMENT.md)** - Contributing and development setup
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## 🎯 Common Commands

```bash
# Get matrix information
uv run ssdl info ct20stif

# List matrices by group
uv run ssdl list --group Boeing

# Download with custom output directory
uv run ssdl download ct20stif --output ./matrices

# Search by name pattern
uv run ssdl list --name "stif" --limit 5
```

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](docs/DEVELOPMENT.md) for setup instructions and coding standards.

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [SuiteSparse Matrix Collection](https://sparse.tamu.edu/) by [Tim Davis](https://people.engr.tamu.edu/davis/)
- Built with [httpx](https://www.python-httpx.org/), [Rich](https://rich.readthedocs.io/), and [Typer](https://typer.tiangolo.com/)
