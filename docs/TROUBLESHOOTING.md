# Troubleshooting Guide

Common issues and solutions for the SuiteSparse Matrix Collection Downloader.

## Installation Issues

### Python Version Problems

**Problem**: `ImportError` or compatibility issues
```
ERROR: Package requires Python >=3.12
```

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.12+ if needed
# Using pyenv (recommended)
pyenv install 3.12
pyenv local 3.12

# Using conda
conda install python=3.12

# Using system package manager
sudo apt update && sudo apt install python3.12  # Ubuntu
brew install python@3.12                        # macOS
```

### uv Installation Issues

**Problem**: `command not found: uv`

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative methods
pip install uv
brew install uv  # macOS
```

**Problem**: Permission denied during installation

**Solution**:
```bash
# Use user installation
pip install --user uv

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install uv
```

### Dependency Conflicts

**Problem**: Conflicting package versions

**Solution**:
```bash
# Clean install with uv
rm -rf .venv uv.lock
uv sync

# Or create fresh virtual environment
python -m venv fresh_env
source fresh_env/bin/activate
pip install -e .
```

## Network and Download Issues

### Connection Timeouts

**Problem**: Downloads fail with timeout errors
```
NetworkError: Request timeout after 30 seconds
```

**Solutions**:

1. **Increase timeout**:
```python
downloader = SuiteSparseDownloader(timeout=300.0)  # 5 minutes
```

2. **Check network connection**:
```bash
# Test connection to SuiteSparse
curl -I https://sparse.tamu.edu/
ping sparse.tamu.edu
```

3. **Use fewer workers**:
```python
downloader = SuiteSparseDownloader(workers=2)  # Reduce from default 4
```

### Proxy and Firewall Issues

**Problem**: Downloads fail behind corporate firewall

**Solutions**:

1. **Configure proxy**:
```bash
export HTTPS_PROXY=https://proxy.company.com:8080
export HTTP_PROXY=http://proxy.company.com:8080
uv run ssdl download ct20stif
```

2. **Use proxy in Python**:
```python
import httpx
from ssdownload import SuiteSparseDownloader

# Custom HTTP client with proxy
proxy_client = httpx.AsyncClient(
    proxies={"https://": "https://proxy.company.com:8080"}
)
downloader = SuiteSparseDownloader()
# Note: Custom client configuration may require code modification
```

3. **Verify SSL certificates**:
```bash
# Test SSL connection
openssl s_client -connect sparse.tamu.edu:443
```

### Resume Support Issues

**Problem**: Downloads don't resume properly

**Solutions**:

1. **Clean partial files**:
```bash
# Remove .part files and retry
find . -name "*.part" -delete
uv run ssdl download ct20stif
```

2. **Check disk space**:
```bash
df -h  # Check available space
```

3. **Verify file permissions**:
```bash
ls -la ./  # Check write permissions in output directory
```

## Matrix Discovery Issues

### Matrix Not Found Errors

**Problem**: `MatrixNotFoundError: Matrix 'xyz' not found`

**Solutions**:

1. **Search for similar names**:
```bash
# Find matrices with similar names
uv run ssdl list --name "xyz" --limit 10
uv run ssdl list --name "xy" --limit 10
```

2. **Check exact spelling**:
```bash
# List all matrices in a group
uv run ssdl list --group Boeing
```

3. **Use case-insensitive search**:
```python
# Python API - search manually
downloader = SuiteSparseDownloader()
all_matrices = await downloader.find_matrices()
matches = [m for m in all_matrices if 'xyz' in m['name'].lower()]
```

### Empty Search Results

**Problem**: Filters return no results

**Solutions**:

1. **Broaden search criteria**:
```bash
# Start with loose filters
uv run ssdl list --spd --limit 10
uv run ssdl list --group "Boeing" --limit 10

# Gradually add constraints
uv run ssdl list --spd --size :10000 --limit 10
```

2. **Check filter syntax**:
```bash
# Correct range syntax
uv run ssdl list --size 1000:10000  # ✓ Correct
uv run ssdl list --size 1000-10000  # ✗ Wrong
uv run ssdl list --size "1000:10000"  # ✓ Also correct
```

3. **Verify available options**:
```bash
# Check available groups
uv run ssdl groups

# Check available field types
uv run ssdl list --field real --limit 5
uv run ssdl list --field complex --limit 5
```

## File Format Issues

### Corrupted Downloads

**Problem**: Downloaded files are corrupted or unreadable

**Solutions**:

1. **Enable checksum verification**:
```bash
uv run ssdl download ct20stif --verify
```

```python
downloader = SuiteSparseDownloader(verify_checksums=True)
```

2. **Re-download with verification**:
```bash
# Remove existing file and re-download
rm ./Boeing/ct20stif.mat
uv run ssdl download Boeing/ct20stif --verify
```

3. **Try different format**:
```bash
# If MAT file is corrupted, try Matrix Market
uv run ssdl download ct20stif --format mm
```

### Matrix Loading Issues

**Problem**: Cannot load matrix with scipy.io.loadmat

**Solutions**:

1. **Check file format**:
```python
import scipy.io
import os

file_path = "Boeing/ct20stif.mat"
print(f"File size: {os.path.getsize(file_path)} bytes")

try:
    data = scipy.io.loadmat(file_path)
    print(f"Keys: {list(data.keys())}")
except Exception as e:
    print(f"Error loading: {e}")
```

2. **Use Matrix Market format**:
```bash
# Download in Matrix Market format
uv run ssdl download ct20stif --format mm

# Extract and load
tar -xzf ct20stif.tar.gz
```

