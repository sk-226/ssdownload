"""File downloader for SuiteSparse matrices.

This module provides the FileDownloader class that handles downloading matrix
files from the SuiteSparse Matrix Collection with advanced features:

- Resume support for interrupted downloads using HTTP Range requests
- MD5 checksum verification for data integrity
- Progress tracking integration with Rich progress bars
- Configurable timeout and retry behavior
- Efficient streaming downloads with chunked reading

Example:
    >>> from ssdownload.downloader import FileDownloader
    >>> from pathlib import Path
    >>>
    >>> downloader = FileDownloader(verify_checksums=True)
    >>> success = await downloader.download_file(
    ...     "https://example.com/matrix.mat",
    ...     Path("./matrix.mat"),
    ...     expected_md5="abc123def456"
    ... )

The downloader creates temporary .part files during download and only moves
them to the final location after successful completion and verification.
"""

import hashlib
from pathlib import Path

import httpx
from rich.progress import Progress, TaskID

from .config import Config
from .exceptions import ChecksumError


class FileDownloader:
    """Handles file downloading with resume support and checksum verification."""

    def __init__(self, verify_checksums: bool = True, timeout: float = None):
        """Initialize the file downloader.

        Args:
            verify_checksums: Whether to verify file checksums after download
            timeout: HTTP request timeout in seconds
        """
        self.verify_checksums = verify_checksums
        self.timeout = timeout or Config.DEFAULT_TIMEOUT

    async def download_file(
        self,
        url: str,
        output_path: Path,
        expected_md5: str | None = None,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> bool:
        """Download a single file with resume support.

        Args:
            url: URL to download
            output_path: Path to save file
            expected_md5: Expected MD5 checksum
            progress: Rich progress instance
            task_id: Progress task ID

        Returns:
            True if download successful
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = output_path.with_suffix(output_path.suffix + ".part")

        # Check if file already exists and is valid
        if output_path.exists():
            # If we have a checksum, verify it
            if expected_md5:
                if await self._verify_file_checksum(output_path, expected_md5):
                    if progress and task_id:
                        progress.update(
                            task_id, completed=100, description=f"✓ {output_path.name}"
                        )
                    return True
                # If checksum verification fails, we'll re-download
            else:
                # No checksum available, but file exists - assume it's valid
                if progress and task_id:
                    progress.update(
                        task_id,
                        completed=100,
                        description=f"✓ {output_path.name} (existing)",
                    )
                return True

        # Clean up any orphaned .part files from previous failed downloads
        # Only clean up old, likely stale files to prevent interference with tests
        if temp_path.exists():
            import time

            temp_stat = temp_path.stat()
            temp_age = time.time() - temp_stat.st_mtime
            # Remove only if file is older than 1 hour (not affecting test files)
            if temp_age > 3600:
                temp_path.unlink(missing_ok=True)

        # Download the file
        await self._download_with_resume(url, temp_path, progress, task_id)

        # Verify checksum if provided
        if expected_md5 and self.verify_checksums:
            if not await self._verify_file_checksum(temp_path, expected_md5):
                temp_path.unlink(missing_ok=True)
                raise ChecksumError(f"Checksum mismatch for {output_path.name}")

        # Move temp file to final location
        temp_path.rename(output_path)

        if progress and task_id:
            progress.update(task_id, description=f"✓ {output_path.name}")

        return True

    async def _download_with_resume(
        self,
        url: str,
        temp_path: Path,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> None:
        """Download file with resume support."""
        # Determine resume position
        resume_pos = 0
        if temp_path.exists():
            resume_pos = temp_path.stat().st_size

        headers = {}
        if resume_pos > 0:
            headers["Range"] = f"bytes={resume_pos}-"

        async with httpx.AsyncClient(
            **Config.get_http_client_config(self.timeout)
        ) as client:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                # Get total size for progress tracking
                total_size = None
                if "content-length" in response.headers:
                    content_length = int(response.headers["content-length"])
                    total_size = content_length + resume_pos

                if progress and task_id and total_size:
                    progress.update(task_id, total=total_size, completed=resume_pos)

                # Download with resume
                mode = "ab" if resume_pos > 0 else "wb"
                with open(temp_path, mode) as f:
                    downloaded = resume_pos
                    async for chunk in response.aiter_bytes(
                        chunk_size=Config.CHUNK_SIZE
                    ):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress and task_id:
                            progress.update(task_id, completed=downloaded)

    async def _verify_file_checksum(self, file_path: Path, expected_md5: str) -> bool:
        """Verify file MD5 checksum.

        Args:
            file_path: Path to file to verify
            expected_md5: Expected MD5 hash

        Returns:
            True if checksum matches
        """
        if not file_path.exists():
            return False

        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(Config.CHUNK_SIZE), b""):
                hasher.update(chunk)

        return hasher.hexdigest().lower() == expected_md5.lower()

    async def get_checksum(
        self, group: str, name: str, format_type: str = "mat"
    ) -> str | None:
        """Get MD5 checksum for a matrix file.

        Args:
            group: Matrix group name
            name: Matrix name
            format_type: File format

        Returns:
            MD5 checksum if available, None otherwise
        """
        try:
            checksum_url = Config.get_checksum_url(group, name, format_type)
            async with httpx.AsyncClient(
                **Config.get_http_client_config(self.timeout)
            ) as client:
                response = await client.get(checksum_url)
                if response.status_code == 200:
                    return response.text.strip().split()[0]
        except Exception:
            pass  # Checksum not available

        return None
