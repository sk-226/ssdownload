"""Tests for config module."""

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
        assert (
            Config.CSV_INDEX_URL
            == "http://sparse-files.engr.tamu.edu/files/ssstats.csv"
        )
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
