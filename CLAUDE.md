# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📝 Documentation Maintenance Protocol

**CRITICAL**: When making ANY code changes, you MUST also update documentation:

1. **Test all code examples** in documentation files before committing
2. **Update affected docs** when changing APIs, CLI options, or functionality
3. **Verify README links** still work after restructuring
4. **Update CLI_REFERENCE.md** when adding/modifying commands or options
5. **Update API_REFERENCE.md** when changing method signatures or adding classes
6. **Test installation instructions** in INSTALLATION.md after dependency changes
7. **Add troubleshooting entries** for new error conditions
8. **Update EXAMPLES.md** with new usage patterns

**Documentation Testing Checklist**:
- [ ] All CLI examples in docs actually work: `uv run ssdl [command]`
- [ ] All Python examples run without errors
- [ ] Installation steps work from clean environment
- [ ] Links between documentation files are valid
- [ ] New features have corresponding examples
- [ ] Error handling examples are accurate

**When adding features**:
1. Update relevant docs DURING development, not after
2. Add examples showing the new functionality
3. Update CLI help text and ensure it matches CLI_REFERENCE.md
4. Test that documentation examples work with the new code

## 📋 CHANGELOG.md Maintenance Protocol

**CRITICAL**: Following [Keep a Changelog](https://keepachangelog.com/) format, ALL notable changes MUST be documented in CHANGELOG.md:

**Required for EVERY change**:
1. **Add entry to CHANGELOG.md** immediately when making changes
2. **Use proper categories**: Added, Changed, Deprecated, Removed, Fixed, Security
3. **Follow semantic versioning**: Major.Minor.Patch (breaking.feature.bugfix)
4. **Write user-focused descriptions** (not technical implementation details)

**Changelog Categories**:
- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Now removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

**Example entries**:
```markdown
## [Unreleased]

### Added
- New `--verify` option for checksum validation during downloads
- Support for resuming interrupted bulk downloads

### Changed
- Improved error messages for network timeout issues
- Updated README.md structure for better discoverability

### Fixed
- Fixed matrix auto-detection for matrices with special characters in names
```

**When to increment versions**:
- **Patch (0.0.X)** - Bug fixes, documentation updates
- **Minor (0.X.0)** - New features, backward-compatible changes
- **Major (X.0.0)** - Breaking changes to API or CLI

## Development Commands

### Package Management (uv)
- `uv sync` - Install dependencies and sync environment
- `uv run ssdl --help` - Run CLI tool directly
- `uv add <package>` - Add new dependency
- `uv remove <package>` - Remove dependency

### Testing
- `uv run pytest` - Run unit tests (excludes slow network tests)
- `uv run pytest -m "slow or not slow"` - Run all tests including network/download tests
- `uv run pytest -m "not slow"` - Run only fast unit tests
- `uv run pytest --cov=ssdownload --cov-report=html` - Run with coverage
- `uv run pytest tests/test_client.py -v` - Run specific test file
- `uv run pytest tests/test_api_integration.py -m slow -v` - Run real download tests

### Code Quality
- `uv run ruff format src tests` - Format code
- `uv run ruff check src tests` - Lint code
- `uv run ruff check --fix src tests` - Fix linting issues automatically
- `uv run mypy src` - Type checking

### Running the CLI
- `uv run ssdl download ct20stif` - Download matrix by name (auto-detects group)
- `uv run ssdl download Boeing/ct20stif` - Download with explicit group/name
- `uv run ssdl list --spd --size 1000:10000` - List matrices with filters
- `uv run ssdl bulk --spd --format mm --max-files 10` - Bulk download

## Architecture Overview

### Core Components

**Main Classes:**
- `SuiteSparseDownloader` (client.py) - Primary API class for downloading matrices
- `IndexManager` (index_manager.py) - Handles CSV index fetching and caching with 1-hour TTL
- `FileDownloader` (downloader.py) - Manages file downloads with resume support via HTTP Range requests
- `Filter` (filters.py) - Type-safe matrix filtering and search functionality

**CLI:**
- `cli.py` - Typer-based command-line interface with Rich formatting
- `cli_utils.py` - CLI utility functions for argument parsing and display

**Support:**
- `config.py` - Centralized configuration with defaults and validation
- `exceptions.py` - Custom exception hierarchy for error handling

### Key Architectural Patterns

**Async/Await Pattern:** Core downloading uses asyncio with semaphore-based concurrency control (max 8 workers)

**Caching Strategy:**
- Memory cache for recently accessed data
- Disk cache for matrix index (1-hour TTL in `ssstats_cache.json`)
- Smart file existence checks to prevent re-downloads

**Resume Support:** Temporary `.part` files track download progress, enabling HTTP Range request resumption

**Error Handling:** Comprehensive exception hierarchy:
- `SSDownloadError` (base)
- `MatrixNotFoundError`, `ChecksumError`, `DownloadError`, `NetworkError`, `IndexError`

### Matrix Identification
The system supports flexible matrix identification:
- By name only: `ct20stif` (auto-detects group)
- By group/name: `Boeing/ct20stif`
- With explicit group parameter: `ct20stif --group Boeing`

### File Formats
- `mat` - MATLAB/Octave MAT-file (default, `.mat` extension)
- `mm` - Matrix Market format (`.tar.gz`)
- `rb` - Rutherford-Boeing format (`.tar.gz`)

## Test Structure

**Test Categories:**
- Unit tests: Fast, isolated with mocking (default when running `pytest`)
- Integration tests: Real API calls to SuiteSparse servers
- Slow tests: Actual file downloads (marked with `@pytest.mark.slow`)

All test outputs saved to `test_output/` directory to keep project clean.

## Key Configuration

**Dependencies:** Uses modern Python stack with httpx (async HTTP), Typer (CLI), Rich (terminal UI), Pydantic (validation)

**Python Version:** Requires Python 3.12+

**Entry Point:** `ssdl` command via `ssdownload.cli:app`

**Project Structure:**
```
src/ssdownload/           # Main package
tests/                    # Test suite
test_output/              # Test artifacts (git-ignored)
test_matrices/            # Test data
```
