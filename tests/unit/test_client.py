"""Tests for client module."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ssdownload.client import SuiteSparseDownloader
from ssdownload.exceptions import MatrixNotFoundError
from ssdownload.filters import Filter


@pytest.fixture
def sample_csv_content():
    """Sample CSV content from SuiteSparse."""
    return """2
2023-12-01
Boeing,ct20stif,52329,52329,1566095,1,0,0,1,0.5,1.0,structural problem,2698463
HB,bcsstk01,48,48,224,1,0,0,1,1.0,1.0,structural problem,224"""


@pytest.fixture
def sample_matrices():
    """Sample parsed matrix data."""
    return [
        {
            "group": "Boeing",
            "name": "ct20stif",
            "rows": 52329,
            "cols": 52329,
            "nnz": 1566095,
            "real": True,
            "binary": False,
            "complex": False,
            "2d_3d": False,
            "symmetric": True,
            "spd": True,
            "kind": "structural problem",
            "pattern_entries": 2698463,
            "num_rows": 52329,
            "num_cols": 52329,
            "nonzeros": 1566095,
            "field": "real",
            "structure": "symmetric",
            "posdef": True,
        },
        {
            "group": "HB",
            "name": "bcsstk01",
            "rows": 48,
            "cols": 48,
            "nnz": 224,
            "real": True,
            "binary": False,
            "complex": False,
            "2d_3d": False,
            "symmetric": True,
            "spd": True,
            "kind": "structural problem",
            "pattern_entries": 224,
            "num_rows": 48,
            "num_cols": 48,
            "nonzeros": 224,
            "field": "real",
            "structure": "symmetric",
            "posdef": True,
        },
    ]


@pytest.fixture
def temp_cache_dir():
    """Temporary cache directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestSuiteSparseDownloader:
    """Test SuiteSparseDownloader functionality."""

    def test_init_default_cache_dir(self):
        """Test initialization with default cache directory."""
        downloader = SuiteSparseDownloader()

        # Should default to current working directory
        expected_path = Path.cwd()
        assert downloader.cache_dir == expected_path
        assert downloader.workers == 4
        assert downloader.timeout == 30.0
        assert downloader.verify_checksums is False
        assert downloader.index_manager is not None
        assert downloader.file_downloader is not None

    def test_init_custom_settings(self, temp_cache_dir):
        """Test initialization with custom settings."""
        downloader = SuiteSparseDownloader(
            cache_dir=temp_cache_dir, workers=2, timeout=60.0, verify_checksums=False
        )

        assert downloader.cache_dir == temp_cache_dir
        assert downloader.workers == 2
        assert downloader.timeout == 60.0
        assert downloader.verify_checksums is False

    @patch("ssdownload.client.IndexManager")
    async def test_find_matrices_with_filter(self, mock_index_manager, sample_matrices):
        """Test finding matrices with filter."""
        # Mock index manager
        mock_instance = mock_index_manager.return_value
        mock_instance.get_index = AsyncMock(return_value=sample_matrices)

        downloader = SuiteSparseDownloader()
        filter_obj = Filter(group="Boeing")

        matrices = await downloader.find_matrices(filter_obj)

        # Should return only Boeing matrices
        assert len(matrices) == 1
        assert matrices[0]["group"] == "Boeing"

    @patch("ssdownload.client.IndexManager")
    async def test_find_matrices_no_filter(self, mock_index_manager, sample_matrices):
        """Test finding matrices without filter."""
        mock_instance = mock_index_manager.return_value
        mock_instance.get_index = AsyncMock(return_value=sample_matrices)

        downloader = SuiteSparseDownloader()

        matrices = await downloader.find_matrices(None)

        # Should return all matrices
        assert len(matrices) == 2

    @patch("ssdownload.client.IndexManager")
    async def test_download_by_name_success(self, mock_index_manager, temp_cache_dir):
        """Test downloading matrix by name."""
        mock_instance = mock_index_manager.return_value
        mock_instance.find_matrix_group = AsyncMock(return_value="Boeing")

        downloader = SuiteSparseDownloader(cache_dir=temp_cache_dir)

        # Mock the download method
        with patch.object(
            downloader, "download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.return_value = Path("/fake/path")

            result = await downloader.download_by_name("ct20stif")

            mock_download.assert_called_once_with("Boeing", "ct20stif", "mat", None)
            assert result == Path("/fake/path")

    @patch("ssdownload.client.IndexManager")
    async def test_download_by_name_not_found(self, mock_index_manager):
        """Test downloading matrix by name when not found."""
        mock_instance = mock_index_manager.return_value
        mock_instance.find_matrix_group = AsyncMock(return_value=None)

        downloader = SuiteSparseDownloader()

        with pytest.raises(
            MatrixNotFoundError, match="Could not find matrix 'unknown'"
        ):
            await downloader.download_by_name("unknown")

    @patch("ssdownload.client.IndexManager")
    def test_list_matrices_sync(self, mock_index_manager, sample_matrices):
        """Test synchronous matrix listing."""
        downloader = SuiteSparseDownloader()

        # Mock the async method
        with patch.object(
            downloader, "_list_matrices_async", new_callable=AsyncMock
        ) as mock_async:
            mock_async.return_value = sample_matrices[:1]  # Return first matrix only

            matrices = downloader.list_matrices(Filter(group="Boeing"), limit=1)

            assert len(matrices) == 1
            assert matrices[0]["group"] == "Boeing"
            mock_async.assert_called_once_with(Filter(group="Boeing"), 1)

    @patch("ssdownload.client.IndexManager")
    @patch("ssdownload.client.FileDownloader")
    async def test_download_success(
        self, mock_file_downloader, mock_index_manager, temp_cache_dir
    ):
        """Test successful matrix download."""
        # Mock file downloader
        mock_downloader_instance = mock_file_downloader.return_value
        mock_downloader_instance.get_checksum = AsyncMock(return_value="abc123")
        expected_path = temp_cache_dir / "Boeing" / "ct20stif.mat"
        mock_downloader_instance.download_file = AsyncMock(return_value=expected_path)

        downloader = SuiteSparseDownloader(cache_dir=temp_cache_dir)

        result = await downloader.download("Boeing", "ct20stif")

        assert result == expected_path

        # Verify file downloader was called correctly
        mock_downloader_instance.download_file.assert_called_once()
        call_args = mock_downloader_instance.download_file.call_args
        assert "Boeing/ct20stif.mat" in call_args[0][0]  # URL
        assert call_args[0][1] == expected_path  # Output path

    @patch("ssdownload.client.IndexManager")
    async def test_bulk_download(self, mock_index_manager, temp_cache_dir):
        """Test bulk download functionality."""
        sample_matrices = [
            {"group": "Boeing", "name": "ct20stif"},
            {"group": "HB", "name": "bcsstk01"},
        ]

        mock_instance = mock_index_manager.return_value
        mock_instance.get_index = AsyncMock(return_value=sample_matrices)

        downloader = SuiteSparseDownloader(cache_dir=temp_cache_dir)

        # Mock the download method
        with patch.object(
            downloader, "download", new_callable=AsyncMock
        ) as mock_download:
            mock_download.side_effect = [
                Path(temp_cache_dir / "Boeing" / "ct20stif.mat"),
                Path(temp_cache_dir / "HB" / "bcsstk01.mat"),
            ]

            result = await downloader.bulk_download(max_files=2)

            assert len(result) == 2
            assert mock_download.call_count == 2

    @patch("ssdownload.client.IndexManager")
    async def test_get_available_groups(self, mock_index_manager):
        """Test getting available groups."""
        mock_instance = mock_index_manager.return_value
        mock_instance.get_groups = AsyncMock(return_value={"Boeing", "HB", "SNAP"})

        downloader = SuiteSparseDownloader()
        groups = await downloader._get_available_groups()

        assert len(groups) == 3
        assert "Boeing" in groups
        assert "HB" in groups
        assert "SNAP" in groups
