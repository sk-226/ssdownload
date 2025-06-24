"""SuiteSparse Matrix Collection Downloader."""

from .client import SuiteSparseDownloader
from .exceptions import (
    ChecksumError,
    DownloadError,
    IndexError,
    MatrixNotFoundError,
    NetworkError,
    SSDownloadError,
)
from .filters import Filter

__all__ = [
    "SuiteSparseDownloader",
    "Filter",
    "SSDownloadError",
    "ChecksumError",
    "MatrixNotFoundError",
    "IndexError",
    "DownloadError",
    "NetworkError",
]
__version__ = "0.1.0"