```python
import scipy.sparse
matrix = scipy.sparse.mmread("ct20stif/ct20stif.mtx")
```

3. **Check matrix structure**:
```python
# For MAT files, matrices are often in 'Problem' field
data = scipy.io.loadmat("ct20stif.mat")
if 'Problem' in data:
    problem = data['Problem'][0, 0]
    matrix = problem['A']  # The actual sparse matrix
    print(f"Matrix shape: {matrix.shape}")
    print(f"Matrix type: {type(matrix)}")
```

## Performance Issues

### Slow Downloads

**Problem**: Downloads are very slow

**Solutions**:

1. **Increase concurrent workers**:
```python
downloader = SuiteSparseDownloader(workers=8)  # Max is 8
```

2. **Use faster format**:
```bash
# MAT files are typically smaller
uv run ssdl download ct20stif --format mat
```

3. **Check network bandwidth**:
```bash
# Test download speed
curl -o /dev/null -s -w "%{speed_download}\n" https://sparse.tamu.edu/
```

### Memory Issues

**Problem**: Out of memory errors during downloads

**Solutions**:

1. **Reduce concurrent downloads**:
```python
downloader = SuiteSparseDownloader(workers=2)
```

2. **Download smaller matrices first**:
```bash
# Filter by size
uv run ssdl bulk --size :10000 --max-files 10
```

3. **Monitor memory usage**:
```bash
# Watch memory usage during downloads
watch -n 1 'ps aux | grep ssdl'
```

## CLI Issues

### Command Not Found

**Problem**: `command not found: ssdl`

**Solutions**:

1. **Use with uv run**:
```bash
uv run ssdl --help  # Instead of just 'ssdl'
```

2. **Check installation**:
```bash
# Verify package is installed
uv run python -c "import ssdownload; print('OK')"
```

3. **Activate virtual environment** (if using pip):
```bash
source venv/bin/activate
ssdl --help
```

### Permission Errors

**Problem**: Permission denied when writing files

**Solutions**:

1. **Check directory permissions**:
```bash
ls -la .
mkdir -p matrices && chmod 755 matrices
```

2. **Use different output directory**:
```bash
uv run ssdl download ct20stif --output ~/Downloads/matrices
```

3. **Run with appropriate permissions**:
```bash
# Create directory first
mkdir -p ./matrices
uv run ssdl download ct20stif --output ./matrices
```

## Python API Issues

### Async/Await Errors

**Problem**: `RuntimeError: asyncio.run() cannot be called from a running event loop`

**Solutions**:

1. **Use await in async context**:
```python
# ✓ Correct - in async function
async def main():
    downloader = SuiteSparseDownloader()
    path = await downloader.download_by_name("ct20stif")
    return path

# Run with asyncio
import asyncio
result = asyncio.run(main())
```

2. **For Jupyter notebooks**:
```python
# Install nest-asyncio for Jupyter
# pip install nest-asyncio

import nest_asyncio
nest_asyncio.apply()

# Now you can use asyncio.run() in Jupyter
result = asyncio.run(main())
```

3. **Use synchronous methods when available**:
```python
# Some methods have sync versions
downloader = SuiteSparseDownloader()
matrices = downloader.list_matrices()  # Synchronous
```

### Import Errors

**Problem**: `ImportError: cannot import name 'SuiteSparseDownloader'`

**Solutions**:

1. **Check installation**:
```bash
uv run python -c "import ssdownload; print(ssdownload.__file__)"
```

2. **Reinstall package**:
```bash
uv sync
# or
pip install -e .
```

3. **Check Python path**:
```python
import sys
print(sys.path)
```

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all HTTP requests and responses will be logged
downloader = SuiteSparseDownloader()
await downloader.download_by_name("ct20stif")
```

### Verbose CLI Output

```bash
# Add verbose flag if available
uv run ssdl download ct20stif --verbose
```

### Check File Contents

```bash
# Verify downloaded files
file Boeing/ct20stif.mat
ls -la Boeing/ct20stif.mat

# For compressed files
file ct20stif.tar.gz
tar -tzf ct20stif.tar.gz  # List contents without extracting
```

### Test Network Connectivity

```bash
# Test basic connectivity
curl -I https://sparse.tamu.edu/

# Test specific matrix URL
curl -I https://sparse.tamu.edu/mat/Boeing/ct20stif.mat
```

## Getting Further Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Search existing GitHub issues**
3. **Try the solution with a simple example**
4. **Gather diagnostic information**:
   ```bash
   uv run python --version
   uv run python -c "import ssdownload; print(ssdownload.__version__)"
   uv run ssdl --help
   ```

### Reporting Issues

When reporting bugs, include:

1. **Python version** and operating system
2. **Package version**: `uv run python -c "import ssdownload; print(ssdownload.__version__)"`
3. **Complete error message** with traceback
4. **Minimal example** that reproduces the issue
5. **Network environment** (proxy, firewall, etc.)

### Example Issue Report

```
**Environment:**
- Python: 3.12.0
- ssdownload: 0.1.0
- OS: macOS 14.0
- Network: Corporate firewall with proxy

**Problem:**
Downloads fail with timeout error

**Error message:**
```
NetworkError: Request timeout after 30 seconds
```

**Minimal example:**
```python
from ssdownload import SuiteSparseDownloader
downloader = SuiteSparseDownloader()
await downloader.download_by_name("ct20stif")  # Fails here
```

**What I tried:**
- Increased timeout to 300 seconds
- Tested network connectivity with curl
- Tried with different matrix

**Additional context:**
Behind corporate firewall, other downloads work fine
```

This format helps maintainers quickly understand and reproduce the issue.