# AGENTS.md

## Cursor Cloud specific instructions

### Overview

**ssdownload** (`ssdl`) is a Python CLI tool and library for downloading sparse matrices from the [SuiteSparse Matrix Collection](https://sparse.tamu.edu/). It is a pure client-side application with no local services to run — it talks to external SuiteSparse servers.

### Dev commands

All dev commands are documented in `CLAUDE.md` and `docs/DEVELOPMENT.md`. Key ones:

- `uv sync` — install/sync all dependencies
- `uv run pytest` — run unit tests (excludes slow/network tests)
- `uv run pytest -m "slow or not slow"` — run all tests including network tests
- `uv run ruff check src tests` / `uv run ruff format src tests` — lint/format
- `uv run mypy src` — type checking
- `uv run ssdl --help` — run the CLI

### Non-obvious caveats

- **`ruff` must be added as a dev dependency** — it is listed in `[project.optional-dependencies]` but needs to be in `[tool.uv]` dev-dependencies to be available via `uv run ruff`. The update script handles this.
- **Python 3.12+ required** — the codebase uses `X | Y` union syntax and other 3.12 features.
- The `list` CLI command function shadows Python's built-in `list` type. Use `builtins.list` for type annotations in that scope.
- **Two-phase filtering**: When page-scraped filter options (e.g. `--cond`, `--norm`, `--cholesky`) are used, the system first filters by CSV index data, then scrapes individual matrix web pages for extended metadata. This can be slow for large candidate sets.
- **Page data caching**: Scraped page data is cached as `page_info_cache.json` in the cache directory (1-year TTL — page data rarely changes). The CSV index is cached as `ssstats_cache.json` (1h TTL). Both caches can be cleared with `ssdl clean-cache`.
- Unit tests run fully offline using mocks (`pytest-httpx`). Integration/contract/e2e tests require network access to `sparse.tamu.edu`.
- `beautifulsoup4` is a runtime dependency used for page scraping (not just dev tooling).
