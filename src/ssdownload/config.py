"""Configuration constants and settings for SuiteSparse downloader.

This module provides centralized configuration management for the SuiteSparse
Matrix Collection downloader. It includes URL endpoints, HTTP client settings,
timeout configurations, and utility methods for generating download URLs.

Example:
    >>> from ssdownload.config import Config
    >>> url = Config.get_matrix_url("Boeing", "ct20stif", "mat")
    >>> client_config = Config.get_http_client_config(timeout=60.0)

Attributes:
    BASE_URL: Base URL for the SuiteSparse collection website
    FILES_BASE_URL: Base URL for matrix file downloads
    CSV_INDEX_URL: URL for the CSV index file
    CACHE_TTL: Cache time-to-live in seconds
    DEFAULT_WORKERS: Default number of concurrent workers
    MAX_WORKERS: Maximum allowed concurrent workers
    DEFAULT_TIMEOUT: Default HTTP timeout in seconds
    CHUNK_SIZE: File download chunk size in bytes
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from platformdirs import user_cache_dir


@dataclass
class Config:
    """Configuration settings for SuiteSparse downloader."""

    # URLs
    BASE_URL: str = "https://suitesparse-collection-website.herokuapp.com"
    FILES_BASE_URL: str = "https://suitesparse-collection-website.herokuapp.com"
    CSV_INDEX_URL: str = "https://sparse.tamu.edu/files/ssstats.csv"

    # Cache settings
    CACHE_TTL: int = 3600  # 1 hour

    # Download settings
    MAX_WORKERS: int = 8
    DEFAULT_WORKERS: int = 4
    DEFAULT_TIMEOUT: float = 30.0
    CHUNK_SIZE: int = 8192

    # HTTP client settings
    MAX_CONNECTIONS: int = 10
    MAX_KEEPALIVE_CONNECTIONS: int = 5
    USER_AGENT: str = "ssdownload/0.1.0 (Python SuiteSparse downloader)"

    @classmethod
    def get_http_client_config(cls, timeout: float | None = None) -> dict[str, Any]:
        """Get HTTP client configuration for httpx.AsyncClient.

        Args:
            timeout: Custom timeout in seconds. If None, uses DEFAULT_TIMEOUT.

        Returns:
            Dictionary containing httpx client configuration with timeout,
            connection limits, redirect settings, and user agent.

        Example:
            >>> config = Config.get_http_client_config(timeout=30.0)
            >>> async with httpx.AsyncClient(**config) as client:
            ...     response = await client.get("https://example.com")
        """
        return {
            "timeout": httpx.Timeout(timeout or cls.DEFAULT_TIMEOUT),
            "limits": httpx.Limits(
                max_connections=cls.MAX_CONNECTIONS,
                max_keepalive_connections=cls.MAX_KEEPALIVE_CONNECTIONS,
            ),
            "follow_redirects": True,
            "headers": {"User-Agent": cls.USER_AGENT},
        }

    @classmethod
    def get_file_extension(cls, format_type: str) -> str:
        """Get file extension for the given format type.

        Args:
            format_type: Matrix format ('mat', 'mm', 'rb')

        Returns:
            File extension string including the dot

        Example:
            >>> Config.get_file_extension("mat")
            '.mat'
            >>> Config.get_file_extension("mm")
            '.tar.gz'
        """
        extensions = {"mat": ".mat", "mm": ".tar.gz", "rb": ".tar.gz"}
        return extensions.get(format_type, ".mat")

    @classmethod
    def get_matrix_url(cls, group: str, name: str, format_type: str = "mat") -> str:
        """Generate download URL for a matrix file.

        Args:
            group: Matrix group/collection name
            name: Matrix name
            format_type: File format ('mat', 'mm', 'rb')

        Returns:
            Complete download URL for the matrix file

        Raises:
            ValueError: If format_type is not supported

        Example:
            >>> Config.get_matrix_url("Boeing", "ct20stif", "mat")
            'https://suitesparse-collection-website.herokuapp.com/mat/Boeing/ct20stif.mat'
        """
        if format_type == "mat":
            return f"{cls.FILES_BASE_URL}/mat/{group}/{name}.mat"
        elif format_type == "mm":
            return f"{cls.FILES_BASE_URL}/MM/{group}/{name}.tar.gz"
        elif format_type == "rb":
            return f"{cls.FILES_BASE_URL}/RB/{group}/{name}.tar.gz"
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @classmethod
    def get_checksum_url(cls, group: str, name: str, format_type: str = "mat") -> str:
        """Generate MD5 checksum URL for a matrix file.

        Args:
            group: Matrix group/collection name
            name: Matrix name
            format_type: File format ('mat', 'mm', 'rb')

        Returns:
            Complete URL for the MD5 checksum file

        Example:
            >>> Config.get_checksum_url("Boeing", "ct20stif", "mat")
            'https://suitesparse-collection-website.herokuapp.com/mat/Boeing/ct20stif.mat.md5'
        """
        base_url = cls.get_matrix_url(group, name, format_type)
        return f"{base_url}.md5"

    @classmethod
    def get_default_cache_dir(cls) -> Path:
        """Get the default system cache directory for ssdownload.

        Uses platformdirs to get the appropriate cache directory for the current OS:
        - Linux/macOS: ~/.cache/ssdownload/
        - Windows: %LOCALAPPDATA%/ssdownload/cache/

        Can be overridden by setting the SSDOWNLOAD_CACHE_DIR environment variable.

        Returns:
            Path to the default cache directory

        Example:
            >>> cache_dir = Config.get_default_cache_dir()
            >>> print(cache_dir)
            PosixPath('/home/user/.cache/ssdownload')
        """
        # Allow override via environment variable
        env_cache_dir = os.getenv("SSDOWNLOAD_CACHE_DIR")
        if env_cache_dir:
            return Path(env_cache_dir)

        # Use platformdirs for system-appropriate cache directory
        return Path(user_cache_dir("ssdownload", appauthor=False))
