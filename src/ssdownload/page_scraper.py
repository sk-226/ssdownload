"""Web page scraper for SuiteSparse Matrix Collection.

Fetches and parses extended matrix information from individual matrix
detail pages at sparse.tamu.edu. This data includes SVD-based statistics
(condition number, matrix norm, rank, etc.) and structural properties
(structural rank, Dmperm blocks, connected components, etc.) that are
not available in the CSV index.
"""

import json
import time
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .config import Config


class PageScraper:
    """Scrapes extended matrix information from SuiteSparse web pages."""

    MATRIX_PAGE_URL = "https://sparse.tamu.edu"
    PAGE_CACHE_FILENAME = "page_info_cache.json"
    PAGE_CACHE_TTL = 365 * 86400  # 1 year (page data rarely changes)

    # Mapping from table header text to standardized field names
    STRUCTURAL_FIELDS = {
        "Structural Rank": ("structural_rank", "int"),
        "Structural Rank Full": ("structural_rank_full", "bool"),
        "Num Dmperm Blocks": ("num_dmperm_blocks", "int"),
        "Strongly Connect Components": ("num_strong_components", "int"),
        "Num Explicit Zeros": ("num_explicit_zeros", "int"),
        "Pattern Symmetry": ("page_pattern_symmetry", "percent"),
        "Numeric Symmetry": ("page_numeric_symmetry", "percent"),
        "Cholesky Candidate": ("cholesky_candidate", "bool"),
        "Positive Definite": ("page_positive_definite", "bool"),
        "Type": ("rb_type", "str"),
    }

    SVD_FIELDS = {
        "Matrix Norm": ("matrix_norm", "float"),
        "Minimum Singular Value": ("min_singular_value", "float"),
        "Condition Number": ("condition_number", "float"),
        "Rank": ("numerical_rank", "int"),
        "sprank(A)-rank(A)": ("rank_deficiency", "int"),
        "Null Space Dimension": ("null_space_dim", "int"),
        "Full Numerical Rank?": ("full_numerical_rank", "bool"),
    }

    BASIC_FIELDS = {
        "Date": ("date", "str"),
        "Author": ("author", "str"),
        "Editor": ("editor", "str"),
    }

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Config.get_default_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._page_cache: dict[str, dict[str, Any]] = {}
        self._cache_loaded = False

    def _load_disk_cache(self) -> None:
        """Load the page info cache from disk."""
        if self._cache_loaded:
            return
        cache_file = self.cache_dir / self.PAGE_CACHE_FILENAME
        if cache_file.exists():
            try:
                stat = cache_file.stat()
                if (time.time() - stat.st_mtime) < self.PAGE_CACHE_TTL:
                    with open(cache_file, encoding="utf-8") as f:
                        self._page_cache = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        self._cache_loaded = True

    def _save_disk_cache(self) -> None:
        """Save the page info cache to disk."""
        cache_file = self.cache_dir / self.PAGE_CACHE_FILENAME
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self._page_cache, f, indent=2)
        except OSError:
            pass

    def _parse_value(self, raw: str, value_type: str) -> Any:
        """Parse a raw string value into the appropriate type."""
        raw = raw.strip()
        if not raw:
            return None

        if value_type == "int":
            try:
                return int(raw.replace(",", ""))
            except ValueError:
                return None
        elif value_type == "float":
            try:
                return float(raw)
            except ValueError:
                return None
        elif value_type == "percent":
            try:
                return float(raw.replace("%", "")) / 100.0
            except ValueError:
                return None
        elif value_type == "bool":
            return raw.lower() in ("yes", "true", "1")
        else:
            return raw

    def _parse_page_html(self, html: str) -> dict[str, Any]:
        """Parse HTML of a matrix detail page into a dict of extended info."""
        soup = BeautifulSoup(html, "html.parser")
        result: dict[str, Any] = {}

        tables = soup.find_all("table", class_="table")

        from bs4 import Tag

        for table in tables:
            if not isinstance(table, Tag):
                continue
            for row in table.find_all("tr"):
                if not isinstance(row, Tag):
                    continue
                th = row.find("th")
                td = row.find("td")
                if not th or not td:
                    continue
                if not isinstance(th, Tag) or not isinstance(td, Tag):
                    continue
                key = th.get_text(strip=True)
                val = td.get_text(strip=True)

                if key in self.STRUCTURAL_FIELDS:
                    field_name, field_type = self.STRUCTURAL_FIELDS[key]
                    parsed = self._parse_value(val, field_type)
                    if parsed is not None:
                        result[field_name] = parsed

                elif key in self.SVD_FIELDS:
                    field_name, field_type = self.SVD_FIELDS[key]
                    parsed = self._parse_value(val, field_type)
                    if parsed is not None:
                        result[field_name] = parsed

                elif key in self.BASIC_FIELDS:
                    field_name, field_type = self.BASIC_FIELDS[key]
                    parsed = self._parse_value(val, field_type)
                    if parsed is not None:
                        result[field_name] = parsed

        return result

    async def fetch_page_info(
        self, group: str, name: str, use_cache: bool = True
    ) -> dict[str, Any]:
        """Fetch extended matrix info from its SuiteSparse web page.

        Args:
            group: Matrix group name
            name: Matrix name
            use_cache: Whether to use cached results

        Returns:
            Dictionary of extended matrix properties
        """
        cache_key = f"{group}/{name}"

        if use_cache:
            self._load_disk_cache()
            if cache_key in self._page_cache:
                return self._page_cache[cache_key]

        url = f"{self.MATRIX_PAGE_URL}/{group}/{name}"
        try:
            async with httpx.AsyncClient(**Config.get_http_client_config()) as client:
                response = await client.get(url)
                response.raise_for_status()
                page_info = self._parse_page_html(response.text)
        except Exception:
            page_info = {}

        if use_cache and page_info:
            self._page_cache[cache_key] = page_info
            self._save_disk_cache()

        return page_info

    async def enrich_matrix_info(self, matrix_info: dict[str, Any]) -> dict[str, Any]:
        """Enrich a matrix info dict with page-scraped data.

        Args:
            matrix_info: Existing matrix info dict (from CSV index)

        Returns:
            Enriched copy of the matrix info dict
        """
        group = matrix_info.get("group", "")
        name = matrix_info.get("name", "")
        if not group or not name:
            return matrix_info

        page_info = await self.fetch_page_info(group, name)
        enriched = dict(matrix_info)
        enriched.update(page_info)
        return enriched

    async def enrich_matrices(
        self,
        matrices: list[dict[str, Any]],
        concurrency: int = 4,
    ) -> list[dict[str, Any]]:
        """Enrich multiple matrix info dicts with page-scraped data.

        Uses concurrent requests with a semaphore to limit load.

        Args:
            matrices: List of matrix info dicts
            concurrency: Max concurrent requests

        Returns:
            List of enriched matrix info dicts
        """
        import asyncio

        semaphore = asyncio.Semaphore(concurrency)
        results: list[dict[str, Any]] = [{}] * len(matrices)

        async def enrich_one(idx: int, matrix: dict[str, Any]) -> None:
            async with semaphore:
                results[idx] = await self.enrich_matrix_info(matrix)

        tasks = [enrich_one(i, m) for i, m in enumerate(matrices)]
        await asyncio.gather(*tasks)
        return results
