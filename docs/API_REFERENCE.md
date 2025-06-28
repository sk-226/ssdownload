# Python API Reference

Complete Python API documentation for the SuiteSparse Matrix Collection Downloader.

## Quick Start

```python
from ssdownload import SuiteSparseDownloader, Filter
from pathlib import Path

# Initialize downloader
downloader = SuiteSparseDownloader()

# Download a matrix
path = await downloader.download_by_name("ct20stif")
print(f"Downloaded to: {path}")
```

## Core Classes

### SuiteSparseDownloader

The main class for downloading matrices with robust error handling and progress tracking.

#### Constructor

```python
SuiteSparseDownloader(
    cache_dir: Optional[Union[str, Path]] = None,
    workers: int = 4,
    timeout: float = 30.0,
    verify_checksums: bool = False
)
```

**Parameters:**
- `cache_dir` - Directory to store downloaded files (default: current directory)
- `workers` - Number of concurrent download workers (max: 8)
- `timeout` - HTTP request timeout in seconds
- `verify_checksums` - Whether to verify file checksums after download

**Example:**
```python
downloader = SuiteSparseDownloader(
    cache_dir="./matrices",
    workers=8,
    timeout=120.0,
    verify_checksums=True
)
```

#### Methods

##### `download()` - Download Single Matrix

```python
async def download(
    self,
    group: str,
    name: str,
    format_type: str = "mat",
    output_dir: Optional[Union[str, Path]] = None
) -> Path
```

Download a single matrix by group and name.

**Parameters:**
- `group` - Matrix group name (e.g., "Boeing")
- `name` - Matrix name (e.g., "ct20stif")
- `format_type` - File format: "mat", "mm", "rb" (default: "mat")
- `output_dir` - Output directory (default: cache_dir)

**Returns:** Path to downloaded file

**Example:**
```python
path = await downloader.download("Boeing", "ct20stif", format_type="mm")
```

##### `download_by_name()` - Download with Auto Group Detection

```python
async def download_by_name(
    self,
    name: str,
    format_type: str = "mat",
    output_dir: Optional[Union[str, Path]] = None
) -> Path
```

Download a matrix by name with automatic group detection.

**Parameters:**
- `name` - Matrix name (searches all groups)
- `format_type` - File format: "mat", "mm", "rb"
- `output_dir` - Output directory (default: cache_dir)

**Returns:** Path to downloaded file

**Example:**
```python
path = await downloader.download_by_name("ct20stif")
```

##### `bulk_download()` - Download Multiple Matrices

```python
async def bulk_download(
    self,
    filter_obj: Optional[Filter] = None,
    format_type: str = "mat",
    output_dir: Optional[Union[str, Path]] = None,
    max_files: Optional[int] = None
) -> List[Path]
```

Download multiple matrices matching filter criteria.

**Parameters:**
- `filter_obj` - Filter object for matrix selection
- `format_type` - File format: "mat", "mm", "rb"
- `output_dir` - Output directory (default: cache_dir)
- `max_files` - Maximum number of files to download

**Returns:** List of paths to downloaded files

**Example:**
```python
filter_obj = Filter(spd=True, n_rows=(1000, 10000))
paths = await downloader.bulk_download(filter_obj, max_files=5)
```

##### `find_matrices()` - Search Matrices (Async)

```python
async def find_matrices(
    self,
    filter_obj: Optional[Filter] = None
) -> List[Dict[str, Any]]
```

Search matrices asynchronously.

**Parameters:**
- `filter_obj` - Filter object for matrix selection

**Returns:** List of matrix metadata dictionaries

**Example:**
```python
filter_obj = Filter(group="Boeing", n_rows=(1000, None))
matrices = await downloader.find_matrices(filter_obj)
for matrix in matrices:
    print(f"{matrix['group']}/{matrix['name']}: {matrix['num_rows']}×{matrix['num_cols']}")
```

##### `list_matrices()` - Search Matrices (Sync)

```python
def list_matrices(
    self,
    filter_obj: Optional[Filter] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]
```

Search matrices synchronously.

**Parameters:**
- `filter_obj` - Filter object for matrix selection
- `limit` - Maximum number of results

**Returns:** List of matrix metadata dictionaries

**Example:**
```python
matrices = downloader.list_matrices(Filter(spd=True), limit=10)
```

### Filter

Advanced filter class for matrix search with type safety.

#### Constructor

```python
Filter(
    spd: Optional[bool] = None,
    n_rows: Optional[Tuple[Optional[int], Optional[int]]] = None,
    n_cols: Optional[Tuple[Optional[int], Optional[int]]] = None,
    nnz: Optional[Tuple[Optional[int], Optional[int]]] = None,
    field: Optional[str] = None,
    group: Optional[str] = None,
    name: Optional[str] = None,
    kind: Optional[str] = None,
    structure: Optional[str] = None
)
```

