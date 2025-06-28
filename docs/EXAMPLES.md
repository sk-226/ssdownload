# Usage Examples

Comprehensive examples for using the SuiteSparse Matrix Collection Downloader.

## Command Format Note

Examples are shown in both formats:
- **Global installation** (recommended): `ssdl command`
- **Development with uv**: `uv run ssdl command`

Choose the format that matches your installation method.

## Basic CLI Examples

### Single Matrix Downloads

#### Global Installation
```bash
# Download by name (auto-detects group)
ssdl download ct20stif

# Download specific format
ssdl download ct20stif --format mm

# Specify group explicitly
ssdl download Boeing/ct20stif
ssdl download ct20stif --group Boeing

# Custom output directory
ssdl download ct20stif --output ./my_matrices

# Download with checksum verification
ssdl download ct20stif --verify
```

#### Development with uv
```bash
# Download by name (auto-detects group)
uv run ssdl download ct20stif

# Download specific format
uv run ssdl download ct20stif --format mm

# Specify group explicitly
uv run ssdl download Boeing/ct20stif
uv run ssdl download ct20stif --group Boeing

# Custom output directory
uv run ssdl download ct20stif --output ./my_matrices

# Download with checksum verification
uv run ssdl download ct20stif --verify
```

### Matrix Information and Search

#### Global Installation
```bash
# Get matrix details
ssdl info ct20stif

# List matrices from specific group
ssdl list --group Boeing --limit 10

# Search by size
ssdl list --size 1000:10000 --limit 5

# Search SPD matrices
ssdl list --spd --field real --verbose

# Search by name pattern
ssdl list --name "stif" --limit 3
```

#### Development with uv
```bash
# Get matrix details
uv run ssdl info ct20stif

# List matrices from specific group
uv run ssdl list --group Boeing --limit 10

# Search by size
uv run ssdl list --size 1000:10000 --limit 5

# Search SPD matrices
uv run ssdl list --spd --field real --verbose

# Search by name pattern
uv run ssdl list --name "stif" --limit 3
```

### Bulk Downloads

#### Global Installation
```bash
# Download SPD matrices
ssdl bulk --spd --max-files 5

# Download by size range in Matrix Market format
ssdl bulk --size 1000:5000 --format mm --max-files 10

# Download from multiple groups
ssdl bulk --group "Boeing" --group "HB" --max-files 15

# Complex filter: real-valued, medium-sized, sparse
ssdl bulk --field real --size 5000:50000 --nnz :100000 --max-files 20
```

#### Development with uv
```bash
# Download SPD matrices
uv run ssdl bulk --spd --max-files 5

# Download by size range in Matrix Market format
uv run ssdl bulk --size 1000:5000 --format mm --max-files 10

# Download from multiple groups
uv run ssdl bulk --group "Boeing" --group "HB" --max-files 15

# Complex filter: real-valued, medium-sized, sparse
uv run ssdl bulk --field real --size 5000:50000 --nnz :100000 --max-files 20
```

## Python API Examples

### Basic Usage

```python
import asyncio
from ssdownload import SuiteSparseDownloader, Filter
from pathlib import Path

async def basic_example():
    # Initialize downloader
    downloader = SuiteSparseDownloader(cache_dir="./matrices")

    # Download single matrix
    path = await downloader.download_by_name("ct20stif")
    print(f"Downloaded to: {path}")

    # Download specific format
    path = await downloader.download("Boeing", "ct20stif", format_type="mm")
    print(f"Matrix Market file: {path}")

# Run the example
asyncio.run(basic_example())
```

### Search and Filter Examples

```python
import asyncio
from ssdownload import SuiteSparseDownloader, Filter

async def search_examples():
    downloader = SuiteSparseDownloader()

    # Find SPD matrices
    spd_filter = Filter(spd=True, n_rows=(1000, 10000))
    matrices = await downloader.find_matrices(spd_filter)

    print(f"Found {len(matrices)} SPD matrices:")
    for matrix in matrices[:5]:  # Show first 5
        print(f"  {matrix['group']}/{matrix['name']}: "
              f"{matrix['num_rows']}×{matrix['num_cols']}, "
              f"nnz={matrix['nnz']:,}")

    # Search by group and field type
    boeing_filter = Filter(group="Boeing", field="real")
    boeing_matrices = await downloader.find_matrices(boeing_filter)
    print(f"\nFound {len(boeing_matrices)} Boeing real-valued matrices")

    # Complex filter
    complex_filter = Filter(
        n_rows=(5000, 50000),
        nnz=(None, 1000000),
        field="real",
        structure="symmetric"
    )
    filtered = await downloader.find_matrices(complex_filter)
    print(f"Complex filter matched {len(filtered)} matrices")

asyncio.run(search_examples())
```

