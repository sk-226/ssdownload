"""CSV index manager for SuiteSparse Matrix Collection.

This module provides functionality to fetch, parse, and cache the matrix index
from the SuiteSparse Matrix Collection. The index is stored as a CSV file and
contains metadata about all available matrices.

The IndexManager class handles:
- Fetching the CSV index from the remote server
- Parsing CSV content into structured matrix metadata
- Caching the index both in memory and on disk
- Providing search functionality for matrices and groups

Example:
    >>> from pathlib import Path
    >>> from ssdownload.index_manager import IndexManager
    >>>
    >>> manager = IndexManager(Path("/tmp/cache"))
    >>> matrices = await manager.get_index()
    >>> groups = await manager.get_groups()
    >>> matrix_info = await manager.find_matrix_info("ct20stif")

The CSV format from SuiteSparse contains the following columns:
- Group name
- Matrix name
- Number of rows
- Number of columns
- Number of nonzeros
- Real flag (1/0)
- Binary flag (1/0)
- 2D/3D flag (1/0)
- Symmetric flag (1/0)
- SPD flag (1/0)
- Reserved field
- Kind description
- NNZ with explicit zeros
"""

import json
import time
from pathlib import Path
from typing import Any

import httpx

from .config import Config
from .exceptions import IndexError


class IndexManager:
    """Manages the SuiteSparse matrix index from CSV."""

    def __init__(self, cache_dir: Path):
        """Initialize the index manager.

        Args:
            cache_dir: Directory to store cached index files

        Note:
            The cache directory will be created if it doesn't exist.
            Cache files are stored as JSON for fast loading.
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._csv_index_cache: list[dict[str, Any]] | None = None
        self._csv_index_cache_time: float = 0
        self._groups_cache: set[str] | None = None

    async def get_index(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Get the matrix index from SuiteSparse CSV file.

        Args:
            force_refresh: Force refresh of cached index

        Returns:
            List of matrix metadata dictionaries
        """
        current_time = time.time()

        # Check if we have a valid cached index
        if (
            not force_refresh
            and self._csv_index_cache is not None
            and (current_time - self._csv_index_cache_time) < Config.CACHE_TTL
        ):
            return self._csv_index_cache

        # Try to load from disk cache
        index_file = self.cache_dir / "ssstats_cache.json"
        if not force_refresh and index_file.exists():
            try:
                stat = index_file.stat()
                if (current_time - stat.st_mtime) < Config.CACHE_TTL:
                    with open(index_file, encoding="utf-8") as f:
                        self._csv_index_cache = json.load(f)
                        self._csv_index_cache_time = current_time
                        return self._csv_index_cache
            except (json.JSONDecodeError, OSError):
                pass

        # Fetch fresh CSV index
        matrices = await self._fetch_csv_index()

        # Cache to disk
        self._save_index_to_disk(matrices, index_file)

        self._csv_index_cache = matrices
        self._csv_index_cache_time = current_time
        return matrices

    async def _fetch_csv_index(self) -> list[dict[str, Any]]:
        """Fetch and parse CSV index from remote."""
        async with httpx.AsyncClient(**Config.get_http_client_config()) as client:
            response = await client.get(Config.CSV_INDEX_URL)
            response.raise_for_status()
            csv_content = response.text

        return self._parse_csv_content(csv_content)

    def _parse_csv_content(self, csv_content: str) -> list[dict[str, Any]]:
        """Parse CSV content into matrix dictionaries."""
        matrices = []
        lines = csv_content.strip().split("\n")

        # Skip first two lines (count and date)
        data_lines = lines[2:]

        for line in data_lines:
            if not line.strip():
                continue

            matrix_info = self._parse_csv_line(line)
            if matrix_info:
                matrices.append(matrix_info)

        return matrices

    def _parse_csv_line(self, line: str) -> dict[str, Any] | None:
        """Parse a single CSV line into matrix info."""
        parts = line.split(",")
        if len(parts) < 12:
            return None

        try:
            matrix_info = {
                "group": parts[0],
                "name": parts[1],
                "rows": int(parts[2]),
                "cols": int(parts[3]),
                "nnz": int(parts[4]),
                "real": bool(int(parts[5])),
                "binary": bool(int(parts[6])),
                "complex": not bool(int(parts[5])),  # If not real, assume complex
                "2d_3d": bool(int(parts[7])),
                "symmetric": bool(int(parts[8])),
                "spd": bool(int(parts[9])),
                "kind": parts[11] if len(parts) > 11 else "",
                "nnz_with_explicit_zeros": int(parts[12])
                if len(parts) > 12
                else int(parts[4]),
            }

            # Add derived fields for compatibility
            matrix_info.update(
                {
                    "num_rows": matrix_info["rows"],
                    "num_cols": matrix_info["cols"],
                    "nonzeros": matrix_info["nnz"],
                    "field": self._get_field_type(matrix_info),
                    "structure": "symmetric"
                    if matrix_info["symmetric"]
                    else "unsymmetric",
                    "posdef": matrix_info["spd"],  # SPD implies positive definite
                }
            )

            return matrix_info

        except (ValueError, IndexError):
            return None

    def _get_field_type(self, matrix_info: dict[str, Any]) -> str:
        """Determine field type from matrix info."""
        if matrix_info["real"]:
            return "real"
        elif matrix_info["binary"]:
            return "binary"
        else:
            return "complex"

    def _save_index_to_disk(
        self, matrices: list[dict[str, Any]], index_file: Path
    ) -> None:
        """Save index to disk cache."""
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(matrices, f, indent=2)
        except OSError:
            pass  # Cache write failure is not critical

    async def get_groups(self) -> set[str]:
        """Get all available groups from the index.

        Returns:
            Set of group names
        """
        if self._groups_cache is not None:
            return self._groups_cache

        matrices = await self.get_index()
        groups = {matrix["group"] for matrix in matrices}
        self._groups_cache = groups
        return groups

    async def find_matrix_info(self, name: str) -> dict[str, Any] | None:
        """Find matrix information by name.

        Args:
            name: Matrix name

        Returns:
            Matrix info dictionary if found, None otherwise
        """
        matrices = await self.get_index()

        for matrix in matrices:
            if matrix["name"] == name:
                return matrix

        return None

    async def find_matrix_group(self, name: str) -> str | None:
        """Find the group for a matrix by name.

        Args:
            name: Matrix name

        Returns:
            Group name if found, None otherwise
        """
        matrix_info = await self.find_matrix_info(name)
        return matrix_info["group"] if matrix_info else None
