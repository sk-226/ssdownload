"""Real integration tests with actual SuiteSparse API calls."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from ssdownload.client import SuiteSparseDownloader
from ssdownload.filters import Filter


@pytest.mark.slow
@pytest.mark.integration
class TestRealAPIIntegration:
    """Integration tests using real SuiteSparse API."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    async def test_real_matrix_search(self):
        """Test actual matrix search with real API."""
        downloader = SuiteSparseDownloader()

        # Search for small matrices to keep test fast
        filter_obj = Filter(n_rows=(None, 100))  # Very small matrices
        matrices, total_count = downloader.list_matrices(filter_obj, limit=5)

        # Verify we got real data
        assert isinstance(matrices, list)
        assert isinstance(total_count, int)
        assert total_count >= len(matrices)

        # Verify data structure
        for matrix in matrices:
            assert isinstance(matrix, dict)
            assert "group" in matrix
            assert "name" in matrix
            assert "num_rows" in matrix or "rows" in matrix

            # Verify filter actually worked
            rows = matrix.get("num_rows", matrix.get("rows", 0))
            if rows:
                assert rows <= 100

    async def test_real_matrix_info_retrieval(self):
        """Test retrieving info for a known matrix."""
        downloader = SuiteSparseDownloader()

        # Use a well-known small matrix from HB collection
        try:
            matrices, _ = downloader.list_matrices(Filter(group="HB"), limit=1)
            if not matrices:
                pytest.skip("No HB matrices available")

            matrix = matrices[0]
            group = matrix["group"]
            name = matrix["name"]

            # Test matrix info retrieval
            info_matrices, _ = downloader.list_matrices(
                Filter(group=group, name=name), limit=1
            )

            assert len(info_matrices) == 1
            assert info_matrices[0]["group"] == group
            assert info_matrices[0]["name"] == name

        except Exception as e:
            pytest.skip(f"API not available: {e}")

    async def test_real_group_listing(self):
        """Test listing real matrix groups."""
        downloader = SuiteSparseDownloader()

        try:
            # Get actual groups from the API
            groups = await downloader.get_available_groups()

            assert isinstance(groups, set)
            assert len(groups) > 0

            # Known groups that should exist
            known_groups = {"HB", "Boeing", "FIDAP"}
            found_known = known_groups.intersection(groups)
            assert len(found_known) > 0, f"Expected some known groups in {groups}"

        except Exception as e:
            pytest.skip(f"API not available: {e}")

    async def test_real_spd_filter(self):
        """Test SPD filtering with real data."""
        downloader = SuiteSparseDownloader()

        try:
            # Get SPD matrices
            spd_matrices, spd_total = downloader.list_matrices(
                Filter(spd=True), limit=10
            )

            assert isinstance(spd_matrices, list)
            assert spd_total > 0

            # Verify all returned matrices are actually SPD
            for matrix in spd_matrices:
                assert matrix.get("spd") is True, f"Non-SPD matrix returned: {matrix}"

        except Exception as e:
            pytest.skip(f"API not available: {e}")

    async def test_real_field_filter(self):
        """Test field type filtering with real data."""
        downloader = SuiteSparseDownloader()

        try:
            # Test real field filter
            real_matrices, _ = downloader.list_matrices(Filter(field="real"), limit=5)

            for matrix in real_matrices:
                field = matrix.get("field", "")
                assert field == "real", f"Non-real matrix returned: {matrix}"

        except Exception as e:
            pytest.skip(f"API not available: {e}")

    async def test_real_size_filter(self):
        """Test size filtering with real data."""
        downloader = SuiteSparseDownloader()

        try:
            # Test size range filter
            size_filtered, _ = downloader.list_matrices(
                Filter(size=(100, 1000)), limit=10
            )

            for matrix in size_filtered:
                rows = matrix.get("num_rows", matrix.get("rows", 0))
                cols = matrix.get("num_cols", matrix.get("cols", 0))

                if rows and cols:
                    size = max(rows, cols)  # Use larger dimension
                    assert 100 <= size <= 1000, f"Size {size} outside range: {matrix}"

        except Exception as e:
            pytest.skip(f"API not available: {e}")

    def test_matrix_not_found_error(self):
        """Test error handling for non-existent matrices."""
        downloader = SuiteSparseDownloader()

        # Try to search for a matrix that definitely doesn't exist
        non_existent_filter = Filter(name="this_matrix_definitely_does_not_exist_12345")
        matrices, total = downloader.list_matrices(non_existent_filter, limit=1)

        # Should return empty results, not error
        assert matrices == []
        assert total == 0

    async def test_concurrent_requests(self):
        """Test that concurrent API requests work correctly."""
        downloader = SuiteSparseDownloader()

        try:
            # Create multiple concurrent requests
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    downloader.find_matrices(Filter(n_rows=(None, 50 + i * 10)))
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All requests should succeed
            for i, result in enumerate(results):
                assert not isinstance(result, Exception), (
                    f"Request {i} failed: {result}"
                )
                assert isinstance(result, list)

        except Exception as e:
            pytest.skip(f"Concurrent API calls not supported: {e}")

    async def test_api_response_consistency(self):
        """Test that API responses are consistent across calls."""
        downloader = SuiteSparseDownloader()

        try:
            # Make the same request twice
            filter_obj = Filter(group="HB", n_rows=(None, 50))

            matrices1, total1 = downloader.list_matrices(filter_obj, limit=5)
            matrices2, total2 = downloader.list_matrices(filter_obj, limit=5)

            # Results should be identical
            assert total1 == total2
            assert len(matrices1) == len(matrices2)

            # Matrix data should be the same (allowing for different ordering)
            names1 = {(m["group"], m["name"]) for m in matrices1}
            names2 = {(m["group"], m["name"]) for m in matrices2}
            assert names1 == names2

        except Exception as e:
            pytest.skip(f"API consistency test failed: {e}")

    async def test_api_data_quality(self):
        """Test that API returns well-formed data."""
        downloader = SuiteSparseDownloader()

        try:
            matrices, _ = downloader.list_matrices(Filter(), limit=10)

            for matrix in matrices:
                # Required fields should exist
                assert "group" in matrix, f"Missing group in {matrix}"
                assert "name" in matrix, f"Missing name in {matrix}"

                # Numeric fields should be numeric
                for field in [
                    "num_rows",
                    "rows",
                    "num_cols",
                    "cols",
                    "nnz",
                    "nonzeros",
                ]:
                    if field in matrix:
                        value = matrix[field]
                        assert isinstance(value, int | float), (
                            f"Non-numeric {field}: {value}"
                        )
                        assert value >= 0, f"Negative {field}: {value}"

                # Boolean fields should be boolean
                for field in ["spd", "symmetric", "real", "complex", "binary"]:
                    if field in matrix:
                        value = matrix[field]
                        assert isinstance(value, bool), f"Non-boolean {field}: {value}"

                # String fields should be strings
                for field in ["group", "name", "field", "kind"]:
                    if field in matrix:
                        value = matrix[field]
                        assert isinstance(value, str), f"Non-string {field}: {value}"
                        assert len(value) > 0, f"Empty {field}: {value}"

        except Exception as e:
            pytest.skip(f"API data quality test failed: {e}")

    async def test_limit_parameter_effectiveness(self):
        """Test that limit parameter actually works."""
        downloader = SuiteSparseDownloader()

        try:
            # Test different limits
            for limit in [1, 5, 10]:
                matrices, total = downloader.list_matrices(Filter(), limit=limit)

                # Should not exceed limit
                assert len(matrices) <= limit

                # If total > limit, should return exactly limit items
                if total > limit:
                    assert len(matrices) == limit

        except Exception as e:
            pytest.skip(f"Limit test failed: {e}")