**Parameters:**
- `spd` - Symmetric positive definite flag
- `n_rows` - Row count range (min, max)
- `n_cols` - Column count range (min, max)
- `nnz` - Non-zero count range (min, max)
- `field` - Field type: "real", "complex", "integer", "binary"
- `group` - Matrix group name (partial match)
- `name` - Matrix name pattern (partial match)
- `kind` - Matrix kind
- `structure` - Matrix structure type

**Examples:**
```python
# SPD matrices with 1000-10000 rows
filter1 = Filter(spd=True, n_rows=(1000, 10000))

# Real-valued matrices from Boeing group
filter2 = Filter(field="real", group="Boeing")

# Large sparse matrices
filter3 = Filter(n_rows=(100000, None), nnz=(None, 1000000))

# Search by name pattern
filter4 = Filter(name="stif")
```

## Exception Handling

The library provides specific exception types for better error handling.

### Exception Hierarchy

```python
from ssdownload.exceptions import (
    SSDownloadError,        # Base exception
    MatrixNotFoundError,    # Matrix not found in collection
    ChecksumError,          # File integrity check failed
    DownloadError,          # Download operation failed
    NetworkError,           # Network-related errors
    IndexError              # Index fetching/parsing errors
)
```

### Usage Examples

```python
try:
    path = await downloader.download_by_name("nonexistent_matrix")
except MatrixNotFoundError as e:
    print(f"Matrix not found: {e}")
except ChecksumError as e:
    print(f"File integrity check failed: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except SSDownloadError as e:
    print(f"General download error: {e}")
```

## Configuration Classes

### Config

Centralized configuration management.

```python
from ssdownload.config import Config

# Access configuration constants
print(Config.DEFAULT_WORKERS)    # 4
print(Config.MAX_WORKERS)        # 8
print(Config.DEFAULT_TIMEOUT)    # 30.0

# Get file extension for format
ext = Config.get_file_extension("mm")  # ".tar.gz"
```

## Advanced Usage

### Custom Progress Tracking

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize downloader without internal progress display
downloader = SuiteSparseDownloader()

# Custom progress tracking for bulk downloads
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    transient=True,
) as progress:
    task = progress.add_task("Downloading matrices...", total=None)

    filter_obj = Filter(spd=True, n_rows=(1000, 5000))
    paths = await downloader.bulk_download(filter_obj, max_files=10)

    progress.update(task, completed=len(paths))
```

### Concurrent Operations

```python
import asyncio

async def download_multiple():
    downloader = SuiteSparseDownloader(workers=8)

    # Download multiple matrices concurrently
    tasks = [
        downloader.download_by_name("ct20stif"),
        downloader.download_by_name("bcsstk14"),
        downloader.download_by_name("bcspwr01")
    ]

    paths = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(paths):
        if isinstance(result, Exception):
            print(f"Download {i} failed: {result}")
        else:
            print(f"Downloaded to: {result}")

# Run the async function
asyncio.run(download_multiple())
```

### Custom Cache Management

```python
from pathlib import Path
import shutil

class CustomDownloader(SuiteSparseDownloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clear_cache(self):
        """Clear the entire cache directory."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        for file in self.cache_dir.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size

# Usage
downloader = CustomDownloader(cache_dir="./custom_cache")
cache_size = downloader.get_cache_size()
print(f"Cache size: {cache_size / 1024 / 1024:.2f} MB")
```

### Integration with Scientific Libraries

```python
import scipy.io
import numpy as np
from pathlib import Path

async def download_and_load_matrix(name: str):
    """Download matrix and load into NumPy array."""
    downloader = SuiteSparseDownloader()

    # Download MAT file
    path = await downloader.download_by_name(name, format_type="mat")

    # Load matrix data
    mat_data = scipy.io.loadmat(path)

    # Extract the sparse matrix (usually stored under 'Problem')
    if 'Problem' in mat_data:
        matrix = mat_data['Problem'][0, 0]['A']
        return matrix.toarray() if hasattr(matrix, 'toarray') else matrix
    else:
        # Fallback: find the largest array
        arrays = {k: v for k, v in mat_data.items()
                 if isinstance(v, np.ndarray) and not k.startswith('__')}
        if arrays:
            largest_key = max(arrays.keys(), key=lambda k: arrays[k].size)
            return arrays[largest_key]

    return None

# Usage
matrix = await download_and_load_matrix("ct20stif")
if matrix is not None:
    print(f"Matrix shape: {matrix.shape}")
    print(f"Matrix dtype: {matrix.dtype}")
```

## Type Hints

The library is fully typed for better IDE support:

```python
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path

# All public APIs include proper type hints
downloader: SuiteSparseDownloader = SuiteSparseDownloader()
path: Path = await downloader.download_by_name("ct20stif")
matrices: List[Dict[str, Any]] = downloader.list_matrices()
```
