"""Tests for downloader module."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ssdownload.config import Config
from ssdownload.downloader import FileDownloader
from ssdownload.exceptions import ChecksumError


@pytest.fixture
def temp_dir():
    """Temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestFileDownloader:
    """Test FileDownloader functionality."""

    def test_init_default(self):
        """Test FileDownloader initialization with defaults."""
        downloader = FileDownloader()

        assert downloader.verify_checksums is True
        assert downloader.timeout == Config.DEFAULT_TIMEOUT

    def test_init_custom(self):
        """Test FileDownloader initialization with custom settings."""
        downloader = FileDownloader(verify_checksums=False, timeout=60.0)

        assert downloader.verify_checksums is False
        assert downloader.timeout == 60.0

    async def test_verify_file_checksum_success(self, temp_dir):
        """Test successful file checksum verification."""
        downloader = FileDownloader()

        # Create test file
        test_file = temp_dir / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)

        # Calculate expected MD5
        expected_md5 = hashlib.md5(content).hexdigest()

        result = await downloader._verify_file_checksum(test_file, expected_md5)
        assert result is True

    async def test_verify_file_checksum_mismatch(self, temp_dir):
        """Test file checksum verification with mismatch."""
        downloader = FileDownloader()

        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_bytes(b"test content")

        result = await downloader._verify_file_checksum(test_file, "wrong_checksum")
        assert result is False

    async def test_verify_file_checksum_missing_file(self, temp_dir):
        """Test file checksum verification with missing file."""
        downloader = FileDownloader()

        missing_file = temp_dir / "missing.txt"

        result = await downloader._verify_file_checksum(missing_file, "any_checksum")
        assert result is False

    @patch("httpx.AsyncClient")
    async def test_get_checksum_success(self, mock_client):
        """Test getting checksum from server."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "abc123def456  ct20stif.mat"

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client.return_value = mock_client_instance

        downloader = FileDownloader()

        result = await downloader.get_checksum("Boeing", "ct20stif", "mat")

        assert result == "abc123def456"
        expected_url = Config.get_checksum_url("Boeing", "ct20stif", "mat")
        mock_client_instance.get.assert_called_once_with(expected_url)

    @patch("httpx.AsyncClient")
    async def test_get_checksum_not_found(self, mock_client):
        """Test getting checksum when not available."""
        # Mock HTTP response with 404
        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client.return_value = mock_client_instance

        downloader = FileDownloader()

        result = await downloader.get_checksum("Boeing", "ct20stif", "mat")

        assert result is None

    @patch("httpx.AsyncClient")
    async def test_get_checksum_exception(self, mock_client):
        """Test getting checksum with exception."""
        # Mock HTTP client to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client.return_value = mock_client_instance

        downloader = FileDownloader()

        result = await downloader.get_checksum("Boeing", "ct20stif", "mat")

        assert result is None

    @patch.object(FileDownloader, "_download_with_resume")
    async def test_download_with_resume_new_file(self, mock_download, temp_dir):
        """Test downloading a new file."""
        content = b"test matrix data"
        downloader = FileDownloader()
        temp_file = temp_dir / "test.part"

        # Create the file that would be created by the download
        async def mock_download_side_effect(url, path):
            path.write_bytes(content)

        mock_download.side_effect = mock_download_side_effect

        await downloader._download_with_resume("http://example.com/file", temp_file)

        assert temp_file.exists()
        assert temp_file.read_bytes() == content

    @patch.object(FileDownloader, "_download_with_resume")
    async def test_download_with_resume_existing_file(self, mock_download, temp_dir):
        """Test downloading with resume from existing partial file."""
        initial_content = b"test"
        additional_content = b" matrix data"

        # Create partial file
        temp_file = temp_dir / "test.part"
        temp_file.write_bytes(initial_content)

        downloader = FileDownloader()

        # Mock download to append additional content
        async def mock_download_side_effect(url, path):
            existing_content = path.read_bytes() if path.exists() else b""
            path.write_bytes(existing_content + additional_content)

        mock_download.side_effect = mock_download_side_effect

        await downloader._download_with_resume("http://example.com/file", temp_file)

        assert temp_file.exists()
        assert temp_file.read_bytes() == initial_content + additional_content

    async def test_download_file_existing_valid(self, temp_dir):
        """Test download_file when file already exists and is valid."""
        downloader = FileDownloader()

        # Create existing file
        output_path = temp_dir / "test.mat"
        content = b"test content"
        output_path.write_bytes(content)

        # Calculate expected MD5
        expected_md5 = hashlib.md5(content).hexdigest()

        result = await downloader.download_file(
            "http://example.com/file", output_path, expected_md5
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == content

    @patch.object(FileDownloader, "_download_with_resume")
    @patch.object(FileDownloader, "_verify_file_checksum")
    async def test_download_file_checksum_mismatch(
        self, mock_verify, mock_download, temp_dir
    ):
        """Test download_file with checksum mismatch."""
        downloader = FileDownloader()

        output_path = temp_dir / "test.mat"
        temp_path = output_path.with_suffix(output_path.suffix + ".part")

        # Mock download and verification
        mock_download.return_value = None
        mock_verify.return_value = False

        # Create temp file to be deleted
        temp_path.write_bytes(b"invalid content")

        with pytest.raises(ChecksumError, match="Checksum mismatch"):
            await downloader.download_file(
                "http://example.com/file", output_path, "expected_checksum"
            )

        # Verify temp file was deleted
        assert not temp_path.exists()

    @patch.object(FileDownloader, "_download_with_resume")
    @patch.object(FileDownloader, "_verify_file_checksum")
    async def test_download_file_success_with_checksum(
        self, mock_verify, mock_download, temp_dir
    ):
        """Test successful download_file with checksum verification."""
        downloader = FileDownloader()

        output_path = temp_dir / "test.mat"
        temp_path = output_path.with_suffix(output_path.suffix + ".part")

        # Mock download and verification
        mock_download.return_value = None
        mock_verify.return_value = True

        # Create temp file
        content = b"test content"
        temp_path.write_bytes(content)

        result = await downloader.download_file(
            "http://example.com/file", output_path, "valid_checksum"
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == content
        assert not temp_path.exists()  # Temp file should be moved

    @patch.object(FileDownloader, "_download_with_resume")
    async def test_download_file_no_checksum_verification(
        self, mock_download, temp_dir
    ):
        """Test download_file without checksum verification."""
        downloader = FileDownloader(verify_checksums=False)

        output_path = temp_dir / "test.mat"
        temp_path = output_path.with_suffix(output_path.suffix + ".part")

        # Mock download
        mock_download.return_value = None

        # Create temp file
        content = b"test content"
        temp_path.write_bytes(content)

        result = await downloader.download_file(
            "http://example.com/file",
            output_path,
            "any_checksum",  # Should be ignored
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == content
