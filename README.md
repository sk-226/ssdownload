# SuiteSparse Matrix Collection Downloader

A modern Python command-line tool and library for downloading sparse matrices from the [SuiteSparse Matrix Collection](https://sparse.tamu.edu/).

## Features

- **Matrix Discovery**: Search matrices by metadata filters (size, nnz, SPD flag, field type, etc.)
- **Multiple Formats**: Download MAT-files, Matrix Market, or Rutherford-Boeing formats
- **Concurrent Downloads**: Configurable number of parallel download workers (up to 8)
- **Resume Support**: HTTP range requests with temporary `.part` files for interrupted downloads
- **Checksum Verification**: MD5 validation for downloaded files ensuring data integrity
- **Smart Caching**: Skip downloads if identical files already exist with valid checksums
- **Rich CLI**: Progress bars and colored output using Rich library
- **Robust Error Handling**: Comprehensive exception handling with custom error types
- **Type Safety**: Full type hints for better IDE support and code reliability

## Installation

> **Note**: This package is currently in development and not yet published to PyPI.

### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd ssdownload

# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and set up development environment
uv sync

# Run the CLI tool
uv run ssdl --help
```

### Future PyPI Installation (not yet available)

```bash
# This will be available once published to PyPI
pip install ssdownload
```

## Quick Start

### Command Line Interface

```bash
# Download a specific matrix (MAT-file format) - auto-detects group
ssdl download ct20stif

# Download Matrix Market format
ssdl download ct20stif --format mm

# Or specify group explicitly
ssdl download Boeing/ct20stif --format mm
ssdl download ct20stif --group Boeing --format mm

# List available matrices with filters
ssdl list --spd --size 1000:10000 --field real

# Bulk download with filters
ssdl bulk --spd --size 1e4:1e5 --nnz :5e6 --format mm --max-files 10

# Get detailed information about a matrix (auto-detects group)
ssdl info ct20stif

# Or specify group explicitly
ssdl info Boeing/ct20stif
ssdl info ct20stif --group Boeing

# Download by name only (searches all groups automatically)  
ssdl get ct20stif
```

### Python API

```python
from ssdownload import SuiteSparseDownloader, Filter
from pathlib import Path

# Initialize downloader with custom settings
downloader = SuiteSparseDownloader(
    cache_dir=Path("./matrices"),
    workers=4,
    timeout=60.0,
    verify_checksums=True
)

# Download a specific matrix
path = await downloader.download("Boeing", "ct20stif")
print(f"Downloaded to: {path}")

# Download by name only (auto-detect group)
path = await downloader.download_by_name("ct20stif")
print(f"Downloaded to: {path}")

# Search and bulk download with filters
filter_obj = Filter(
    spd=True,
    n_rows=(10_000, 100_000),
    nnz=(None, 5_000_000),
    field="real"
)
paths = await downloader.bulk_download(
    filter_obj, 
    format_type="mm", 
    max_files=50
)
print(f"Downloaded {len(paths)} matrices")

# List matrices (synchronous)
matrices = downloader.list_matrices(filter_obj, limit=10)
for matrix in matrices:
    print(f"{matrix['group']}/{matrix['name']}: {matrix['num_rows']}×{matrix['num_cols']}")

# Get all available groups
groups = await downloader._get_available_groups()
print(f"Available groups: {sorted(groups)}")
```

## Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| `mat` | `.mat` | MATLAB/Octave MAT-file (default) |
| `mm` | `.tar.gz` | Matrix Market format |
| `rb` | `.tar.gz` | Rutherford-Boeing format |

## Filter Options

### CLI Filters

- `--spd`: Symmetric positive definite matrices only
- `--posdef`: Positive definite matrices only
- `--size MIN:MAX`: Matrix size range (applies to both rows and columns)
- `--rows MIN:MAX`: Number of rows range
- `--cols MIN:MAX`: Number of columns range
- `--nnz MIN:MAX`: Number of nonzeros range
- `--field TYPE`: Field type (`real`, `complex`, `integer`, `binary`)
- `--group NAME`: Matrix group/collection name (partial match)
- `--name PATTERN`: Matrix name pattern (partial match)
- `--structure TYPE`: Matrix structure (`symmetric`, `unsymmetric`, etc.)

### Range Syntax

- `1000:5000` - Between 1000 and 5000 (inclusive)
- `:5000` - Up to 5000
- `1000:` - 1000 and above
- `1e4:1e6` - Scientific notation supported

## Configuration

### Cache Directory

By default, matrices are downloaded to the current working directory. You can specify custom directories:

```bash
# CLI: specify output directory
ssdl download Boeing ct20stif --output ./my_matrices

# Python: set cache directory
downloader = SuiteSparseDownloader(cache_dir="./my_matrices")
```

### Environment Variables

Set `SSDL_CACHE_DIR` to change the default cache directory:

```bash
export SSDL_CACHE_DIR=/path/to/cache
ssdl download Boeing ct20stif
```

### Advanced Configuration

The library supports various configuration options:

```python
downloader = SuiteSparseDownloader(
    cache_dir="./matrices",     # Custom cache directory
    workers=8,                  # Max concurrent downloads
    timeout=120.0,              # HTTP timeout in seconds  
    verify_checksums=True       # Enable MD5 verification
)
```

## Development

### Setup Development Environment

```bash
git clone <repository-url>
cd ssdownload

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ssdownload --cov-report=html

# Run specific test file
uv run pytest tests/test_client.py -v

# Run tests for specific module
uv run pytest tests/test_index_manager.py tests/test_downloader.py
```

### Code Quality

```bash
# Format code
uv run ruff format src tests

# Lint code
uv run ruff check src tests

# Fix linting issues automatically
uv run ruff check --fix src tests

# Type checking
uv run mypy src
```

### Architecture

The codebase follows a modular architecture:

- **`client.py`**: Main SuiteSparseDownloader class
- **`index_manager.py`**: CSV index fetching and caching
- **`downloader.py`**: File downloading with resume support
- **`filters.py`**: Matrix filtering and search functionality
- **`config.py`**: Centralized configuration management
- **`cli.py`**: Command-line interface
- **`cli_utils.py`**: CLI utility functions
- **`exceptions.py`**: Custom exception classes

## Examples

### Download Specific Matrices

```bash
# Boeing structural matrices (auto-detect group)
ssdl download ct20stif
ssdl download bcsstk14

# Or specify group explicitly
ssdl download Boeing/ct20stif
ssdl download Boeing/bcsstk14

# Network matrices
ssdl download email-Eu-core
ssdl download SNAP/email-Eu-core
```

### Bulk Downloads

```bash
# Small to medium SPD matrices in Matrix Market format
ssdl bulk --spd --size 1000:50000 --format mm --output ./spd_matrices

# Real-valued matrices from specific groups
ssdl bulk --field real --group "Boeing" --group "HB" --max-files 20

# Large sparse matrices with few nonzeros
ssdl bulk --size 100000: --nnz :1000000 --max-files 5
```

### Search and Explore

```bash
# List all Boeing matrices
ssdl list --group Boeing --verbose

# Find small test matrices
ssdl list --size :1000 --limit 10

# Search by name pattern
ssdl list --name "stif" --verbose
```

## API Reference

### SuiteSparseDownloader

The main class for downloading matrices with robust error handling and progress tracking.

```python
SuiteSparseDownloader(
    cache_dir: Optional[Union[str, Path]] = None,
    workers: int = 4,
    timeout: float = 30.0,
    verify_checksums: bool = True
)
```

#### Methods

- `download(group, name, format_type="mat", output_dir=None)` - Download single matrix by group and name
- `download_by_name(name, format_type="mat", output_dir=None)` - Download by name with automatic group detection
- `bulk_download(filter_obj, format_type="mat", output_dir=None, max_files=None)` - Download multiple matrices
- `find_matrices(filter_obj=None)` - Search matrices (async)
- `list_matrices(filter_obj=None, limit=None)` - Search matrices (sync)

#### CLI Commands

- `ssdl download <identifier>` - Download matrix by name (auto-detects group) or group/name format
- `ssdl get <name>` - Alternative command for downloading by name only
- `ssdl download <identifier> --group <group>` - Download with explicit group specification
- `ssdl list [filters...]` - List matrices matching criteria
- `ssdl bulk [filters...]` - Bulk download matrices
- `ssdl info <identifier>` - Show detailed matrix information (auto-detects group or use group/name format)
- `ssdl groups` - List all available groups

#### Exception Handling

The library provides specific exception types for better error handling:

```python
from ssdownload.exceptions import (
    SSDownloadError,        # Base exception
    MatrixNotFoundError,    # Matrix not found in collection
    ChecksumError,          # File integrity check failed
    DownloadError,          # Download operation failed
    NetworkError,           # Network-related errors
    IndexError              # Index fetching/parsing errors
)

try:
    path = await downloader.download_by_name("nonexistent_matrix")
except MatrixNotFoundError as e:
    print(f"Matrix not found: {e}")
except ChecksumError as e:
    print(f"File integrity check failed: {e}")
except SSDownloadError as e:
    print(f"Download error: {e}")
```

### Filter

Advanced filter class for matrix search with type safety.

```python
Filter(
    spd: Optional[bool] = None,                                    # Symmetric positive definite
    posdef: Optional[bool] = None,                                 # Positive definite
    n_rows: Optional[Tuple[Optional[int], Optional[int]]] = None,  # Row count range
    n_cols: Optional[Tuple[Optional[int], Optional[int]]] = None,  # Column count range
    nnz: Optional[Tuple[Optional[int], Optional[int]]] = None,     # Non-zero count range
    field: Optional[str] = None,                                   # Field type
    group: Optional[str] = None,                                   # Matrix group
    name: Optional[str] = None,                                    # Matrix name pattern
    kind: Optional[str] = None,                                    # Matrix kind
    structure: Optional[str] = None                                # Matrix structure
)
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Performance and Reliability

### Caching Strategy

The library implements a three-tier caching system:
1. **Memory cache** - Fastest access for recently used data
2. **Disk cache** - Persistent storage for matrix index (1-hour TTL)
3. **Remote fetch** - Direct download from SuiteSparse servers

### Resume Support

Interrupted downloads are automatically resumed using HTTP Range requests:
- Temporary `.part` files track download progress
- Robust checksum verification ensures data integrity
- Smart file existence checks prevent unnecessary re-downloads

### Concurrent Downloads

- Configurable worker pools (default: 4, max: 8)
- Semaphore-based concurrency control
- Per-file progress tracking with Rich progress bars
- Graceful handling of failed downloads in bulk operations

## Troubleshooting

### Common Issues

**Matrix not found:**
```python
# Use exact names from the collection
matrices = downloader.list_matrices(Filter(name="ct20"), limit=5)
for m in matrices:
    print(f"{m['group']}/{m['name']}")
```

**Network timeouts:**
```python
# Increase timeout for large files
downloader = SuiteSparseDownloader(timeout=300.0)  # 5 minutes
```

**Checksum failures:**
```python
# Disable checksums if server doesn't provide them
downloader = SuiteSparseDownloader(verify_checksums=False)
```

## Acknowledgments

- [SuiteSparse Matrix Collection](https://sparse.tamu.edu/) - The source of all matrix data
- [Tim Davis](https://people.engr.tamu.edu/davis/) - Creator and maintainer of the collection
- [httpx](https://www.python-httpx.org/) - Modern async HTTP client
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal formatting
- [Typer](https://typer.tiangolo.com/) - Modern CLI framework