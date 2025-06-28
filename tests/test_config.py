"""Tests for config module."""

import os
from pathlib import Path

import pytest

from ssdownload.config import Config


class TestConfig:
    """Test Config functionality."""

    def test_config_constants(self):
        """Test that config constants are properly defined."""
        assert Config.BASE_URL == "https://suitesparse-collection-website.herokuapp.com"
        assert (
            Config.FILES_BASE_URL
            == "https://suitesparse-collection-website.herokuapp.com"
        )
        assert Config.CSV_INDEX_URL == "https://sparse.tamu.edu/files/ssstats.csv"
        assert Config.CACHE_TTL == 3600
        assert Config.MAX_WORKERS == 8
        assert Config.DEFAULT_WORKERS == 4
        assert Config.DEFAULT_TIMEOUT == 30.0
        assert Config.CHUNK_SIZE == 8192
        assert Config.MAX_CONNECTIONS == 10
        assert Config.MAX_KEEPALIVE_CONNECTIONS == 5
        assert "ssdownload" in Config.USER_AGENT

    def test_get_http_client_config_default(self):
        """Test HTTP client config with default timeout."""
        config = Config.get_http_client_config()

        assert "timeout" in config
        assert "limits" in config
        assert "follow_redirects" in config
        assert "headers" in config

        assert config["follow_redirects"] is True
        assert config["headers"]["User-Agent"] == Config.USER_AGENT

    def test_get_http_client_config_custom_timeout(self):
        """Test HTTP client config with custom timeout."""
        config = Config.get_http_client_config(timeout=60.0)

        # Timeout should be an httpx.Timeout object, but we can't easily test the internal value
        assert "timeout" in config

    def test_get_file_extension_mat(self):
        """Test file extension for MAT format."""
        ext = Config.get_file_extension("mat")
        assert ext == ".mat"

    def test_get_file_extension_mm(self):
        """Test file extension for Matrix Market format."""
        ext = Config.get_file_extension("mm")
        assert ext == ".tar.gz"

    def test_get_file_extension_rb(self):
        """Test file extension for Rutherford-Boeing format."""
        ext = Config.get_file_extension("rb")
        assert ext == ".tar.gz"

    def test_get_file_extension_unknown(self):
        """Test file extension for unknown format defaults to MAT."""
        ext = Config.get_file_extension("unknown")
        assert ext == ".mat"

    def test_get_matrix_url_mat(self):
        """Test matrix URL generation for MAT format."""
        url = Config.get_matrix_url("Boeing", "ct20stif", "mat")
        expected = "https://suitesparse-collection-website.herokuapp.com/mat/Boeing/ct20stif.mat"
        assert url == expected

    def test_get_matrix_url_mm(self):
        """Test matrix URL generation for Matrix Market format."""
        url = Config.get_matrix_url("Boeing", "ct20stif", "mm")
        expected = "https://suitesparse-collection-website.herokuapp.com/MM/Boeing/ct20stif.tar.gz"
        assert url == expected

    def test_get_matrix_url_rb(self):
        """Test matrix URL generation for Rutherford-Boeing format."""
        url = Config.get_matrix_url("Boeing", "ct20stif", "rb")
        expected = "https://suitesparse-collection-website.herokuapp.com/RB/Boeing/ct20stif.tar.gz"
        assert url == expected

    def test_get_matrix_url_default_format(self):
        """Test matrix URL generation with default format."""
        url = Config.get_matrix_url("Boeing", "ct20stif")
        expected = "https://suitesparse-collection-website.herokuapp.com/mat/Boeing/ct20stif.mat"
        assert url == expected

    def test_get_matrix_url_invalid_format(self):
        """Test matrix URL generation with invalid format."""
        with pytest.raises(ValueError, match="Unsupported format: invalid"):
            Config.get_matrix_url("Boeing", "ct20stif", "invalid")

    def test_get_checksum_url_mat(self):
        """Test checksum URL generation for MAT format."""
        url = Config.get_checksum_url("Boeing", "ct20stif", "mat")
        expected = "https://suitesparse-collection-website.herokuapp.com/mat/Boeing/ct20stif.mat.md5"
        assert url == expected

    def test_get_checksum_url_mm(self):
        """Test checksum URL generation for Matrix Market format."""
        url = Config.get_checksum_url("Boeing", "ct20stif", "mm")
        expected = "https://suitesparse-collection-website.herokuapp.com/MM/Boeing/ct20stif.tar.gz.md5"
        assert url == expected

    def test_get_checksum_url_default_format(self):
        """Test checksum URL generation with default format."""
        url = Config.get_checksum_url("Boeing", "ct20stif")
        expected = "https://suitesparse-collection-website.herokuapp.com/mat/Boeing/ct20stif.mat.md5"
        assert url == expected

    def test_get_default_cache_dir(self):
        """Test default cache directory detection."""
        cache_dir = Config.get_default_cache_dir()

        # Should return a Path object
        assert isinstance(cache_dir, Path)

        # Should contain 'ssdownload' in the path
        assert "ssdownload" in str(cache_dir)

        # Should be an absolute path
        assert cache_dir.is_absolute()

    def test_get_default_cache_dir_with_env_override(self):
        """Test cache directory override via environment variable."""
        # Test with environment variable override
        test_cache_dir = "/tmp/test_ssdownload_cache"
        original_env = os.environ.get("SSDOWNLOAD_CACHE_DIR")

        try:
            os.environ["SSDOWNLOAD_CACHE_DIR"] = test_cache_dir
            cache_dir = Config.get_default_cache_dir()
            # Convert both to Path objects to handle cross-platform path separators
            assert Path(str(cache_dir)) == Path(test_cache_dir)
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ["SSDOWNLOAD_CACHE_DIR"] = original_env
            else:
                os.environ.pop("SSDOWNLOAD_CACHE_DIR", None)
