# Development Guide

Complete guide for contributing to and developing the SuiteSparse Matrix Collection Downloader.

## Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd ssdownload

# Install dependencies with uv (recommended)
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Verify setup
uv run pytest
```

## Development Environment

### Prerequisites

- **Python 3.12+** - Required for full compatibility
- **uv** (recommended) or **pip** for package management
- **Git** for version control

### Package Management

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable package management:

```bash
# Install all dependencies (including dev)
uv sync

# Add new dependency
uv add httpx

# Add development dependency
uv add --dev pytest-mock

# Update dependencies
uv sync --upgrade

# Run commands in project environment
uv run pytest
uv run ssdl --help
```

### Global Installation for Development

For convenient CLI testing without `uv run` prefix:

```bash
# Install globally for easy testing
uv tool install .

# Verify installation
ssdl --help

# After making code changes
uv tool upgrade ssdownload --reinstall

# Test changes immediately
ssdl download ct20stif  # No need for uv run
```

### Alternative: pip setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Project Structure

```
ssdownload/
├── src/ssdownload/           # Main package
│   ├── __init__.py          # Package exports
│   ├── cli.py               # Command-line interface
│   ├── cli_utils.py         # CLI utility functions
│   ├── client.py            # Main SuiteSparseDownloader class
│   ├── config.py            # Configuration management
│   ├── downloader.py        # File downloading with resume support
│   ├── exceptions.py        # Custom exception classes
│   ├── filters.py           # Matrix filtering and search
│   └── index_manager.py     # CSV index fetching and caching
├── tests/                   # Test suite
│   ├── test_*.py           # Unit tests
│   └── conftest.py         # Test configuration
├── docs/                   # Documentation
├── test_output/            # Test artifacts (git-ignored)
└── pyproject.toml          # Project configuration
```

## Running Tests

### Test Categories

- **Unit tests**: Fast, isolated tests with mocking (default)
- **Integration tests**: Real API calls to SuiteSparse servers
- **Slow tests**: Actual file downloads (marked with `@pytest.mark.slow`)

### Test Commands

```bash
# Run all tests (excluding slow network tests)
uv run pytest

# Run all tests including slow network/download tests
uv run pytest -m "slow or not slow"

# Run only fast unit tests
uv run pytest -m "not slow"

# Run with coverage
uv run pytest --cov=ssdownload --cov-report=html

# Run specific test file
uv run pytest tests/test_client.py -v

# Run API integration tests
uv run pytest tests/test_api_integration.py -v

# Run real download tests (requires network)
uv run pytest tests/test_api_integration.py -m slow -v

# Run tests matching pattern
uv run pytest -k "test_download" -v
```

### Test Output

All test outputs are saved to `test_output/` directory to keep the project clean. This directory is git-ignored.

## Code Quality

### Formatting and Linting

```bash
# Format code (modifies files)
uv run ruff format src tests

# Check linting (read-only)
uv run ruff check src tests

# Fix linting issues automatically
uv run ruff check --fix src tests

# Type checking
uv run mypy src
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks:

```bash
# Install hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files

# Update hook versions
uv run pre-commit autoupdate
```

### Configuration

Code quality tools are configured in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true
```

## Architecture Overview

### Core Components

**Main Classes:**
- `SuiteSparseDownloader` (client.py) - Primary API class
- `IndexManager` (index_manager.py) - CSV index fetching and caching
- `FileDownloader` (downloader.py) - File downloads with resume support
- `Filter` (filters.py) - Type-safe matrix filtering

**CLI:**
- `cli.py` - Typer-based command-line interface
- `cli_utils.py` - CLI utility functions

**Support:**
- `config.py` - Centralized configuration
- `exceptions.py` - Custom exception hierarchy

### Key Patterns

**Async/Await**: Core downloading uses asyncio with semaphore-based concurrency control

**Caching Strategy**:
- Memory cache for recently accessed data
- Disk cache for matrix index (1-hour TTL)
- Smart file existence checks

**Resume Support**: Temporary `.part` files enable HTTP Range request resumption

**Error Handling**: Comprehensive exception hierarchy for different failure modes

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch
from ssdownload import SuiteSparseDownloader, Filter

class TestSuiteSparseDownloader:
    @pytest.fixture
    def downloader(self):
        return SuiteSparseDownloader(cache_dir="./test_cache")

    async def test_download_by_name(self, downloader):
        # Test implementation
        pass

    @pytest.mark.slow
    async def test_real_download(self, downloader):
        # Network-dependent test
        pass
```

### Mocking Guidelines

Use mocking for external dependencies:

```python
@patch('ssdownload.client.httpx.AsyncClient')
async def test_download_with_mock(self, mock_client):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.content = b"test data"
    mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

    # Test with mocked HTTP client
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.slow
async def test_network_operation():
    # Requires network access
    pass

@pytest.mark.integration
async def test_api_integration():
    # Tests API integration
    pass
```

## Adding New Features

### 1. Design Phase

1. **Create issue** describing the feature
2. **Design API** - consider backwards compatibility
3. **Update CLAUDE.md** with implementation notes
4. **Plan tests** - unit, integration, and edge cases

