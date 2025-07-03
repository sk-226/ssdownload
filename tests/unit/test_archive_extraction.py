"""Tests for archive extraction functionality."""

import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ssdownload.downloader import FileDownloader
from ssdownload.exceptions import DownloadError


class TestArchiveExtraction:
    """Test archive extraction functionality."""

    def test_init_with_extraction_options(self):
        """Test FileDownloader initialization with extraction options."""
        # Test default values
        downloader = FileDownloader()
        assert downloader.extract_archives is True
        assert downloader.keep_archives is False

        # Test custom values
        downloader = FileDownloader(extract_archives=False, keep_archives=True)
        assert downloader.extract_archives is False
        assert downloader.keep_archives is True

    def test_validate_tar_members_safe(self):
        """Test tar member validation with safe paths."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a safe test archive
            archive_path = temp_path / "test.tar.gz"
            test_file = temp_path / "test.mtx"
            test_file.write_text("test matrix data")

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(test_file, arcname="test.mtx")

            # Validate should pass for safe archive
            with tarfile.open(archive_path, "r:gz") as tar:
                downloader._validate_tar_members(tar)  # Should not raise

    def test_validate_tar_members_unsafe_absolute_path(self):
        """Test tar member validation rejects absolute paths."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create archive with absolute path using TarInfo directly
            archive_path = temp_path / "unsafe.tar.gz"
            test_file = temp_path / "test.mtx"
            test_file.write_text("test matrix data")

            with tarfile.open(archive_path, "w:gz") as tar:
                # Create TarInfo with absolute path manually
                tarinfo = tar.gettarinfo(test_file)
                tarinfo.name = "/etc/passwd"  # Force absolute path
                with open(test_file, "rb") as f:
                    tar.addfile(tarinfo, f)

            # Validation should fail
            with tarfile.open(archive_path, "r:gz") as tar:
                with pytest.raises(DownloadError, match="absolute path"):
                    downloader._validate_tar_members(tar)

    def test_validate_tar_members_unsafe_parent_reference(self):
        """Test tar member validation rejects parent directory references."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create archive with parent reference
            archive_path = temp_path / "unsafe.tar.gz"
            test_file = temp_path / "test.mtx"
            test_file.write_text("test matrix data")

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(test_file, arcname="../../../etc/passwd")  # Parent reference

            # Validation should fail
            with tarfile.open(archive_path, "r:gz") as tar:
                with pytest.raises(DownloadError, match="parent reference"):
                    downloader._validate_tar_members(tar)

    def test_find_main_file_matrix_market(self):
        """Test finding main file prioritizes .mtx files."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            files = [
                temp_path / "readme.txt",
                temp_path / "matrix.mtx",  # Should be selected
                temp_path / "other.dat",
            ]

            for f in files:
                f.write_text("test content")

            main_file = downloader._find_main_file(files)
            assert main_file.name == "matrix.mtx"

    def test_find_main_file_rutherford_boeing(self):
        """Test finding main file prioritizes .rua files when no .mtx."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            files = [
                temp_path / "readme.txt",
                temp_path / "matrix.rua",  # Should be selected
                temp_path / "other.dat",
            ]

            for f in files:
                f.write_text("test content")

            main_file = downloader._find_main_file(files)
            assert main_file.name == "matrix.rua"

    def test_find_main_file_largest_fallback(self):
        """Test finding main file falls back to largest file."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files with different sizes
            small_file = temp_path / "small.txt"
            small_file.write_text("small")

            large_file = temp_path / "large.dat"
            large_file.write_text("this is a much larger file content")

            files = [small_file, large_file]

            main_file = downloader._find_main_file(files)
            assert main_file.name == "large.dat"

    async def test_extract_archive_success(self):
        """Test successful archive extraction."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test archive
            archive_path = temp_path / "test.tar.gz"
            test_content = "%%MatrixMarket matrix coordinate real general\n5 5 3\n"

            # Create temporary file for archiving
            matrix_file = temp_path / "matrix.mtx"
            matrix_file.write_text(test_content)

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(matrix_file, arcname="matrix.mtx")

            # Remove original file so we can test extraction
            matrix_file.unlink()

            # Extract archive
            extracted_path = await downloader._extract_archive(archive_path)

            assert extracted_path.exists()
            assert extracted_path.name == "matrix.mtx"
            assert extracted_path.read_text() == test_content

    async def test_extract_archive_cleanup_on_error(self):
        """Test cleanup of partially extracted files on error."""
        downloader = FileDownloader()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create corrupted archive
            archive_path = temp_path / "corrupted.tar.gz"
            archive_path.write_text("not a valid tar.gz file")

            # Extraction should fail and clean up
            with pytest.raises(DownloadError):
                await downloader._extract_archive(archive_path)

            # Verify no extracted files remain
            extracted_files = list(temp_path.glob("*.mtx"))
            assert len(extracted_files) == 0

    async def test_handle_extraction_keep_archive(self):
        """Test extraction with archive keeping enabled."""
        downloader = FileDownloader(keep_archives=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test archive
            archive_path = temp_path / "test.tar.gz"
            matrix_file = temp_path / "matrix.mtx"
            matrix_file.write_text("test matrix")

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(matrix_file, arcname="matrix.mtx")

            matrix_file.unlink()  # Remove original

            # Mock the extraction to avoid complexity
            with patch.object(downloader, "_extract_archive", return_value=matrix_file):
                matrix_file.write_text("test matrix")  # Recreate for test

                result = await downloader._handle_extraction(archive_path, "mm")

                # Archive should still exist
                assert archive_path.exists()
                assert result == matrix_file

    async def test_handle_extraction_remove_archive(self):
        """Test extraction with archive removal (default)."""
        downloader = FileDownloader(keep_archives=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test archive
            archive_path = temp_path / "test.tar.gz"
            matrix_file = temp_path / "matrix.mtx"
            matrix_file.write_text("test matrix")

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(matrix_file, arcname="matrix.mtx")

            matrix_file.unlink()  # Remove original

            # Mock the extraction to avoid complexity
            with patch.object(downloader, "_extract_archive", return_value=matrix_file):
                matrix_file.write_text("test matrix")  # Recreate for test

                result = await downloader._handle_extraction(archive_path, "mm")

                # Archive should be removed
                assert not archive_path.exists()
                assert result == matrix_file

    async def test_download_file_with_extraction(self):
        """Test download_file method with format_type triggering extraction."""
        downloader = FileDownloader(extract_archives=True, keep_archives=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            archive_path = temp_path / "test.tar.gz"
            extracted_path = temp_path / "test.mtx"

            # Create temp file that will be renamed
            temp_part_path = archive_path.with_suffix(archive_path.suffix + ".part")

            def mock_download_side_effect(*args, **kwargs):
                # Create the .part file that download_with_resume would create
                temp_part_path.write_text("test archive content")

            # Mock the download and extraction process
            with patch.object(
                downloader,
                "_download_with_resume",
                side_effect=mock_download_side_effect,
            ) as mock_download:
                with patch.object(
                    downloader, "_handle_extraction", return_value=extracted_path
                ) as mock_extract:
                    result = await downloader.download_file(
                        url="http://example.com/test.tar.gz",
                        output_path=archive_path,
                        format_type="mm",  # Should trigger extraction
                    )

                    # Should have called download
                    mock_download.assert_called_once()

                    # Should have called extraction for mm format
                    mock_extract.assert_called_once_with(archive_path, "mm", None, None)

                    # Should return extracted path
                    assert result == extracted_path

    async def test_download_file_no_extraction_for_mat(self):
        """Test download_file method doesn't extract for MAT format."""
        downloader = FileDownloader(extract_archives=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            mat_path = temp_path / "test.mat"

            # Create temp file that will be renamed
            temp_part_path = mat_path.with_suffix(mat_path.suffix + ".part")

            def mock_download_side_effect(*args, **kwargs):
                # Create the .part file that download_with_resume would create
                temp_part_path.write_text("test matrix content")

            # Mock the download process
            with patch.object(
                downloader,
                "_download_with_resume",
                side_effect=mock_download_side_effect,
            ) as mock_download:
                with patch.object(downloader, "_handle_extraction") as mock_extract:
                    result = await downloader.download_file(
                        url="http://example.com/test.mat",
                        output_path=mat_path,
                        format_type="mat",  # Should NOT trigger extraction
                    )

                    # Should have called download
                    mock_download.assert_called_once()

                    # Should NOT have called extraction for mat format
                    mock_extract.assert_not_called()

                    # Should return original path
                    assert result == mat_path
