"""SuiteSparse Matrix Collection Downloader client."""

import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .config import Config
from .downloader import FileDownloader
from .exceptions import MatrixNotFoundError
from .filters import Filter
from .index_manager import IndexManager


class SuiteSparseDownloader:
    """Client for downloading matrices from SuiteSparse Matrix Collection."""

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        workers: int = Config.DEFAULT_WORKERS,
        timeout: float = Config.DEFAULT_TIMEOUT,
        verify_checksums: bool = False,
        extract_archives: bool = True,
        keep_archives: bool = False,
        flat_structure: bool = False,
    ):
        """Initialize the downloader.

        Args:
            cache_dir: Directory to store downloaded files. If None, uses system
                      default cache directory for index caching and current directory
                      for matrix downloads.
            workers: Number of concurrent download workers
            timeout: HTTP request timeout in seconds
            verify_checksums: Whether to verify file checksums after download (default: False)
            extract_archives: Whether to automatically extract tar.gz files (default: True)
            keep_archives: Whether to keep original tar.gz files after extraction (default: False)
            flat_structure: Whether to save files directly in output directory without group subdirectories (default: False)
        """
        self.cache_dir = Path(cache_dir or Path.cwd())
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.workers = min(workers, Config.MAX_WORKERS)
        self.timeout = timeout
        self.verify_checksums = verify_checksums
        self.extract_archives = extract_archives
        self.keep_archives = keep_archives
        self.flat_structure = flat_structure

        self.console = Console()
        # IndexManager uses system cache by default, but can be overridden for downloads
        index_cache_dir = None if cache_dir is None else self.cache_dir
        self.index_manager = IndexManager(index_cache_dir)
        self.file_downloader = FileDownloader(
            verify_checksums=verify_checksums,
            timeout=timeout,
            extract_archives=extract_archives,
            keep_archives=keep_archives,
        )

    async def download(
        self,
        group: str,
        name: str,
        format_type: str = "mat",
        output_dir: str | Path | None = None,
        _show_progress: bool = True,
    ) -> Path:
        """Download a single matrix.

        Args:
            group: Matrix group name
            name: Matrix name
            format_type: File format ('mat', 'mm', 'rb')
            output_dir: Output directory (default: cache_dir)
            _show_progress: Internal flag to control progress display

        Returns:
            Path to downloaded file
        """
        if output_dir is None:
            output_dir = self.cache_dir
        else:
            output_dir = Path(output_dir)

        # Determine output path
        ext = Config.get_file_extension(format_type)
        if self.flat_structure:
            output_path = output_dir / f"{name}{ext}"
        else:
            output_path = output_dir / group / f"{name}{ext}"

        # Get download URL and checksum
        download_url = Config.get_matrix_url(group, name, format_type)
        expected_md5 = None

        if self.verify_checksums:
            expected_md5 = await self.file_downloader.get_checksum(
                group, name, format_type
            )

        # Download with or without progress
        if _show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console,
            ) as progress:
                task = progress.add_task(f"Downloading {name}", total=100)

                final_path = await self.file_downloader.download_file(
                    download_url,
                    output_path,
                    expected_md5,
                    progress,
                    task,
                    format_type,
                )
        else:
            # Download without progress bar (for bulk downloads)
            final_path = await self.file_downloader.download_file(
                download_url,
                output_path,
                expected_md5,
                None,
                None,
                format_type,
            )

        return final_path

    async def _get_available_groups(self):
        """Get all available groups from the index.

        Returns:
            Set of group names
        """
        return await self.index_manager.get_groups()

    async def download_by_name(
        self,
        name: str,
        format_type: str = "mat",
        output_dir: str | Path | None = None,
    ) -> Path:
        """Download a matrix by name only (automatically find group).

        Args:
            name: Matrix name
            format_type: File format ('mat', 'mm', 'rb')
            output_dir: Output directory (default: cache_dir)

        Returns:
            Path to downloaded file
        """
        # Try to find the group
        group = await self.index_manager.find_matrix_group(name)
        if group is None:
            raise MatrixNotFoundError(
                f"Could not find matrix '{name}' in any known group"
            )

        # Download using the found group
        return await self.download(group, name, format_type, output_dir)

    async def find_matrices(
        self, filter_obj: Filter | None = None
    ) -> list[dict[str, Any]]:
        """Find matrices matching the given filter.

        Args:
            filter_obj: Filter criteria

        Returns:
            List of matching matrix metadata dictionaries
        """
        matrices = await self.index_manager.get_index()

        if filter_obj is None:
            return matrices

        return [matrix for matrix in matrices if filter_obj.matches(matrix)]

    async def bulk_download(
        self,
        filter_obj: Filter | None = None,
        format_type: str = "mat",
        output_dir: str | Path | None = None,
        max_files: int | None = None,
    ) -> list[Path]:
        """Download multiple matrices matching filter criteria.

        Args:
            filter_obj: Filter criteria
            format_type: File format ('mat', 'mm', 'rb')
            output_dir: Output directory
            max_files: Maximum number of files to download

        Returns:
            List of paths to downloaded files
        """
        # Find matching matrices
        matrices = await self.find_matrices(filter_obj)

        if max_files is not None:
            matrices = matrices[:max_files]

        if not matrices:
            self.console.print("No matrices found matching criteria")
            return []

        self.console.print(f"Found {len(matrices)} matrices to download")

        # Create download tasks
        semaphore = asyncio.Semaphore(self.workers)
        downloaded_paths = []

        async def download_with_semaphore(matrix: dict[str, Any]) -> Path | None:
            async with semaphore:
                try:
                    group = matrix.get("group", "")
                    name = matrix.get("name", "")
                    if not group or not name:
                        return None

                    path = await self.download(
                        group, name, format_type, output_dir, _show_progress=False
                    )
                    return path
                except Exception as e:
                    self.console.print(
                        f"Failed to download {matrix.get('name', 'unknown')}: {e}"
                    )
                    return None

        # Execute downloads
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            main_task = progress.add_task("Overall progress", total=len(matrices))

            tasks = [download_with_semaphore(matrix) for matrix in matrices]

            for i, coro in enumerate(asyncio.as_completed(tasks)):
                result = await coro
                if result:
                    downloaded_paths.append(result)
                progress.update(main_task, completed=i + 1)

        self.console.print(f"Successfully downloaded {len(downloaded_paths)} matrices")
        return downloaded_paths

    def list_matrices(
        self,
        filter_obj: Filter | None = None,
        limit: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """List matrices matching filter criteria (synchronous version).

        Args:
            filter_obj: Filter criteria
            limit: Maximum number of results

        Returns:
            Tuple of (limited results, total count) where:
            - limited results: List of matrix metadata (up to limit)
            - total count: Total number of matching matrices
        """
        try:
            # Check if we're already in an event loop
            asyncio.get_running_loop()
            # If we're in a loop, we can't use asyncio.run
            import warnings

            warnings.warn(
                "list_matrices() called from within an async context. "
                "Consider using find_matrices() directly instead.",
                RuntimeWarning,
                stacklevel=2,
            )
            # Return empty list to avoid blocking
            return [], 0
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self._list_matrices_async(filter_obj, limit))

    async def _list_matrices_async(
        self,
        filter_obj: Filter | None = None,
        limit: int | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Async version of list_matrices."""
        matrices = await self.find_matrices(filter_obj)
        total_count = len(matrices)

        if limit is not None:
            matrices = matrices[:limit]

        return matrices, total_count
