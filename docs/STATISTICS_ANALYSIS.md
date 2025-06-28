# SuiteSparse Matrix Collection Statistics Analysis

## Overview

This document analyzes the comprehensive statistics available for matrices in the SuiteSparse Matrix Collection and provides recommendations for organizing them in the ssdownload tool. This analysis is based on the official SuiteSparse documentation (`statistics.md`) and comparison with existing tools like ssgetpy.

## Official SuiteSparse Statistics

Based on the official SuiteSparse documentation, there are three categories of statistics:

### 1. Basic CSV Fields (Available in ssstats.csv)

These 12 fields are currently available in the CSV index that ssdownload uses:

| Field | Description | Current Support |
|-------|-------------|-----------------|
| `Group` | Matrix collection group name | ✓ |
| `Name` | Matrix name | ✓ |
| `nrows` | Number of rows | ✓ |
| `ncols` | Number of columns | ✓ |
| `nnz` | Number of numerically nonzero entries | ✓ |
| `isReal` | 1 if real, 0 if complex | ✓ |
| `isBinary` | 1 if binary (0/1 values only) | ✓ |
| `isND` | 1 if from 2D/3D discretization | ✓ |
| `posdef` | 1 if SPD, 0 if not, -1 if unknown | ✓ |
| `pattern_symmetry` | Pattern symmetry ratio (0-1) | ✓ |
| `numerical_symmetry` | Numerical symmetry ratio (0-1) | ✓ |
| `kind` | Problem classification string | ✓ |

### 2. Extended Index Statistics (Available in full UFindex)

These statistics are available in the full MATLAB index but not in the CSV:

| Field | Description | Current Support |
|-------|-------------|-----------------|
| `nzero` | Number of explicit zero entries | ✗ |
| `nnzdiag` | Number of nonzero diagonal entries | ✗ |
| `amd_lnz` | Cholesky factorization nonzeros after AMD ordering | ✗ |
| `amd_flops` | Floating-point operations for Cholesky factorization | ✗ |
| `amd_vnz` | Householder vector entries for QR factorization | ✗ |
| `amd_rnz` | R factor entries for QR factorization | ✗ |
| `nblocks` | Number of blocks from dmperm | ✗ |
| `sprank` | Structural rank of the matrix | ✗ |
| `RBtype` | Rutherford-Boeing type (3-letter code) | ✗ |
| `cholcand` | 1 if candidate for Cholesky factorization | ✗ |
| `ncc` | Number of strongly-connected components | ✗ |
| `isGraph` | 1 if best considered as graph problem | ✗ |

### 3. SVD-based Statistics (Web-only)

These statistics are only available on individual matrix web pages:

| Field | Description | Current Support |
|-------|-------------|-----------------|
| `norm(A)` | 2-norm of A (largest singular value) | ✗ |
| `min(svd(A))` | Smallest singular value | ✗ |
| `cond(A)` | 2-norm condition number | ✗ |
| `rank(A)` | Numerical rank | ✗ |
| `sprank(A)-rank(A)` | Rank deficiency | ✗ |
| `null space dimension` | Dimension of null space | ✗ |
| `full numerical rank?` | Yes/no indicator | ✗ |
| `singular value gap` | Gap between singular values | ✗ |

## Comparison with ssgetpy

ssgetpy (the existing Python library) provides similar functionality but with limitations:

### ssgetpy Fields
- Basic identification: `id`, `group`, `name`
- Dimensions: `rows`, `cols`, `nnz`
- Properties: `dtype`, `is2d3d`, `isspd`, `psym`, `nsym`, `kind`
- Methods: `download()`, `url()`, `localpath()`

### ssgetpy Approach
- Single level of information display
- Programmatic access oriented
- Limited to CSV-available fields
- No separation between basic and detailed views

## Recommended Command Structure

### Current `ssdl info` Command

The current implementation focuses on the most commonly needed information:

**Displayed Fields:**
- Matrix ID (derived from CSV position)
- Group and Name
- Dimensions (rows×cols format)
- Nonzeros (NNZ)
- Field type classification
- Symmetry properties (boolean and numerical values)
- SPD status
- Problem classification
- Download URLs