### Bulk Download Examples

```python
import asyncio
from ssdownload import SuiteSparseDownloader, Filter

async def bulk_download_examples():
    downloader = SuiteSparseDownloader(
        cache_dir="./bulk_matrices",
        workers=6,
        verify_checksums=True
    )

    # Download small SPD matrices
    small_spd = Filter(spd=True, n_rows=(None, 5000))
    paths = await downloader.bulk_download(
        small_spd,
        format_type="mat",
        max_files=10
    )
    print(f"Downloaded {len(paths)} small SPD matrices:")
    for path in paths:
        print(f"  {path}")

    # Download matrices from specific groups
    group_filter = Filter(group="HB")
    hb_paths = await downloader.bulk_download(
        group_filter,
        format_type="mm",
        max_files=5
    )
    print(f"\nDownloaded {len(hb_paths)} HB matrices in Matrix Market format")

asyncio.run(bulk_download_examples())
```

## Scientific Computing Examples

### Load Matrix into NumPy/SciPy

```python
import asyncio
import scipy.io
import numpy as np
from ssdownload import SuiteSparseDownloader

async def load_matrix_example():
    downloader = SuiteSparseDownloader()

    # Download and load a matrix
    path = await downloader.download_by_name("bcsstk14", format_type="mat")
    mat_data = scipy.io.loadmat(path)

    # Extract the matrix (typically stored in 'Problem' field)
    if 'Problem' in mat_data:
        problem = mat_data['Problem'][0, 0]
        matrix = problem['A']

        print(f"Matrix shape: {matrix.shape}")
        print(f"Matrix type: {type(matrix)}")
        print(f"Non-zeros: {matrix.nnz}")
        print(f"Density: {matrix.nnz / (matrix.shape[0] * matrix.shape[1]):.6f}")

        # Convert to dense for small matrices
        if matrix.shape[0] < 1000:
            dense = matrix.toarray()
            print(f"Dense matrix shape: {dense.shape}")
            print(f"First 5x5 block:\n{dense[:5, :5]}")

asyncio.run(load_matrix_example())
```

### Matrix Analysis Pipeline

```python
import asyncio
import scipy.io
import numpy as np
from ssdownload import SuiteSparseDownloader, Filter

async def matrix_analysis_pipeline():
    """Download and analyze multiple matrices."""
    downloader = SuiteSparseDownloader()

    # Find small SPD matrices for analysis
    filter_obj = Filter(spd=True, n_rows=(100, 1000), field="real")
    matrices_info = await downloader.find_matrices(filter_obj)

    print(f"Analyzing {len(matrices_info[:5])} matrices:")

    for info in matrices_info[:5]:  # Analyze first 5
        name = info['name']
        group = info['group']

        # Download matrix
        path = await downloader.download(group, name)

        # Load and analyze
        mat_data = scipy.io.loadmat(path)
        if 'Problem' in mat_data:
            matrix = mat_data['Problem'][0, 0]['A']

            # Basic properties
            eigenvals = np.linalg.eigvals(matrix.toarray()) if matrix.shape[0] < 500 else None
            condition_number = np.max(eigenvals) / np.min(eigenvals) if eigenvals is not None else "N/A"

            print(f"\n{group}/{name}:")
            print(f"  Size: {matrix.shape[0]}×{matrix.shape[1]}")
            print(f"  Non-zeros: {matrix.nnz:,}")
            print(f"  Density: {matrix.nnz / (matrix.shape[0] * matrix.shape[1]):.6f}")
            if eigenvals is not None:
                print(f"  Condition number: {condition_number:.2e}")
                print(f"  Eigenvalue range: [{np.min(eigenvals):.2e}, {np.max(eigenvals):.2e}]")

asyncio.run(matrix_analysis_pipeline())
```

## Advanced Usage Examples

### Custom Progress Tracking

```python
import asyncio
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from ssdownload import SuiteSparseDownloader, Filter

async def custom_progress_example():
    downloader = SuiteSparseDownloader(workers=4)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:

        # Search task
        search_task = progress.add_task("Searching matrices...", total=None)
        filter_obj = Filter(spd=True, n_rows=(1000, 5000))
        matrices = await downloader.find_matrices(filter_obj)
        progress.remove_task(search_task)

        # Download task
        download_count = min(10, len(matrices))
        download_task = progress.add_task(
            f"Downloading {download_count} matrices...",
            total=download_count
        )

        paths = []
        for i, matrix_info in enumerate(matrices[:download_count]):
            path = await downloader.download(
                matrix_info['group'],
                matrix_info['name']
            )
            paths.append(path)
            progress.update(download_task, advance=1)

        progress.update(download_task, description=f"Downloaded {len(paths)} matrices!")

asyncio.run(custom_progress_example())
```

