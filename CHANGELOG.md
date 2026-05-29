# 📋 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🔄 Changed
- Installation docs now recommend `uv tool install ssdownload` as the primary CLI setup; removed outdated PyPI-unpublished and `uvx` quick-start guidance
- GitHub Release notes list `uv tool install` for CLI installs
- Installation docs note that a new terminal is required after `uv tool update-shell` before `ssdl` is on PATH

### ✨ Added
- **🆕 NEW**: System-wide cache directory support using platformdirs
  - 📁 Cache files now stored in OS-appropriate locations (e.g., `~/.cache/ssdownload/` on Linux/macOS)
  - 🧹 No more scattered `ssstats_cache.json` files in working directories
  - 🔧 Environment variable `SSDOWNLOAD_CACHE_DIR` can override default location
- **🆕 NEW**: `ssdl clean-cache` command for system cache management
  - 🧹 Clear matrix index cache (`ssstats_cache.json`) from system cache directory
  - 📊 Display cache file location and size before deletion
  - ⚡ Skip confirmation with `--yes` flag for automated scripts
  - 🔄 Forces fresh index download on next matrix operation
- 📊 Enhanced matrix information display with correct field mappings from UFstats.csv format
- 🔢 Pattern Entries field showing number of zero and explicit zero entries in sparse matrices
- 🆔 Matrix ID display in `ssdl info` command for easy reference

### 🔄 Changed
- **⚠️ BREAKING**: CSV field parsing now follows official UFstats.csv format specification
  - 📌 posdef field correctly mapped to 8th position in CSV
  - 📈 pattern_symmetry and numerical_symmetry correctly parsed as decimal values
  - 📊 All 2904 matrices now properly recognized (up from 2136)
- 🎨 Improved `ssdl info` command display:
  - 📊 Pattern/Numerical Symmetry now shown as percentages (e.g., "100%" instead of "1.000")
  - 🔍 Clear distinction between "Positive Definite" and "SPD (Symmetric Positive Definite)"
  - 🧹 Removed duplicate field displays for cleaner output
- 🧮 SPD (Symmetric Positive Definite) calculation now mathematically accurate:
  - ✅ Requires symmetric AND positive definite AND real AND square matrix
  - 🎯 ct20stif now correctly identified as SPD matrix

### 🔧 Fixed
- **🚨 CRITICAL**: Fixed CSV data source URL to use official `https://sparse.tamu.edu/files/ssstats.csv` instead of incorrect `http://sparse-files.engr.tamu.edu/files/ssstats.csv`
- **🚨 CRITICAL**: Fixed PART file pollution - downloads now check for existing files before starting and skip re-downloading existing valid files
- **🚨 CRITICAL**: Fixed --spd option logic to properly filter for Symmetric Positive Definite matrices (symmetric AND positive definite AND square)
- **🚨 CRITICAL**: Fixed CSV field order parsing according to official UFstats.csv specification
- 🔧 Fixed all MyPy type errors for improved code quality and type safety
  - ✅ Fixed Optional/Union type annotations (e.g., `float | None` instead of `float = None`)
  - ✅ Fixed dictionary type annotations in filters and CLI utilities
  - ✅ Improved numerical type safety in matrix symmetry calculations
- 🧪 Updated test suite to reflect improved SPD filtering logic and correct CSV data
- 🧹 Improved downloader cleanup logic to prevent interference with temporary files

### 🗑️ Removed
- 🧹 Removed unnecessary research/validation modules (research_filters.py, research_cli.py, research_client.py, data_validator.py, enhanced_index_manager.py)
- 🧹 Cleaned up academic/research CLI options that were not being used
- 🔄 Removed backward compatibility field `nnz_with_explicit_zeros` in favor of `pattern_entries`
