# CLI Reference

Complete command-line interface reference for the SuiteSparse Matrix Collection Downloader.

## Commands Overview

| Command | Description |
|---------|-------------|
| `ssdl download` | Download a single matrix |
| `ssdl get` | Download by name only (alias for download) |
| `ssdl bulk` | Download multiple matrices with filters |
| `ssdl list` | Search and list matrices |
| `ssdl info` | Get detailed matrix information |
| `ssdl groups` | List all available matrix groups |

## Global Options

```bash
ssdl --help                    # Show help
ssdl --version                 # Show version
```

## Download Commands

### `ssdl download`

Download a single matrix by name or group/name.

```bash
ssdl download IDENTIFIER [OPTIONS]
```

**Arguments:**
- `IDENTIFIER` - Matrix name or group/name (e.g., `ct20stif` or `Boeing/ct20stif`)

**Options:**
- `--format, -f` - File format: `mat` (default), `mm`, `rb`
- `--group, -g` - Matrix group name (optional if identifier contains group/name)
- `--output, -o` - Output directory (default: current directory)
- `--workers, -w` - Number of concurrent workers (default: 4, max: 8)
- `--verify` - Enable checksum verification (default: False)

**Examples:**
```bash
# Download by name (auto-detects group)
ssdl download ct20stif

# Download Matrix Market format
ssdl download ct20stif --format mm

# Specify group explicitly
ssdl download Boeing/ct20stif
ssdl download ct20stif --group Boeing

# Custom output directory
ssdl download ct20stif --output ./matrices

# Enable checksum verification
ssdl download ct20stif --verify
```

### `ssdl get`

Alternative command for downloading by name only.

```bash
ssdl get NAME [OPTIONS]
```

**Examples:**
```bash
# Download by name (searches all groups automatically)
ssdl get ct20stif

# With Matrix Market format
ssdl get ct20stif --format mm
```

## Bulk Operations

### `ssdl bulk`

Download multiple matrices matching filter criteria.

```bash
ssdl bulk [FILTER_OPTIONS] [OPTIONS]
```

**Options:**
- `--format, -f` - File format: `mat`, `mm`, `rb` (default: mat)
- `--output, -o` - Output directory (default: current directory)
- `--max-files` - Maximum number of files to download
- `--workers, -w` - Number of concurrent workers (default: 4)
- `--verify` - Enable checksum verification

**Examples:**
```bash
# Download SPD matrices
ssdl bulk --spd --max-files 10

# Download small to medium matrices in Matrix Market format
ssdl bulk --size 1000:50000 --format mm --output ./matrices

# Download from specific groups
ssdl bulk --group "Boeing" --group "HB" --max-files 20
```

## Search and Information

### `ssdl list`

Search and list matrices matching criteria.

```bash
ssdl list [FILTER_OPTIONS] [OPTIONS]
```

**Options:**
- `--limit` - Maximum number of results to show
- `--verbose, -v` - Show detailed information

**Examples:**
```bash
# List all Boeing matrices
ssdl list --group Boeing

# Find small test matrices
ssdl list --size :1000 --limit 10

# Search by name pattern
ssdl list --name "stif" --verbose

# List SPD matrices with size constraints
ssdl list --spd --size 1000:10000 --field real
```

### `ssdl info`

Get detailed information about a specific matrix.

```bash
ssdl info IDENTIFIER
```

**Examples:**
```bash
# Get matrix information (auto-detects group)
ssdl info ct20stif

# Specify group explicitly
ssdl info Boeing/ct20stif
ssdl info ct20stif --group Boeing
```

### `ssdl groups`

List all available matrix groups.

```bash
ssdl groups
```

## Filter Options

These filters can be used with `bulk` and `list` commands:

### Matrix Properties
- `--spd` - Symmetric positive definite matrices only (automatically filters for symmetric AND positive definite AND square matrices)
- `--field TYPE` - Field type: `real`, `complex`, `integer`, `binary`
- `--structure TYPE` - Matrix structure: `symmetric`, `unsymmetric`, etc.

### Size Filters
- `--size MIN:MAX` - Matrix size range (applies to both rows and columns)
- `--rows MIN:MAX` - Number of rows range
- `--cols MIN:MAX` - Number of columns range
- `--nnz MIN:MAX` - Number of nonzeros range

### Identification Filters
- `--group NAME` - Matrix group/collection name (partial match)
- `--name PATTERN` - Matrix name pattern (partial match)

## Range Syntax

Use these patterns for numeric ranges:

- `1000:5000` - Between 1000 and 5000 (inclusive)
- `:5000` - Up to 5000
- `1000:` - 1000 and above
- `1e4:1e6` - Scientific notation supported

**Examples:**
```bash
# Matrices with 1000-10000 rows
ssdl list --rows 1000:10000

# Large sparse matrices
ssdl list --size 100000: --nnz :1000000

# Medium-sized matrices
ssdl list --size 1e4:1e5
```

## File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| `mat` | `.mat` | MATLAB/Octave MAT-file (default) |
| `mm` | `.tar.gz` | Matrix Market format |
| `rb` | `.tar.gz` | Rutherford-Boeing format |

## Environment Variables

- `SSDL_CACHE_DIR` - Default cache directory for downloads

```bash
export SSDL_CACHE_DIR=/path/to/cache
ssdl download ct20stif  # Downloads to /path/to/cache
```

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Matrix not found
- `3` - Network error
- `4` - File I/O error

## Performance Tips

### Concurrent Downloads
```bash
# Increase workers for bulk downloads
ssdl bulk --spd --workers 8 --max-files 50
```

### Checksum Verification
```bash
# Enable for critical data integrity
ssdl download ct20stif --verify

# Disable for faster downloads (less safe)
ssdl download ct20stif  # Default: no verification
```

### Output Organization
```bash
# Organize by format
ssdl bulk --spd --format mm --output ./matrix_market_spd
ssdl bulk --spd --format mat --output ./matlab_spd

# Organize by group
ssdl bulk --group Boeing --output ./boeing_matrices
```

## Advanced Usage

### Combining Filters
```bash
# Complex filter: SPD, real-valued, medium-sized
ssdl list --spd --field real --size 5000:50000 --nnz :1000000

# Multiple groups
ssdl bulk --group "HB" --group "Boeing" --group "FIDAP" --max-files 30
```

### Scripting Integration
```bash
# Check if matrix exists before downloading
if ssdl info ct20stif > /dev/null 2>&1; then
    echo "Matrix exists, downloading..."
    ssdl download ct20stif
else
    echo "Matrix not found"
fi

# Download with error handling
ssdl download ct20stif || echo "Download failed with exit code $?"
```

### Pipeline Usage
```bash
# Get list of matrices and process
ssdl list --group Boeing --limit 5 | while read line; do
    matrix_name=$(echo $line | cut -d' ' -f1)
    ssdl download "$matrix_name"
done
```