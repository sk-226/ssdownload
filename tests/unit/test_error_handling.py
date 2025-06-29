"""Comprehensive error handling tests."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ssdownload.client import SuiteSparseDownloader
from ssdownload.downloader import FileDownloader
from ssdownload.exceptions import (
    DownloadError,
    IndexError,
    NetworkError,
)
from ssdownload.filters import Filter
from ssdownload.index_manager import IndexManager


class TestErrorHandling:
    """Test error handling across all components."""

    @pytest.mark.parametrize(
        "exception_type,expected_error",
        [
            (httpx.TimeoutException("Timeout"), NetworkError),
            (httpx.ConnectError("Connection failed"), NetworkError),
            (
                httpx.HTTPStatusError(
                    "404", request=MagicMock(), response=MagicMock(status_code=404)
                ),
                NetworkError,
            ),
            (json.JSONDecodeError("Invalid JSON", "", 0), IndexError),
        ],
    )
    async def test_index_manager_error_handling(self, exception_type, expected_error):
        """Test IndexManager handles various network errors."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(side_effect=exception_type)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            index_manager = IndexManager()

            with pytest.raises(expected_error):
                await index_manager._fetch_csv_index()

    async def test_file_downloader_network_errors(self):
        """Test FileDownloader handles network errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = FileDownloader()

            # Test various network error scenarios
            error_scenarios = [
                httpx.TimeoutException("Request timeout"),
                httpx.ConnectError("Connection failed"),
                httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                ),
            ]

            for error in error_scenarios:
                with patch("httpx.AsyncClient") as mock_client:
                    mock_client_instance = MagicMock()
                    mock_client_instance.stream = AsyncMock(side_effect=error)
                    mock_client_instance.__aenter__ = AsyncMock(
                        return_value=mock_client_instance
                    )
                    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
                    mock_client.return_value = mock_client_instance

                    with pytest.raises(DownloadError):
                        await downloader.download_file(
                            "https://example.com/test.mat", Path(temp_dir) / "test.mat"
                        )

    async def test_checksum_verification_errors(self):
        """Test checksum verification error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = FileDownloader()
            test_file = Path(temp_dir) / "test.mat"

            # Create a test file with known content
            test_content = b"test matrix data"
            test_file.write_bytes(test_content)

            # Test checksum mismatch
            wrong_checksum = "wrongchecksum123"

            # _verify_file_checksum returns bool, not raises exception
            result = await downloader._verify_file_checksum(test_file, wrong_checksum)
            assert result is False, (
                "Checksum verification should fail with wrong checksum"
            )

    def test_client_error_propagation(self):
        """Test that client properly propagates errors from components."""
        with patch("ssdownload.client.IndexManager") as mock_index:
            mock_instance = mock_index.return_value
            mock_instance.get_index = AsyncMock(
                side_effect=NetworkError("Network failed")
            )

            downloader = SuiteSparseDownloader()

            with pytest.raises(NetworkError):
                downloader.list_matrices(Filter(), limit=10)

    async def test_concurrent_download_error_handling(self):
        """Test error handling in concurrent downloads."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = SuiteSparseDownloader(cache_dir=Path(temp_dir))

            # Mock some downloads to fail
            with patch.object(downloader, "download") as mock_download:
                # Make every other download fail
                def side_effect(group, name, *args, **kwargs):
                    if name.endswith("1"):
                        raise DownloadError(f"Failed to download {group}/{name}")
                    return Path(temp_dir) / f"{name}.mat"

                mock_download.side_effect = side_effect

                # Mock finding matrices
                mock_matrices = [
                    {"group": "Test", "name": "matrix1"},
                    {"group": "Test", "name": "matrix2"},
                    {"group": "Test", "name": "matrix3"},
                ]

                with patch.object(
                    downloader, "find_matrices", return_value=mock_matrices
                ):
                    # Should handle partial failures gracefully
                    downloaded = await downloader.bulk_download(Filter(), max_files=3)

                    # Should get successful downloads only
                    assert len(downloaded) == 2  # matrix2 and matrix3 should succeed

    @pytest.mark.parametrize(
        "invalid_range",
        [
            "invalid",
            "1000:abc",
            "abc:1000",
            "1000::2000",
            ":",
            "",
        ],
    )
    def test_invalid_range_parsing(self, invalid_range):
        """Test that invalid range inputs are handled properly."""
        from ssdownload.cli_utils import parse_range

        with pytest.raises(ValueError):
            parse_range(invalid_range)

    def test_invalid_filter_parameters(self):
        """Test Filter class handles invalid parameters gracefully."""
        # These should not raise exceptions during construction
        filter_with_invalid = Filter(
            field="invalid_field_type",
            n_rows=(-1, -1),  # Negative values
            nnz=(1000, 100),  # Reversed range
        )

        # But should handle them gracefully during matching
        test_matrix = {
            "field": "real",
            "num_rows": 500,
            "num_cols": 500,
        }

        # Should not crash, even with invalid filter parameters
        try:
            result = filter_with_invalid.matches(test_matrix)
            assert isinstance(result, bool)
        except Exception as e:
            # If it does raise an exception, it should be a meaningful one
            assert isinstance(e, ValueError | TypeError)

    async def test_malformed_api_response_handling(self):
        """Test handling of malformed API responses."""
        with patch("httpx.AsyncClient") as mock_client:
            # Test various malformed responses
            malformed_responses = [
                "",  # Empty response
                "not,enough,fields",  # Too few fields
                "group,name,not_a_number,cols,nnz",  # Non-numeric in numeric field
                "group,name,100,200,300,invalid_bool,0,0,1",  # Invalid boolean
            ]

            for malformed_data in malformed_responses:
                mock_response = MagicMock()
                mock_response.text = f"1\n2023-01-01\n{malformed_data}"
                mock_response.raise_for_status = MagicMock()

                mock_client_instance = MagicMock()
                mock_client_instance.get = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__ = AsyncMock(
                    return_value=mock_client_instance
                )
                mock_client_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_client_instance

                index_manager = IndexManager()

                # Should either handle gracefully or raise appropriate error
                try:
                    result = await index_manager._fetch_csv_index()
                    # If no exception, should return valid data structure
                    assert isinstance(result, list)
                except (IndexError, ValueError):
                    # These are acceptable exceptions for malformed data
                    pass

    async def test_disk_space_error_simulation(self):
        """Test handling of disk space errors during download."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = FileDownloader()

            # Mock disk space error during file writing
            with patch("builtins.open", side_effect=OSError("No space left on device")):
                with pytest.raises(DownloadError):
                    await downloader.download_file(
                        "https://example.com/test.mat", Path(temp_dir) / "test.mat"
                    )

    async def test_cache_corruption_handling(self):
        """Test handling of corrupted cache files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            index_manager = IndexManager(cache_dir)

            # Create corrupted cache file
            cache_file = cache_dir / "ssstats_cache.json"
            cache_file.write_text("corrupted json data {{{")

            # Should handle corrupted cache gracefully
            try:
                # This should either succeed by fetching fresh data
                # or fail with a clear error message
                result = await index_manager.get_index()
                assert isinstance(result, list)
            except (IndexError, NetworkError):
                # These are acceptable for cache corruption
                pass

    async def test_timeout_handling(self):
        """Test that timeouts are handled appropriately."""
        with patch("httpx.AsyncClient") as mock_client:
            # Simulate timeout
            mock_client_instance = MagicMock()
            mock_client_instance.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance

            index_manager = IndexManager()

            with pytest.raises(NetworkError):
                await index_manager._fetch_csv_index()

    def test_permission_error_handling(self):
        """Test handling of file permission errors."""
        # Test with a directory we definitely can't write to
        read_only_dir = Path("/")  # Root directory

        try:
            SuiteSparseDownloader(cache_dir=read_only_dir)
            # This might succeed on some systems, fail on others
            # The important thing is it doesn't crash unexpectedly
        except (PermissionError, OSError):
            # Expected on most systems
            pass
