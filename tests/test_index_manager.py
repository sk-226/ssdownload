"""Tests for index_manager module."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ssdownload.config import Config
from ssdownload.index_manager import IndexManager


@pytest.fixture
def temp_cache_dir():
    """Temporary cache directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_csv_content():
    """Sample CSV content from SuiteSparse."""
    return """2
2023-12-01
Boeing,ct20stif,52329,52329,1566095,1,0,0,1,0.5,1.0,structural problem,2698463
HB,bcsstk01,48,48,224,1,0,0,1,1.0,1.0,structural problem,224"""


@pytest.fixture
def expected_parsed_data():
    """Expected parsed matrix data."""
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


class TestIndexManager:
    """Test IndexManager functionality."""

    def test_init(self, temp_cache_dir):
        """Test IndexManager initialization."""
        manager = IndexManager(temp_cache_dir)

        assert manager.cache_dir == temp_cache_dir
        assert manager._csv_index_cache is None
        assert manager._csv_index_cache_time == 0
        assert manager._groups_cache is None

    def test_init_default_cache_dir(self):
        """Test IndexManager initialization with default cache directory."""
        manager = IndexManager()

        # Should use system default cache directory
        from ssdownload.config import Config

        expected_dir = Config.get_default_cache_dir()
        assert manager.cache_dir == expected_dir
        assert manager.cache_dir.exists()  # Should be created

    def test_parse_csv_content(
        self, temp_cache_dir, sample_csv_content, expected_parsed_data
    ):
        """Test CSV content parsing."""
        manager = IndexManager(temp_cache_dir)

        parsed = manager._parse_csv_content(sample_csv_content)

        assert len(parsed) == 2
        assert parsed[0]["group"] == "Boeing"
        assert parsed[0]["name"] == "ct20stif"
        assert parsed[0]["rows"] == 52329
        assert parsed[0]["field"] == "real"
        assert (
            parsed[0]["structure"] == "symmetric"
        )  # ct20stif has numerical_symmetry=1.0, so symmetric
        assert (
            parsed[1]["structure"] == "symmetric"
        )  # bcsstk01 has numerical_symmetry=1.0, so symmetric

    def test_parse_csv_line_valid(self, temp_cache_dir):
        """Test parsing a valid CSV line."""
        manager = IndexManager(temp_cache_dir)

        line = "Boeing,ct20stif,52329,52329,1566095,1,0,0,1,0.5,1.0,structural problem,2698463"
        result = manager._parse_csv_line(line)

        assert result is not None
        assert result["group"] == "Boeing"
        assert result["name"] == "ct20stif"
        assert result["rows"] == 52329
        assert result["real"] is True
        assert result["posdef"] is True
        assert (
            result["spd"] is True
        )  # symmetric (numerical_symmetry=1.0) AND posdef AND real AND square
        assert result["field"] == "real"

    def test_parse_csv_line_invalid(self, temp_cache_dir):
        """Test parsing an invalid CSV line."""
        manager = IndexManager(temp_cache_dir)

        # Too few columns
        line = "Boeing,ct20stif,52329"
        result = manager._parse_csv_line(line)
        assert result is None

        # Invalid integer
        line = "Boeing,ct20stif,invalid,52329,1566095,1,0,0,1,1,0,,1566095"
        result = manager._parse_csv_line(line)
        assert result is None

    def test_get_field_type(self, temp_cache_dir):
        """Test field type determination."""
        manager = IndexManager(temp_cache_dir)

        # Real field
        matrix_info = {"real": True, "binary": False}
        assert manager._get_field_type(matrix_info) == "real"

        # Binary field
        matrix_info = {"real": False, "binary": True}
        assert manager._get_field_type(matrix_info) == "binary"

        # Complex field
        matrix_info = {"real": False, "binary": False}
        assert manager._get_field_type(matrix_info) == "complex"

    @patch("httpx.AsyncClient")
    async def test_fetch_csv_index(
        self, mock_client, temp_cache_dir, sample_csv_content
    ):
        """Test fetching CSV index from remote."""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.text = sample_csv_content
        mock_response.raise_for_status = AsyncMock()

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client.return_value = mock_client_instance

        manager = IndexManager(temp_cache_dir)
        result = await manager._fetch_csv_index()

        assert len(result) == 2
        assert result[0]["group"] == "Boeing"
        mock_client_instance.get.assert_called_once_with(Config.CSV_INDEX_URL)

    async def test_get_index_from_cache(self, temp_cache_dir, expected_parsed_data):
        """Test getting index from memory cache."""
        manager = IndexManager(temp_cache_dir)

        # Set up cache
        manager._csv_index_cache = expected_parsed_data
        manager._csv_index_cache_time = time.time()

        result = await manager.get_index()

        assert result == expected_parsed_data
        assert len(result) == 2

    async def test_get_index_from_disk_cache(
        self, temp_cache_dir, expected_parsed_data
    ):
        """Test getting index from disk cache."""
        manager = IndexManager(temp_cache_dir)

        # Create disk cache
        cache_file = temp_cache_dir / "ssstats_cache.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(expected_parsed_data, f)

        result = await manager.get_index()

        assert len(result) == 2
        assert result[0]["group"] == "Boeing"

    def test_save_index_to_disk(self, temp_cache_dir, expected_parsed_data):
        """Test saving index to disk cache."""
        manager = IndexManager(temp_cache_dir)
        cache_file = temp_cache_dir / "ssstats_cache.json"

        manager._save_index_to_disk(expected_parsed_data, cache_file)

        assert cache_file.exists()
        with open(cache_file, encoding="utf-8") as f:
            saved_data = json.load(f)

        assert len(saved_data) == 2
        assert saved_data[0]["group"] == "Boeing"

    @patch.object(IndexManager, "get_index")
    async def test_get_groups(
        self, mock_get_index, temp_cache_dir, expected_parsed_data
    ):
        """Test getting available groups."""
        mock_get_index.return_value = expected_parsed_data

        manager = IndexManager(temp_cache_dir)
        groups = await manager.get_groups()

        assert len(groups) == 2
        assert "Boeing" in groups
        assert "HB" in groups

    @patch.object(IndexManager, "get_index")
    async def test_get_groups_cached(self, mock_get_index, temp_cache_dir):
        """Test getting groups from cache."""
        manager = IndexManager(temp_cache_dir)
        manager._groups_cache = {"Boeing", "HB", "SNAP"}

        groups = await manager.get_groups()

        assert len(groups) == 3
        assert "SNAP" in groups
        # Should not call get_index since we have cached groups
        mock_get_index.assert_not_called()

    @patch.object(IndexManager, "get_index")
    async def test_find_matrix_info(
        self, mock_get_index, temp_cache_dir, expected_parsed_data
    ):
        """Test finding matrix info by name."""
        mock_get_index.return_value = expected_parsed_data

        manager = IndexManager(temp_cache_dir)

        # Found matrix
        result = await manager.find_matrix_info("ct20stif")
        assert result is not None
        assert result["group"] == "Boeing"
        assert result["name"] == "ct20stif"

        # Not found matrix
        result = await manager.find_matrix_info("nonexistent")
        assert result is None

    @patch.object(IndexManager, "find_matrix_info")
    async def test_find_matrix_group(self, mock_find_info, temp_cache_dir):
        """Test finding matrix group by name."""
        manager = IndexManager(temp_cache_dir)

        # Found matrix
        mock_find_info.return_value = {"group": "Boeing", "name": "ct20stif"}
        result = await manager.find_matrix_group("ct20stif")
        assert result == "Boeing"

        # Not found matrix
        mock_find_info.return_value = None
        result = await manager.find_matrix_group("nonexistent")
        assert result is None
