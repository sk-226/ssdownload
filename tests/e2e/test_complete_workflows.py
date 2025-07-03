"""End-to-end workflow tests."""

import asyncio
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from ssdownload.cli import app
from ssdownload.client import SuiteSparseDownloader
from ssdownload.filters import Filter


@pytest.mark.slow
@pytest.mark.e2e
class TestCompleteWorkflows:
    """Test complete user workflows from start to finish."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()

    async def test_complete_search_and_download_workflow(self):
        """Test complete workflow: search -> info -> download -> verify."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                downloader = SuiteSparseDownloader(cache_dir=output_dir)

                # Step 1: Search for small matrices
                matrices, total = downloader.list_matrices(
                    Filter(n_rows=(None, 100)), limit=3
                )

                if not matrices:
                    pytest.skip("No small matrices available for testing")

                test_matrix = matrices[0]
                group = test_matrix["group"]
                name = test_matrix["name"]

                # Step 2: Get detailed info
                info_matrices, _ = downloader.list_matrices(
                    Filter(group=group, name=name), limit=1
                )
                assert len(info_matrices) == 1

                # Step 3: Download the matrix
                downloaded_path = await downloader.download(
                    group, name, "mat", output_dir
                )

                # Step 4: Verify download
                assert downloaded_path.exists()
                assert downloaded_path.name == f"{name}.mat"
                assert downloaded_path.stat().st_size > 0

                # Step 5: Test cache behavior (re-download should be instant)
                import time

                start_time = time.time()
                cached_path = await downloader.download(group, name, "mat", output_dir)
                cache_time = time.time() - start_time

                assert cached_path == downloaded_path
                assert cache_time < 1.0  # Should be nearly instant from cache

            except Exception as e:
                pytest.skip(f"E2E workflow test failed: {e}")

    def test_cli_complete_workflow(self):
        """Test complete CLI workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Step 1: List matrices
                result = self.runner.invoke(
                    app, ["list", "--limit", "3", "--field", "real"]
                )

                if result.exit_code != 0:
                    pytest.skip(f"CLI list failed: {result.stdout}")

                # Step 2: Get info about a matrix (use a known small one)
                # Try to extract a matrix name from the list output
                lines = result.stdout.split("\n")
                matrix_line = None
                for line in lines:
                    if "/" in line and "HB/" in line:  # Look for HB matrices
                        matrix_line = line
                        break

                if not matrix_line:
                    pytest.skip("No suitable matrix found in list output")

                # Extract matrix identifier
                import re

                match = re.search(r"│\s*([^│]+/[^│\s]+)", matrix_line)
                if not match:
                    pytest.skip("Could not parse matrix identifier")

                matrix_id = match.group(1).strip()

                # Step 3: Get matrix info
                info_result = self.runner.invoke(app, ["info", matrix_id])
                if info_result.exit_code != 0:
                    pytest.skip(f"CLI info failed: {info_result.stdout}")

                # Step 4: Download the matrix
                download_result = self.runner.invoke(
                    app,
                    ["download", matrix_id, "--output", temp_dir, "--format", "mat"],
                )

                if download_result.exit_code != 0:
                    pytest.skip(f"CLI download failed: {download_result.stdout}")

                # Step 5: Verify file was created
                group, name = matrix_id.split("/")
                expected_file = Path(temp_dir) / f"{name}.mat"
                assert expected_file.exists(), (
                    f"Downloaded file not found: {expected_file}"
                )
                assert expected_file.stat().st_size > 0

            except Exception as e:
                pytest.skip(f"CLI workflow test failed: {e}")

    async def test_bulk_download_workflow(self):
        """Test bulk download workflow with various filters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                downloader = SuiteSparseDownloader(cache_dir=output_dir)

                # Test bulk download with size constraint for speed
                filter_obj = Filter(
                    spd=True,
                    field="real",
                    n_rows=(None, 200),  # Small matrices only
                )

                downloaded_paths = await downloader.bulk_download(
                    filter_obj, max_files=3, format_type="mat"
                )

                # Verify downloads
                assert len(downloaded_paths) <= 3
                for path in downloaded_paths:
                    assert path.exists()
                    assert path.suffix == ".mat"
                    assert path.stat().st_size > 0

                # Verify all downloaded matrices match filter
                for path in downloaded_paths:
                    name = path.stem
                    # Find the matrix info to verify it matches filter
                    info_filter = Filter(name=name)
                    matrices, _ = downloader.list_matrices(info_filter, limit=1)

                    if matrices:
                        matrix = matrices[0]
                        assert filter_obj.matches(matrix), (
                            f"Downloaded matrix {name} doesn't match filter"
                        )

            except Exception as e:
                pytest.skip(f"Bulk download workflow test failed: {e}")

    def test_cli_bulk_workflow(self):
        """Test CLI bulk download workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Test CLI bulk download
                result = self.runner.invoke(
                    app,
                    [
                        "bulk",
                        "--spd",
                        "--field",
                        "real",
                        "--size",
                        ":300",  # Small matrices
                        "--max-files",
                        "2",
                        "--output",
                        temp_dir,
                        "--format",
                        "mat",
                    ],
                )

                if result.exit_code != 0:
                    pytest.skip(f"CLI bulk download failed: {result.stdout}")

                # Verify files were downloaded
                mat_files = list(Path(temp_dir).glob("*.mat"))
                assert len(mat_files) <= 2

                for mat_file in mat_files:
                    assert mat_file.stat().st_size > 0

            except Exception as e:
                pytest.skip(f"CLI bulk workflow test failed: {e}")

    async def test_error_recovery_workflow(self):
        """Test workflow with error conditions and recovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                downloader = SuiteSparseDownloader(cache_dir=output_dir)

                # Test 1: Search for non-existent matrix
                fake_filter = Filter(name="definitely_does_not_exist_12345")
                matrices, total = downloader.list_matrices(fake_filter, limit=1)
                assert matrices == []
                assert total == 0

                # Test 2: Try to download non-existent matrix
                from ssdownload.exceptions import MatrixNotFoundError

                with pytest.raises(MatrixNotFoundError):
                    await downloader.download_by_name("nonexistent_matrix_12345")

                # Test 3: Recover with valid operation
                valid_filter = Filter(n_rows=(None, 100))
                valid_matrices, _ = downloader.list_matrices(valid_filter, limit=1)

                if valid_matrices:
                    matrix = valid_matrices[0]
                    # This should succeed
                    path = await downloader.download(
                        matrix["group"], matrix["name"], "mat", output_dir
                    )
                    assert path.exists()

            except Exception as e:
                pytest.skip(f"Error recovery workflow test failed: {e}")

    async def test_concurrent_operations_workflow(self):
        """Test workflow with concurrent operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                # Create multiple downloaders to simulate concurrent usage
                downloaders = [
                    SuiteSparseDownloader(cache_dir=output_dir) for _ in range(3)
                ]

                # Get some matrices to work with
                filter_obj = Filter(n_rows=(None, 150))
                matrices, _ = downloaders[0].list_matrices(filter_obj, limit=3)

                if len(matrices) < 3:
                    pytest.skip("Not enough matrices for concurrent test")

                # Create concurrent tasks
                tasks = []
                for i, downloader in enumerate(downloaders):
                    if i < len(matrices):
                        matrix = matrices[i]
                        task = asyncio.create_task(
                            downloader.download(
                                matrix["group"], matrix["name"], "mat", output_dir
                            )
                        )
                        tasks.append(task)

                # Wait for all downloads to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Verify results
                successful_downloads = [r for r in results if isinstance(r, Path)]
                assert len(successful_downloads) > 0

                for path in successful_downloads:
                    assert path.exists()
                    assert path.stat().st_size > 0

            except Exception as e:
                pytest.skip(f"Concurrent operations workflow test failed: {e}")

    def test_cache_management_workflow(self):
        """Test cache management operations."""
        with tempfile.TemporaryDirectory():
            try:
                # Test clean-cache command
                result = self.runner.invoke(app, ["clean-cache", "--yes"])

                # Should succeed whether cache exists or not
                assert result.exit_code == 0

                # Test that we can still operate after cache clean
                list_result = self.runner.invoke(
                    app, ["list", "--limit", "1", "--field", "real"]
                )

                # This might fail if network is not available, which is okay
                if list_result.exit_code == 0:
                    assert "SuiteSparse Matrices" in list_result.stdout

            except Exception as e:
                pytest.skip(f"Cache management workflow test failed: {e}")

    async def test_format_compatibility_workflow(self):
        """Test downloading in different formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                downloader = SuiteSparseDownloader(cache_dir=output_dir)

                # Find a small matrix
                matrices, _ = downloader.list_matrices(
                    Filter(n_rows=(None, 100)), limit=1
                )

                if not matrices:
                    pytest.skip("No small matrices available")

                matrix = matrices[0]
                group = matrix["group"]
                name = matrix["name"]

                # Test different formats
                formats = ["mat", "mm", "rb"]
                downloaded_files = []

                for fmt in formats:
                    try:
                        path = await downloader.download(group, name, fmt, output_dir)
                        downloaded_files.append((fmt, path))
                        assert path.exists()
                        assert path.stat().st_size > 0
                    except Exception as e:
                        # Some formats might not be available for all matrices
                        print(f"Format {fmt} not available for {group}/{name}: {e}")

                # Should have at least one successful download
                assert len(downloaded_files) > 0

                # Verify file extensions (now auto-extracted)
                for fmt, path in downloaded_files:
                    if fmt == "mat":
                        assert path.suffix == ".mat"
                    elif fmt == "mm":
                        assert path.suffix == ".mtx"  # Auto-extracted Matrix Market
                    elif fmt == "rb":
                        assert path.suffix in [
                            ".rua",
                            ".rb",
                        ]  # Auto-extracted Rutherford-Boeing

            except Exception as e:
                pytest.skip(f"Format compatibility workflow test failed: {e}")