### Error Handling and Retry Logic

```python
import asyncio
from ssdownload import SuiteSparseDownloader, Filter
from ssdownload.exceptions import MatrixNotFoundError, NetworkError, DownloadError

async def robust_download_example():
    downloader = SuiteSparseDownloader(timeout=60.0)

    matrix_names = ["ct20stif", "bcsstk14", "nonexistent_matrix", "bcspwr01"]

    async def download_with_retry(name: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                path = await downloader.download_by_name(name)
                return path, None
            except MatrixNotFoundError as e:
                return None, f"Matrix not found: {e}"
            except NetworkError as e:
                if attempt < max_retries - 1:
                    print(f"Network error for {name}, retrying... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None, f"Network error after {max_retries} attempts: {e}"
            except DownloadError as e:
                return None, f"Download error: {e}"

        return None, f"Failed after {max_retries} attempts"

    # Download with error handling
    results = []
    for name in matrix_names:
        print(f"Downloading {name}...")
        path, error = await download_with_retry(name)

        if path:
            print(f"  ✓ Downloaded to: {path}")
            results.append(path)
        else:
            print(f"  ✗ Failed: {error}")

    print(f"\nSuccessfully downloaded {len(results)} out of {len(matrix_names)} matrices")

asyncio.run(robust_download_example())
```

### Concurrent Matrix Processing

```python
import asyncio
import scipy.io
from concurrent.futures import ThreadPoolExecutor
from ssdownload import SuiteSparseDownloader, Filter

def analyze_matrix_file(file_path):
    """CPU-intensive matrix analysis (runs in thread pool)."""
    try:
        mat_data = scipy.io.loadmat(file_path)
        if 'Problem' in mat_data:
            matrix = mat_data['Problem'][0, 0]['A']
            return {
                'path': file_path,
                'shape': matrix.shape,
                'nnz': matrix.nnz,
                'density': matrix.nnz / (matrix.shape[0] * matrix.shape[1])
            }
    except Exception as e:
        return {'path': file_path, 'error': str(e)}
    return {'path': file_path, 'error': 'Unknown format'}

async def concurrent_processing_example():
    downloader = SuiteSparseDownloader(workers=8)

    # Download matrices
    filter_obj = Filter(n_rows=(100, 2000), field="real")
    matrices_info = (await downloader.find_matrices(filter_obj))[:10]

    print(f"Downloading {len(matrices_info)} matrices...")
    download_tasks = [
        downloader.download(info['group'], info['name'])
        for info in matrices_info
    ]
    paths = await asyncio.gather(*download_tasks, return_exceptions=True)

    # Filter successful downloads
    valid_paths = [p for p in paths if not isinstance(p, Exception)]
    print(f"Successfully downloaded {len(valid_paths)} matrices")

    # Analyze matrices concurrently using thread pool
    print("Analyzing matrices...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        loop = asyncio.get_event_loop()
        analysis_tasks = [
            loop.run_in_executor(executor, analyze_matrix_file, path)
            for path in valid_paths
        ]
        results = await asyncio.gather(*analysis_tasks)

    # Display results
    print("\nAnalysis Results:")
    for result in results:
        if 'error' in result:
            print(f"  {result['path'].name}: Error - {result['error']}")
        else:
            print(f"  {result['path'].name}: {result['shape']}, "
                  f"nnz={result['nnz']:,}, density={result['density']:.6f}")

asyncio.run(concurrent_processing_example())
```

## Integration Examples

### Jupyter Notebook Integration

```python
# Cell 1: Setup
import asyncio
import matplotlib.pyplot as plt
import scipy.io
from ssdownload import SuiteSparseDownloader, Filter

# For Jupyter async support
import nest_asyncio
nest_asyncio.apply()

downloader = SuiteSparseDownloader(cache_dir="./notebook_matrices")

# Cell 2: Download and visualize
async def download_and_plot():
    # Download a small matrix
    path = await downloader.download_by_name("bcsstk14")

    # Load matrix
    mat_data = scipy.io.loadmat(path)
    matrix = mat_data['Problem'][0, 0]['A'].toarray()

    # Plot sparsity pattern
    plt.figure(figsize=(8, 8))
    plt.spy(matrix, markersize=0.5)
    plt.title("Sparsity Pattern of bcsstk14")
    plt.show()

    return matrix

matrix = await download_and_plot()
print(f"Matrix shape: {matrix.shape}")
```

### Command Line Scripting

