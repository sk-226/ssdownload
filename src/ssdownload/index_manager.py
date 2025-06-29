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

The CSV format from SuiteSparse contains the following columns (UFstats.csv format):
- Group name
- Matrix name
- Number of rows
- Number of columns
- Number of nonzeros
- isReal flag (1=real, 0=complex)
- isBinary flag (1=binary, 0=not binary)
- isND flag (1=2D/3D discretization, 0=not)
- posdef flag (1=positive definite, 0=not)
- Pattern symmetry (0-1 ratio)
- Numerical symmetry (0-1 ratio)
- Kind description
- Pattern entries (number of zero and explicit zero entries in the sparse matrix)
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

    def __init__(self, cache_dir: Path | None = None):
        """Initialize the index manager.

        Args:
            cache_dir: Directory to store cached index files. If None, uses the
                      system default cache directory.

        Note:
            The cache directory will be created if it doesn't exist.
            Cache files are stored as JSON for fast loading.
        """
        self.cache_dir = cache_dir or Config.get_default_cache_dir()
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
                        cached_data = json.load(f)
                        if isinstance(cached_data, list):
                            self._csv_index_cache = cached_data
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
        try:
            async with httpx.AsyncClient(**Config.get_http_client_config()) as client:
                response = await client.get(Config.CSV_INDEX_URL)
                response.raise_for_status()
                csv_content = response.text
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
            from .exceptions import NetworkError

            raise NetworkError(f"Failed to fetch CSV index: {e}") from e
        except Exception as e:
            from .exceptions import IndexError

            raise IndexError(f"Error fetching CSV index: {e}") from e

        try:
            return self._parse_csv_content(csv_content)
        except Exception as e:
            from .exceptions import IndexError

            raise IndexError(f"Error parsing CSV content: {e}") from e

    def _parse_csv_content(self, csv_content: str) -> list[dict[str, Any]]:
        """Parse CSV content into matrix dictionaries."""
        matrices = []
        lines = csv_content.strip().split("\n")

        # Skip first two lines (count and date)
        data_lines = lines[2:]

        for index, line in enumerate(data_lines):
            if not line.strip():
                continue

            matrix_info = self._parse_csv_line(line)
            if matrix_info:
                # Add matrix ID based on position (1-indexed)
                matrix_info["matrix_id"] = index + 1
                matrices.append(matrix_info)

        return matrices

    def _parse_csv_line(self, line: str) -> dict[str, Any] | None:
        """Parse a single CSV line into matrix info."""
        parts = line.split(",")
        if len(parts) < 12:
            return None

        try:
            # Parse based on official UFstats.csv format
            matrix_info = {
                "group": parts[0],
                "name": parts[1],
                "rows": int(parts[2]),
                "cols": int(parts[3]),
                "nnz": int(parts[4]),
                "real": bool(int(parts[5])),  # isReal: 1=real, 0=complex
                "binary": bool(int(parts[6])),  # isBinary: 1=binary, 0=not
                "complex": not bool(int(parts[5])),  # If not real, assume complex
                "2d_3d": bool(int(parts[7])),  # isND: 1=2D/3D discretization
                "posdef": bool(int(parts[8])),  # posdef: 1=positive definite, 0=not
                "pattern_symmetry": float(parts[9]),  # Pattern symmetry (0-1)
                "numerical_symmetry": float(parts[10]),  # Numerical symmetry (0-1)
                "kind": parts[11] if len(parts) > 11 else "",
                "pattern_entries": int(parts[12])
                if len(parts) > 12
                else int(
                    parts[4]
                ),  # number of zero (and explicit zero) entries in the sparse matrix
            }

            # Derive symmetric flag from numerical_symmetry
            # Consider matrices with >99% numerical symmetry as symmetric
            numerical_sym = matrix_info["numerical_symmetry"]
            matrix_info["symmetric"] = (
                isinstance(numerical_sym, int | float) and numerical_sym >= 0.99
            )

            # Calculate SPD (Symmetric Positive Definite): symmetric AND positive definite AND real AND square
            is_square = matrix_info["rows"] == matrix_info["cols"]
            matrix_info["spd"] = (
                matrix_info["symmetric"]
                and matrix_info["posdef"]
                and matrix_info["real"]
                and is_square
            )

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
