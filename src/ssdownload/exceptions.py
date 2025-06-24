"""Custom exceptions for SuiteSparse downloader."""


class SSDownloadError(Exception):
    """Base exception for SuiteSparse downloader."""

    pass


class ChecksumError(SSDownloadError):
    """Raised when file checksum doesn't match expected value."""

    pass


class MatrixNotFoundError(SSDownloadError):
    """Raised when matrix is not found in the collection."""

    pass


class IndexError(SSDownloadError):
    """Raised when there's an error with the matrix index."""

    pass


class DownloadError(SSDownloadError):
    """Raised when download fails."""

    pass


class NetworkError(SSDownloadError):
    """Raised when network operation fails."""

    pass