### Proposed `ssdl detail` Command

A future detailed command should provide comprehensive information organized by category:

#### Section 1: Basic Properties
- Matrix ID, Group, Name
- Dimensions and sparsity
- Explicit zeros count (when available)
- Diagonal nonzeros (when available)

#### Section 2: Mathematical Properties  
- Field type and numerical properties
- Symmetry analysis (pattern and numerical)
- SPD classification
- Structural rank (when available)
- Cholesky candidacy (when available)

#### Section 3: Problem Classification
- Problem type/kind
- 2D/3D discretization flag
- Graph problem classification (when available)
- Rutherford-Boeing type (when available)

#### Section 4: Factorization Estimates
- AMD ordering statistics (when available)
- QR factorization estimates (when available)
- Connected components analysis (when available)
- Block structure information (when available)

#### Section 5: Advanced Analysis
- SVD-based statistics (when available via web scraping)
- Condition number estimates
- Rank analysis

## Implementation Strategy

### Phase 1: Enhanced CSV Parsing (Complete)
- ✅ All 12 CSV fields are properly parsed and stored
- ✅ Derived fields (matrix_id, field classification) implemented
- ✅ Proper boolean and numerical field handling

### Phase 2: Extended Statistics (Future)
- Research access to full UFindex data
- Implement web scraping for additional statistics
- Add support for SVD-based metrics

### Phase 3: Command Structure (Future)
- Keep current `info` command for basic information
- Implement `detail` command for comprehensive statistics
- Add filtering options for specific statistic categories

## Field Priority Classification

### High Priority (Essential for most users)
- Basic dimensions and sparsity
- Symmetry and SPD properties
- Problem classification
- Field type information

### Medium Priority (Useful for advanced analysis)
- Structural rank
- Cholesky candidacy
- Connected components
- Diagonal properties

### Low Priority (Specialized use cases)
- Factorization estimates
- Block structure
- SVD-based statistics

## Current Status

As of the latest implementation:
- ✅ All basic CSV fields are supported
- ✅ Matrix ID assignment implemented
- ✅ Clean, organized info display
- ✅ Proper symmetry calculation from numerical_symmetry
- ✅ Rich formatting with logical grouping
- ❌ Extended statistics not yet available
- ❌ Detail command not yet implemented
- ❌ Web-based statistics not accessible

## Future Enhancements

1. **Data Source Expansion**: Research access to full UFindex or alternative data sources
2. **Web Scraping**: Implement optional web scraping for SVD statistics
3. **Caching Strategy**: Cache extended statistics locally when available
4. **User Preferences**: Allow users to configure which statistics to display
5. **Export Functionality**: Enable exporting detailed statistics to JSON/CSV format

## ssgetpy vs ssdownload Comparison

| Aspect | ssgetpy | Current ssdownload |
|--------|---------|-------------------|
| **Basic Info** | ✓ Similar coverage | ✓ Comprehensive coverage |
| **Display Format** | Object attributes | Rich table format |
| **Information Levels** | Single level | Single level (info only) |
| **Advanced Stats** | Limited (CSV only) | Limited (CSV only) |
| **SVD Stats** | Not included | Not included |
| **Presentation** | Programmatic access | User-friendly CLI display |
| **Matrix ID** | ✓ Supported | ✓ Derived from position |
| **Organization** | Flat structure | Organized sections |

## Missing Statistics Analysis

### Currently Missing from ssdownload
All extended and SVD-based statistics are missing because they're not available in the CSV format that ssdownload currently uses.

### Access Methods for Missing Statistics
1. **UFindex MATLAB data**: Contains extended statistics but requires MATLAB or alternative parsing
2. **Web scraping**: Individual matrix pages contain SVD statistics
3. **Alternative APIs**: Research if SuiteSparse provides other data access methods

## Recommendations

1. **Keep current info command simple**: Focus on most commonly needed statistics
2. **Implement detail command**: Provide comprehensive view when needed
3. **Research data sources**: Investigate access to extended statistics
4. **Gradual enhancement**: Add statistics as data sources become available
5. **User feedback**: Monitor which additional statistics users request most

This analysis should guide future development of the statistics display functionality in ssdownload.