```bash
#!/bin/bash
# download_matrices.sh - Batch download script

set -e

MATRICES=("ct20stif" "bcsstk14" "bcspwr01")
OUTPUT_DIR="./downloaded_matrices"
FORMAT="mm"

echo "Downloading ${#MATRICES[@]} matrices to $OUTPUT_DIR"

for matrix in "${MATRICES[@]}"; do
    echo "Downloading $matrix..."
    if uv run ssdl download "$matrix" --format "$FORMAT" --output "$OUTPUT_DIR"; then
        echo "  ✓ Success: $matrix"
    else
        echo "  ✗ Failed: $matrix"
    fi
done

echo "Download completed. Files in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR/"
```

### Data Science Pipeline

```python
import asyncio
import pandas as pd
from pathlib import Path
from ssdownload import SuiteSparseDownloader, Filter

async def create_matrix_dataset():
    """Create a dataset of matrix properties for analysis."""
    downloader = SuiteSparseDownloader()

    # Get matrices from multiple groups
    groups = ["Boeing", "HB", "FIDAP"]
    all_matrices = []

    for group in groups:
        group_filter = Filter(group=group, n_rows=(100, 10000))
        matrices = await downloader.find_matrices(group_filter)
        all_matrices.extend(matrices[:20])  # Limit per group

    # Create DataFrame
    df = pd.DataFrame(all_matrices)

    # Add computed columns
    if not df.empty:
        df['density'] = df['nnz'] / (df['num_rows'] * df['num_cols'])
        df['aspect_ratio'] = df['num_rows'] / df['num_cols']
        df['size_category'] = pd.cut(df['num_rows'],
                                   bins=[0, 1000, 10000, float('inf')],
                                   labels=['Small', 'Medium', 'Large'])

    # Save dataset
    output_file = "matrix_dataset.csv"
    df.to_csv(output_file, index=False)
    print(f"Created dataset with {len(df)} matrices: {output_file}")

    # Basic statistics
    print("\nDataset Statistics:")
    print(df.groupby(['group', 'size_category']).size().unstack(fill_value=0))

    return df

# Run the pipeline
df = asyncio.run(create_matrix_dataset())
```

## Cache Management Examples

### Clearing System Cache

```bash
# Clear cache with confirmation
uv run ssdl clean-cache

# Clear cache automatically (useful for scripts)
uv run ssdl clean-cache --yes
```

### Automation Scripts with Cache Management

```bash
#!/bin/bash
# Script to ensure fresh data for important downloads

echo "Ensuring fresh matrix data..."
uv run ssdl clean-cache --yes

echo "Downloading latest Boeing matrices..."
uv run ssdl bulk --group Boeing --max-files 5

echo "Getting fresh matrix information..."
uv run ssdl info ct20stif
```

### Periodic Cache Refresh

```bash
#!/bin/bash
# Weekly cache refresh script for cron

CACHE_AGE_DAYS=7
CACHE_DIR=$(python3 -c "
from ssdownload.config import Config
import time
import os
cache_file = Config.get_default_cache_dir() / 'ssstats_cache.json'
if cache_file.exists():
    age_days = (time.time() - cache_file.stat().st_mtime) / 86400
    print(int(age_days))
else:
    print(999)
")

if [ "$CACHE_AGE_DAYS" -gt 7 ]; then
    echo "Cache is older than 7 days, refreshing..."
    uv run ssdl clean-cache --yes
    echo "Cache refreshed"
else
    echo "Cache is fresh (${CACHE_AGE_DAYS} days old)"
fi
```

### Python Integration with Cache Management

```python
import subprocess
import os
from pathlib import Path

def ensure_fresh_cache():
    """Clear cache and ensure fresh data for analysis."""
    try:
        # Clear the cache
        result = subprocess.run(['uv', 'run', 'ssdl', 'clean-cache', '--yes'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Cache cleared successfully")
        else:
            print(f"Cache clear failed: {result.stderr}")
    except Exception as e:
        print(f"Error clearing cache: {e}")

def download_with_fresh_data(matrix_name):
    """Download matrix with guaranteed fresh index data."""
    ensure_fresh_cache()

    # Now download the matrix
    result = subprocess.run(['uv', 'run', 'ssdl', 'download', matrix_name],
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ Downloaded {matrix_name}")
        return True
    else:
        print(f"✗ Failed to download {matrix_name}: {result.stderr}")
        return False

# Example usage
if __name__ == "__main__":
    # Download critical matrices with fresh data
    critical_matrices = ['ct20stif', 'nos5', 'bcsstk14']

    for matrix in critical_matrices:
        success = download_with_fresh_data(matrix)
        if not success:
            print(f"Critical matrix {matrix} failed to download!")
            break
```
