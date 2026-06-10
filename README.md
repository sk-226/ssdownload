# SuiteSparse Matrix Collection Downloader

**Modern Python tool for downloading sparse matrices from the [SuiteSparse Matrix Collection](https://sparse.tamu.edu/)**

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

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv tool install ssdownload
uv tool update-shell   # First time only, if ssdl is not on PATH
# Open a new terminal so PATH changes apply
ssdl info ct20stif
```

See the [Installation Guide](docs/INSTALLATION.md) for details. To hack on the project, see the [Development Guide](docs/DEVELOPMENT.md).

### Basic Usage

```bash
# Get matrix information
ssdl info ct20stif

# Download a matrix (auto-detects group)
ssdl download ct20stif

# Download in Matrix Market format
ssdl download ct20stif --format mm

# Search matrices with filters
ssdl list --spd --size 1000:10000 --field real

# Search square unsymmetric matrices
ssdl list --square --structure unsymmetric

# Bulk download (real) SPD matrices in size range
ssdl bulk --spd --field real --size 100:1000 --max-files 5
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

# Find rectangular matrices
rectangular = await downloader.find_matrices(Filter(square=False))
```

</details>

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command-line options
- **[Python API](docs/API_REFERENCE.md)** - Full API documentation
- **[Examples](docs/EXAMPLES.md)** - Usage examples and tutorials
- **[Development](docs/DEVELOPMENT.md)** - Contributing and development setup
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions


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
