"""File downloader for SuiteSparse matrices.

This module provides the FileDownloader class that handles downloading matrix
files from the SuiteSparse Matrix Collection with advanced features:

- Resume support for interrupted downloads using HTTP Range requests
- MD5 checksum verification for data integrity
- Progress tracking integration with Rich progress bars
- Configurable timeout and retry behavior
- Efficient streaming downloads with chunked reading
- Automatic extraction of tar.gz archives for MM/RB formats
- Secure archive validation to prevent path traversal attacks

Example:
    >>> from ssdownload.downloader import FileDownloader
    >>> from pathlib import Path
    >>>
    >>> downloader = FileDownloader(verify_checksums=True, extract_archives=True)
    >>> success = await downloader.download_file(
    ...     "https://example.com/matrix.tar.gz",
    ...     Path("./matrix.tar.gz"),
    ...     expected_md5="abc123def456",
    ...     format_type="mm"
    ... )

The downloader creates temporary .part files during download and only moves
them to the final location after successful completion and verification.
For compressed formats (MM/RB), archives are automatically extracted.
"""

import hashlib
import tarfile
from pathlib import Path

import httpx
from rich.progress import Progress, TaskID

from .config import Config
from .exceptions import ChecksumError, DownloadError


class FileDownloader:
    """Handles file downloading with resume support and checksum verification."""

    def __init__(
        self,
        verify_checksums: bool = True,
        timeout: float | None = None,
        extract_archives: bool = True,
        keep_archives: bool = False,
    ):
        """Initialize the file downloader.

        Args:
            verify_checksums: Whether to verify file checksums after download
            timeout: HTTP request timeout in seconds
            extract_archives: Whether to automatically extract tar.gz files
            keep_archives: Whether to keep original tar.gz files after extraction
        """
        self.verify_checksums = verify_checksums
        self.timeout = timeout or Config.DEFAULT_TIMEOUT
        self.extract_archives = extract_archives
        self.keep_archives = keep_archives

    async def download_file(
        self,
        url: str,
        output_path: Path,
        expected_md5: str | None = None,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
        format_type: str = "mat",
    ) -> Path:
        """Download a single file with resume support and optional extraction.

        Args:
            url: URL to download
            output_path: Path to save file
            expected_md5: Expected MD5 checksum
            progress: Rich progress instance
            task_id: Progress task ID
            format_type: File format ("mat", "mm", "rb")

        Returns:
            Path to the final file (extracted file if archive was extracted)
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
                    # For compressed formats, check if extraction is needed
                    if format_type in ["mm", "rb"] and self.extract_archives:
                        return await self._handle_extraction(
                            output_path, format_type, progress, task_id
                        )
                    return output_path
                # If checksum verification fails, we'll re-download
            else:
                # No checksum available, but file exists - assume it's valid
                if progress and task_id:
                    progress.update(
                        task_id,
                        completed=100,
                        description=f"✓ {output_path.name} (existing)",
                    )
                # For compressed formats, check if extraction is needed
                if format_type in ["mm", "rb"] and self.extract_archives:
                    return await self._handle_extraction(
                        output_path, format_type, progress, task_id
                    )
                return output_path

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

        # Handle extraction for compressed formats
        if format_type in ["mm", "rb"] and self.extract_archives:
            return await self._handle_extraction(
                output_path, format_type, progress, task_id
            )

        return output_path

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

        try:
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
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
            from .exceptions import DownloadError

            raise DownloadError(f"Network error during download: {e}") from e
        except OSError as e:
            from .exceptions import DownloadError

            raise DownloadError(f"File system error during download: {e}") from e
        except Exception as e:
            from .exceptions import DownloadError

            raise DownloadError(f"Unexpected error during download: {e}") from e

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

    async def _handle_extraction(
        self,
        archive_path: Path,
        format_type: str,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> Path:
        """Handle archive extraction for compressed formats.

        Args:
            archive_path: Path to the archive file
            format_type: File format ("mm", "rb")
            progress: Rich progress instance
            task_id: Progress task ID

        Returns:
            Path to the extracted main file
        """
        if progress and task_id:
            progress.update(task_id, description=f"📂 Extracting {archive_path.name}")

        try:
            extracted_path = await self._extract_archive(archive_path)

            # Handle archive cleanup based on keep_archives setting
            if not self.keep_archives:
                if progress and task_id:
                    progress.update(
                        task_id, description=f"🗑️  Removing archive {archive_path.name}"
                    )
                archive_path.unlink()
            else:
                if progress and task_id:
                    progress.update(
                        task_id, description=f"💾 Keeping archive {archive_path.name}"
                    )

            if progress and task_id:
                progress.update(
                    task_id, description=f"✅ Extracted {extracted_path.name}"
                )

            return extracted_path

        except Exception as e:
            raise DownloadError(f"Failed to extract {archive_path.name}: {e}") from e

    async def _extract_archive(self, archive_path: Path) -> Path:
        """Extract tar.gz archive and return path to the main file.

        Args:
            archive_path: Path to the tar.gz archive

        Returns:
            Path to the extracted main file
        """
        extract_dir = archive_path.parent
        temp_files = []

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                # Security validation: prevent path traversal attacks
                self._validate_tar_members(tar)

                # Record files that will be extracted for cleanup on error
                temp_files = [
                    extract_dir / member.name
                    for member in tar.getmembers()
                    if member.isfile()
                ]

                # Extract all files
                tar.extractall(path=extract_dir)

                # Find extracted files that actually exist
                extracted_files = [f for f in temp_files if f.exists() and f.is_file()]

                if not extracted_files:
                    raise DownloadError("No files were extracted from archive")

                # Find the main matrix file
                main_file = self._find_main_file(extracted_files)
                return main_file

        except Exception as e:
            # Cleanup partially extracted files on error
            for temp_file in temp_files:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass  # Ignore cleanup failures

            if isinstance(e, DownloadError):
                raise
            raise DownloadError(f"Archive extraction failed: {e}") from e

    def _validate_tar_members(self, tar: tarfile.TarFile) -> None:
        """Validate tar members for security (prevent path traversal).

        Args:
            tar: TarFile object to validate

        Raises:
            DownloadError: If unsafe tar members are found
        """
        for member in tar.getmembers():
            # Check for absolute paths
            if member.name.startswith("/"):
                raise DownloadError(
                    f"Unsafe tar member with absolute path: {member.name}"
                )

            # Check for parent directory references
            if ".." in member.name:
                raise DownloadError(
                    f"Unsafe tar member with parent reference: {member.name}"
                )

            # Check for excessively long paths
            if len(member.name) > 255:
                raise DownloadError(f"Tar member name too long: {member.name}")

    def _find_main_file(self, extracted_files: list[Path]) -> Path:
        """Find the main matrix file from extracted files.

        Args:
            extracted_files: List of extracted file paths

        Returns:
            Path to the main matrix file
        """
        # Priority order for file selection
        patterns = [
            "*.mtx",  # Matrix Market format
            "*.rua",  # Rutherford Boeing format
            "*.rb",  # Rutherford Boeing format alternative
            "*",  # Any other file
        ]

        for pattern in patterns:
            matches = [f for f in extracted_files if f.match(pattern)]
            if matches:
                # If multiple matches, return the largest file
                return max(matches, key=lambda f: f.stat().st_size)

        # Fallback: return the largest file
        if extracted_files:
            return max(extracted_files, key=lambda f: f.stat().st_size)

        raise DownloadError("No suitable main file found in extracted archive")