### 2. Implementation Phase

1. **Create feature branch** from main
2. **Implement core functionality** with type hints
3. **Add comprehensive tests** (aim for >90% coverage)
4. **Update documentation** as you go
5. **Add CLI support** if user-facing

### 3. Quality Assurance

1. **Run full test suite** including slow tests
2. **Check code quality** with ruff and mypy
3. **Test CLI manually** with real examples
4. **Update documentation** - ensure all examples work
5. **Add changelog entry**

### Example: Adding a New Filter Option

```python
# 1. Add to Filter class in filters.py
@dataclass
class Filter:
    # ... existing fields ...
    new_property: Optional[bool] = None

# 2. Update filtering logic in filters.py
def apply_filter(self, matrix_data: Dict[str, Any]) -> bool:
    # ... existing checks ...
    if self.new_property is not None:
        if matrix_data.get('new_property') != self.new_property:
            return False
    return True

# 3. Add CLI option in cli_utils.py
def build_filter(..., new_property: bool = None) -> Filter:
    return Filter(
        # ... existing args ...
        new_property=new_property
    )

# 4. Add CLI argument in cli.py
@app.command()
def list_matrices(
    # ... existing args ...
    new_property: bool = typer.Option(None, "--new-property", help="Filter by new property")
):
    filter_obj = build_filter(..., new_property=new_property)

# 5. Add tests
class TestNewProperty:
    def test_filter_with_new_property(self):
        filter_obj = Filter(new_property=True)
        # Test filtering logic

    async def test_cli_new_property(self):
        # Test CLI integration
```

## Documentation Maintenance

### Keep Documentation Current

When making changes:

1. **Update affected documentation files**
2. **Test all code examples** to ensure they work
3. **Update CLAUDE.md** with architectural changes
4. **Verify README links** point to correct sections
5. **Update CLI reference** for new options

### Documentation Testing

```bash
# Test CLI examples from documentation
uv run ssdl --help
uv run ssdl list --spd --limit 5

# Test Python examples (create test script)
python test_doc_examples.py
```

## Release Process

### Version Management

1. **Update version** in `pyproject.toml`
2. **Add changelog entry** in `CHANGELOG.md`
3. **Update documentation** references to new version
4. **Test installation** from clean environment

### Pre-release Checklist

- [ ] All tests pass (including slow tests)
- [ ] Documentation is up to date
- [ ] Code quality checks pass
- [ ] Manual CLI testing completed
- [ ] Examples in documentation work
- [ ] CHANGELOG.md updated

### Release Commands

```bash
# Build package
uv build

# Test build
uv run python -m twine check dist/*

# Upload to test PyPI
uv run python -m twine upload --repository testpypi dist/*

# Upload to PyPI
uv run python -m twine upload dist/*
```

## Debugging and Profiling

### Debugging Tips

```python
# Enable asyncio debug mode
import asyncio
asyncio.get_event_loop().set_debug(True)

# Add logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pytest with debugger
uv run pytest --pdb tests/test_client.py::test_specific_function
```

### Performance Profiling

```python
# Profile async code
import cProfile
import asyncio

async def profile_download():
    downloader = SuiteSparseDownloader()
    await downloader.download_by_name("ct20stif")

cProfile.run('asyncio.run(profile_download())')
```

## Contributing Guidelines

### Code Style

- Follow **PEP 8** style guide
- Use **type hints** for all public APIs
- Write **docstrings** for classes and public methods
- Keep functions **focused** and **testable**
- Use **meaningful variable names**

### Git Workflow

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/new-feature`
3. **Make changes** with good commit messages
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit pull request** with description

### Commit Messages

Use conventional commit format:

```
feat: add new matrix filtering option
fix: resolve download resume issue
docs: update API documentation
test: add integration tests for CLI
refactor: simplify filter logic
```

### Pull Request Process

1. **Ensure all tests pass**
2. **Update documentation**
3. **Add changelog entry**
4. **Request review** from maintainers
5. **Address feedback**
6. **Squash commits** if requested

## Troubleshooting Development Issues

### Common Issues

**Import errors after changes:**
```bash
# Reinstall in development mode
uv sync
```

**Tests failing with network errors:**
```bash
# Run only unit tests
uv run pytest -m "not slow"
```

**Type checking errors:**
```bash
# Check specific file
uv run mypy src/ssdownload/client.py
```

**Pre-commit hooks failing:**
```bash
# Fix formatting
uv run ruff format src tests
uv run ruff check --fix src tests
```

### Getting Help

- **Check existing issues** on GitHub
- **Review test failures** carefully
- **Use debugger** for complex issues
- **Ask questions** in discussions

## Performance Considerations

### Optimization Guidelines

- **Use async/await** for I/O operations
- **Implement caching** for expensive operations
- **Limit concurrent operations** to avoid overwhelming servers
- **Use appropriate data structures** for filtering
- **Profile before optimizing** - measure don't guess

### Memory Management

- **Stream large files** instead of loading into memory
- **Clean up temporary files** after operations
- **Use generators** for large result sets
- **Monitor memory usage** in tests
