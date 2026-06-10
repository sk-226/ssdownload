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
from .page_scraper import PageScraper

__all__ = [
    "SuiteSparseDownloader",
    "Filter",
    "PageScraper",
    "SSDownloadError",
    "ChecksumError",
    "MatrixNotFoundError",
    "IndexError",
    "DownloadError",
    "NetworkError",
]
__version__ = "0.3.1"
