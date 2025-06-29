"""Tests for exceptions module."""

import pytest

from ssdownload.exceptions import (
    ChecksumError,
    DownloadError,
    IndexError,
    MatrixNotFoundError,
    NetworkError,
    SSDownloadError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_ssdownload_error_base(self):
        """Test base SSDownloadError."""
        error = SSDownloadError("Base error")
        assert str(error) == "Base error"
        assert isinstance(error, Exception)

    def test_checksum_error_inheritance(self):
        """Test ChecksumError inheritance."""
        error = ChecksumError("Checksum mismatch")
        assert str(error) == "Checksum mismatch"
        assert isinstance(error, SSDownloadError)
        assert isinstance(error, Exception)

    def test_matrix_not_found_error_inheritance(self):
        """Test MatrixNotFoundError inheritance."""
        error = MatrixNotFoundError("Matrix not found")
        assert str(error) == "Matrix not found"
        assert isinstance(error, SSDownloadError)
        assert isinstance(error, Exception)

    def test_index_error_inheritance(self):
        """Test IndexError inheritance."""
        error = IndexError("Index error")
        assert str(error) == "Index error"
        assert isinstance(error, SSDownloadError)
        assert isinstance(error, Exception)

    def test_download_error_inheritance(self):
        """Test DownloadError inheritance."""
        error = DownloadError("Download failed")
        assert str(error) == "Download failed"
        assert isinstance(error, SSDownloadError)
        assert isinstance(error, Exception)

    def test_network_error_inheritance(self):
        """Test NetworkError inheritance."""
        error = NetworkError("Network failure")
        assert str(error) == "Network failure"
        assert isinstance(error, SSDownloadError)
        assert isinstance(error, Exception)

    def test_exceptions_can_be_raised(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(ChecksumError):
            raise ChecksumError("Test checksum error")

        with pytest.raises(MatrixNotFoundError):
            raise MatrixNotFoundError("Test matrix not found")

        with pytest.raises(IndexError):
            raise IndexError("Test index error")

        with pytest.raises(DownloadError):
            raise DownloadError("Test download error")

        with pytest.raises(NetworkError):
            raise NetworkError("Test network error")

    def test_base_exception_catches_all(self):
        """Test that base exception catches all derived exceptions."""
        with pytest.raises(SSDownloadError):
            raise ChecksumError("Test error")

        with pytest.raises(SSDownloadError):
            raise MatrixNotFoundError("Test error")

        with pytest.raises(SSDownloadError):
            raise IndexError("Test error")

        with pytest.raises(SSDownloadError):
            raise DownloadError("Test error")

        with pytest.raises(SSDownloadError):
            raise NetworkError("Test error")
