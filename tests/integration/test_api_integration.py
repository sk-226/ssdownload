"""Integration tests for SuiteSparse Matrix Collection Downloader Python API."""

from pathlib import Path

import pytest

from ssdownload import Filter, SuiteSparseDownloader
from ssdownload.exceptions import MatrixNotFoundError


class TestAPIIntegration:
    """Integration tests for the Python API."""

    @pytest.fixture
    def test_output_dir(self):
        """Create a test output directory."""
        test_dir = Path("test_output/api_tests")
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir

    def test_basic_initialization(self, test_output_dir):
        """Test basic initialization of SuiteSparseDownloader."""
        # Test with default settings
        downloader = SuiteSparseDownloader()
        assert downloader.cache_dir == Path.cwd()
        assert downloader.workers == 4
        assert downloader.timeout == 30.0
        assert downloader.verify_checksums is False

        # Test with custom settings
        downloader_custom = SuiteSparseDownloader(
            cache_dir=test_output_dir, workers=2, timeout=60.0, verify_checksums=True
        )
        assert downloader_custom.cache_dir == test_output_dir
        assert downloader_custom.workers == 2
        assert downloader_custom.timeout == 60.0
        assert downloader_custom.verify_checksums is True

    @pytest.mark.asyncio
    async def test_matrix_search(self):
        """Test matrix search functionality."""
        downloader = SuiteSparseDownloader()

        # Test finding small matrices
        filter_obj = Filter(
            n_rows=(None, 1000),  # Up to 1000 rows
            n_cols=(None, 1000),  # Up to 1000 columns
        )

        matrices = await downloader.find_matrices(filter_obj)
        assert len(matrices) > 0
        assert all(
            matrix.get("num_rows", matrix.get("rows", 0)) <= 1000 for matrix in matrices
        )
        assert all(
            matrix.get("num_cols", matrix.get("cols", 0)) <= 1000 for matrix in matrices
        )

        # Test limited results
        limited_matrices = await downloader._list_matrices_async(filter_obj, limit=5)
        assert len(limited_matrices) <= 5
        assert len(limited_matrices) > 0

    def test_synchronous_listing(self):
        """Test synchronous matrix listing."""
        downloader = SuiteSparseDownloader()

        # Test outside async context (should work)
        filter_obj = Filter(n_rows=(None, 50))  # Very small matrices
        matrices, total_count = downloader.list_matrices(filter_obj, limit=3)
        # Note: May return empty list if called from async context, which is expected
        assert isinstance(matrices, list)
        assert isinstance(total_count, int)

    @pytest.mark.asyncio
    async def test_group_operations(self):
        """Test group-related operations."""
        downloader = SuiteSparseDownloader()

        # Get available groups
        groups = await downloader._get_available_groups()
        assert len(groups) > 0
        assert isinstance(groups, set | list)

        # Test finding a specific matrix by name
        if "HB" in groups:
            group = await downloader.index_manager.find_matrix_group("bcsstk01")
            assert group == "HB"

    @pytest.mark.asyncio
    async def test_download_url_generation(self):
        """Test download URL generation without actual download."""
        downloader = SuiteSparseDownloader()

        # Find a small matrix
        filter_obj = Filter(
            n_rows=(None, 100),  # Very small matrix
            n_cols=(None, 100),
        )
        matrices = await downloader.find_matrices(filter_obj)

        if matrices:
            matrix = matrices[0]
            group = matrix.get("group")
            name = matrix.get("name")

            # Test URL generation
            from ssdownload.config import Config

            mat_url = Config.get_matrix_url(group, name, "mat")
            mm_url = Config.get_matrix_url(group, name, "mm")
            rb_url = Config.get_matrix_url(group, name, "rb")

            assert mat_url.startswith("https://")
            assert mm_url.startswith("https://")
            assert rb_url.startswith("https://")
            assert group in mat_url
            assert name in mat_url

            # Test checksum URL
            checksum_url = Config.get_checksum_url(group, name, "mat")
            assert checksum_url.startswith("https://")
            assert checksum_url.endswith(".md5")

    @pytest.mark.asyncio
    async def test_filter_functionality(self):
        """Test various filter combinations."""
        downloader = SuiteSparseDownloader()

        # Test SPD filter
        spd_filter = Filter(spd=True, n_rows=(None, 100))
        spd_matrices = await downloader.find_matrices(spd_filter)
        assert all(matrix.get("spd", False) for matrix in spd_matrices)

        # Test field filter
        real_filter = Filter(field="real", n_rows=(None, 50))
        real_matrices = await downloader.find_matrices(real_filter)
        assert all(matrix.get("field") == "real" for matrix in real_matrices)

        # Test group filter
        hb_filter = Filter(group="HB", n_rows=(None, 50))
        hb_matrices = await downloader.find_matrices(hb_filter)
        assert all(matrix.get("group") == "HB" for matrix in hb_matrices)

    @pytest.mark.asyncio
    async def test_matrix_info_retrieval(self):
        """Test retrieving detailed matrix information."""
        downloader = SuiteSparseDownloader()

        # Find a very small matrix
        filter_obj = Filter(n_rows=(None, 50), n_cols=(None, 50))
        matrices = await downloader.find_matrices(filter_obj)

        if matrices:
            matrix = matrices[0]

            # Verify required fields exist
            assert "group" in matrix
            assert "name" in matrix
            assert "num_rows" in matrix or "rows" in matrix
            assert "num_cols" in matrix or "cols" in matrix
            assert "nnz" in matrix or "nonzeros" in matrix
            assert "field" in matrix

            # Verify data types
            group = matrix.get("group")
            name = matrix.get("name")
            assert isinstance(group, str)
            assert isinstance(name, str)
            assert len(group) > 0
            assert len(name) > 0

    @pytest.mark.asyncio
    async def test_empty_filter_behavior(self):
        """Test behavior with empty/no filters."""
        downloader = SuiteSparseDownloader()

        # Test with None filter
        all_matrices = await downloader.find_matrices(None)
        assert len(all_matrices) > 1000  # Should return all matrices

        # Test with empty filter
        empty_filter = Filter()
        empty_filtered = await downloader.find_matrices(empty_filter)
        assert len(empty_filtered) == len(all_matrices)  # Should be same as no filter

    def test_config_settings(self):
        """Test configuration settings and constants."""
        from ssdownload.config import Config

        # Test constants exist
        assert hasattr(Config, "DEFAULT_WORKERS")
        assert hasattr(Config, "DEFAULT_TIMEOUT")
        assert hasattr(Config, "MAX_WORKERS")

        # Test URL methods work
        test_url = Config.get_matrix_url("TestGroup", "test_matrix", "mat")
        assert isinstance(test_url, str)
        assert "TestGroup" in test_url
        assert "test_matrix" in test_url

        # Test file extension mapping
        assert Config.get_file_extension("mat") == ".mat"
        assert Config.get_file_extension("mm") == ".tar.gz"
        assert Config.get_file_extension("rb") == ".tar.gz"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid inputs."""
        downloader = SuiteSparseDownloader()

        # Test with non-existent matrix name
        with pytest.raises(MatrixNotFoundError):
            await downloader.download_by_name("definitely_nonexistent_matrix_12345")

        # Test invalid group in find_matrix_group
        result = await downloader.index_manager.find_matrix_group(
            "nonexistent_matrix_name"
        )
        assert result is None


class TestAPIPerformance:
    """Performance and efficiency tests."""

    @pytest.mark.asyncio
    async def test_index_caching(self):
        """Test that index is cached properly."""
        downloader = SuiteSparseDownloader()

        # First call should fetch index
        matrices1 = await downloader.find_matrices(Filter(n_rows=(None, 50)))

        # Second call should use cached index (should be faster)
        matrices2 = await downloader.find_matrices(Filter(n_rows=(None, 60)))

        # Results should be consistent
        assert len(matrices1) > 0
        assert len(matrices2) >= len(matrices1)  # More inclusive filter

    @pytest.mark.asyncio
    async def test_group_caching(self):
        """Test that groups are cached properly."""
        downloader = SuiteSparseDownloader()

        # Multiple calls should return consistent results
        groups1 = await downloader._get_available_groups()
        groups2 = await downloader._get_available_groups()

        assert groups1 == groups2
        assert len(groups1) > 100  # Should have many groups


@pytest.mark.slow
class TestAPIRealDownload:
    """Real download tests (marked as slow)."""

    @pytest.fixture
    def download_dir(self):
        """Create download directory in test_output."""
        download_dir = Path("test_output/real_downloads")
        download_dir.mkdir(parents=True, exist_ok=True)
        return download_dir

    @pytest.mark.asyncio
    async def test_real_single_download(self, download_dir):
        """Test actual downloading of a very small matrix."""
        downloader = SuiteSparseDownloader(
            cache_dir=download_dir,
            workers=1,
            verify_checksums=False,  # Disable to avoid potential issues
        )

        # Find the smallest available matrix
        filter_obj = Filter(n_rows=(None, 50), n_cols=(None, 50))
        matrices = await downloader.find_matrices(filter_obj)

        if not matrices:
            pytest.skip("No small matrices available for download test")

        # Select smallest matrix by total size (rows * cols)
        matrix = min(
            matrices,
            key=lambda m: (
                m.get("num_rows", m.get("rows", 999))
                * m.get("num_cols", m.get("cols", 999))
            ),
        )

        group = matrix.get("group")
        name = matrix.get("name")

        # Test download by group and name
        mat_path = await downloader.download(group, name, "mat")
        assert mat_path.exists()
        assert mat_path.stat().st_size > 0
        assert mat_path.suffix == ".mat"

        # Test download by name only
        mm_path = await downloader.download_by_name(name, "mm")
        assert mm_path.exists()
        assert mm_path.stat().st_size > 0
        assert mm_path.suffix == ".mtx"  # Auto-extracted to .mtx file

        # Test backward compatibility: no extraction when extract_archives=False
        downloader_no_extract = SuiteSparseDownloader(
            cache_dir=download_dir / "no_extract",
            verify_checksums=False,
            extract_archives=False,
        )
        mm_path_no_extract = await downloader_no_extract.download_by_name(name, "mm")
        assert mm_path_no_extract.exists()
        assert mm_path_no_extract.stat().st_size > 0
        assert mm_path_no_extract.suffix == ".gz"  # Should remain compressed

    @pytest.mark.asyncio
    async def test_real_bulk_download(self, download_dir):
        """Test bulk downloading of very small matrices."""
        downloader = SuiteSparseDownloader(
            cache_dir=download_dir / "bulk", workers=2, verify_checksums=False
        )

        # Find very small matrices for bulk download
        filter_obj = Filter(n_rows=(None, 30), n_cols=(None, 30))

        downloaded_paths = await downloader.bulk_download(
            filter_obj=filter_obj,
            format_type="mat",
            max_files=2,  # Download only 2 files
        )

        assert len(downloaded_paths) <= 2
        assert len(downloaded_paths) > 0

        for path in downloaded_paths:
            if path:  # Some downloads might fail
                assert path.exists()
                assert path.stat().st_size > 0

    @pytest.mark.asyncio
    async def test_download_different_formats(self, download_dir):
        """Test downloading the same matrix in different formats."""
        downloader = SuiteSparseDownloader(
            cache_dir=download_dir / "formats", verify_checksums=False
        )

        # Find one small matrix
        filter_obj = Filter(n_rows=(None, 40), n_cols=(None, 40))
        matrices = await downloader.find_matrices(filter_obj)

        if not matrices:
            pytest.skip("No matrices available for format test")

        matrix = matrices[0]
        group = matrix.get("group")
        name = matrix.get("name")

        # Download in all three formats
        formats_to_test = ["mat", "mm", "rb"]
        downloaded_files = []

        for fmt in formats_to_test:
            try:
                path = await downloader.download(group, name, fmt)
                downloaded_files.append((fmt, path))
                assert path.exists()
                assert path.stat().st_size > 0
            except Exception as e:
                # Some formats might not be available for all matrices
                print(f"Format {fmt} failed for {group}/{name}: {e}")

        # At least one format should succeed
        assert len(downloaded_files) > 0
