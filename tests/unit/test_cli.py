"""Tests for CLI module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from ssdownload.cli import app
from ssdownload.cli_utils import parse_range


class TestCLI:
    """Test CLI functionality."""

    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()

    def test_parse_range_single_value(self):
        """Test parsing single value as range."""
        result = parse_range("1000")
        assert result == (1000, 1000)

    def test_parse_range_full_range(self):
        """Test parsing full range."""
        result = parse_range("1000:5000")
        assert result == (1000, 5000)

    def test_parse_range_open_start(self):
        """Test parsing range with open start."""
        result = parse_range(":5000")
        assert result == (None, 5000)

    def test_parse_range_open_end(self):
        """Test parsing range with open end."""
        result = parse_range("1000:")
        assert result == (1000, None)

    def test_parse_range_scientific_notation(self):
        """Test parsing range with scientific notation."""
        result = parse_range("1e3:5e6")
        assert result == (1000, 5000000)

    def test_help_command(self):
        """Test help command displays correctly."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Download sparse matrices" in result.stdout

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_download_command_success(self, mock_asyncio_run, mock_downloader_class):
        """Test successful single matrix download."""
        # Mock downloader instance
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader

        # Mock async download method
        mock_path = Path("/fake/path/Boeing/ct20stif.mat")
        mock_asyncio_run.return_value = mock_path

        result = self.runner.invoke(
            app, ["download", "Boeing/ct20stif", "--format", "mat", "--workers", "2"]
        )

        assert result.exit_code == 0
        assert "Downloaded:" in result.stdout

        # Verify downloader was created with correct parameters
        mock_downloader_class.assert_called_once_with(
            cache_dir=None,
            workers=2,
            verify_checksums=False,
            extract_archives=True,
            keep_archives=False,
            flat_structure=False,
        )

        # Verify download method was called
        mock_asyncio_run.assert_called_once()

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_download_command_error(self, mock_asyncio_run, mock_downloader_class):
        """Test download command with error."""
        mock_downloader_class.return_value = MagicMock()
        mock_asyncio_run.side_effect = Exception("Download failed")

        result = self.runner.invoke(app, ["download", "Boeing/ct20stif"])

        assert result.exit_code == 1
        assert "Error:" in result.stdout

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_bulk_command_basic(self, mock_asyncio_run, mock_downloader_class):
        """Test basic bulk download command."""
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        mock_asyncio_run.return_value = [Path("/fake/path1"), Path("/fake/path2")]

        result = self.runner.invoke(
            app, ["bulk", "--spd", "--format", "mm", "--max-files", "10"]
        )

        assert result.exit_code == 0
        assert "Downloaded 2 matrices" in result.stdout

        # Verify downloader was created
        mock_downloader_class.assert_called_once()

        # Verify bulk_download was called with async.run
        mock_asyncio_run.assert_called_once()

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_bulk_command_with_filters(self, mock_asyncio_run, mock_downloader_class):
        """Test bulk command with various filters."""
        mock_downloader_class.return_value = MagicMock()
        mock_asyncio_run.return_value = []

        result = self.runner.invoke(
            app,
            [
                "bulk",
                "--spd",
                "--size",
                "1000:5000",
                "--nnz",
                ":1000000",
                "--field",
                "real",
                "--group",
                "Boeing",
                "--workers",
                "8",
            ],
        )

        assert result.exit_code == 0

        # Verify downloader was created with correct workers
        mock_downloader_class.assert_called_once_with(
            cache_dir=None,
            workers=8,
            verify_checksums=False,
            extract_archives=True,
            keep_archives=False,
            flat_structure=False,
        )

    @patch("ssdownload.cli.SuiteSparseDownloader")
    def test_list_command_basic(self, mock_downloader_class):
        """Test basic list command."""
        # Mock matrices data
        mock_matrices = [
            {
                "group": "Boeing",
                "name": "ct20stif",
                "num_rows": 52329,
                "nnz": 2698463,
                "field": "real",
                "spd": True,
            },
            {
                "group": "HB",
                "name": "arc130",
                "num_rows": 130,
                "nnz": 1282,
                "field": "real",
                "spd": False,
            },
        ]

        mock_downloader = MagicMock()
        mock_downloader.list_matrices.return_value = (mock_matrices, len(mock_matrices))
        mock_downloader_class.return_value = mock_downloader

        result = self.runner.invoke(app, ["list", "--limit", "10"])

        assert result.exit_code == 0
        assert "Boeing/ct20stif" in result.stdout
        assert "HB/arc130" in result.stdout

        # Verify list_matrices was called with correct parameters
        mock_downloader.list_matrices.assert_called_once_with(
            None,  # No filter
            10,  # Limit
        )

    @patch("ssdownload.cli.SuiteSparseDownloader")
    def test_list_command_verbose(self, mock_downloader_class):
        """Test list command with verbose output."""
        mock_matrices = [
            {
                "group": "Boeing",
                "name": "ct20stif",
                "num_rows": 52329,
                "num_cols": 52329,
                "nnz": 2698463,
                "field": "real",
                "spd": True,
            },
        ]

        mock_downloader = MagicMock()
        mock_downloader.list_matrices.return_value = (mock_matrices, len(mock_matrices))
        mock_downloader_class.return_value = mock_downloader

        result = self.runner.invoke(app, ["list", "--verbose"])

        assert result.exit_code == 0
        # In verbose mode, should show separate columns
        assert "Boeing" in result.stdout
        assert "ct20stif" in result.stdout
        assert "52329" in result.stdout

    @patch("ssdownload.cli.SuiteSparseDownloader")
    def test_list_command_with_filters(self, mock_downloader_class):
        """Test list command with filters."""
        mock_downloader = MagicMock()
        mock_downloader.list_matrices.return_value = ([], 0)
        mock_downloader_class.return_value = mock_downloader

        result = self.runner.invoke(
            app, ["list", "--spd", "--size", "1000:10000", "--field", "real"]
        )

        assert result.exit_code == 0
        assert "No matrices found" in result.stdout

    @patch("ssdownload.cli.SuiteSparseDownloader")
    def test_info_command_success(self, mock_downloader_class):
        """Test info command with existing matrix."""
        mock_matrix = {
            "group": "Boeing",
            "name": "ct20stif",
            "rows": 52329,
            "cols": 52329,
            "num_rows": 52329,
            "num_cols": 52329,
            "nnz": 2698463,
            "field": "real",
            "spd": True,
            "structure": "symmetric",
        }

        mock_downloader = MagicMock()
        mock_downloader.list_matrices.return_value = ([mock_matrix], 1)
        mock_downloader._get_matrix_url.side_effect = (
            lambda g, n, f: f"https://sparse.tamu.edu/{f}/{g}/{n}.ext"
        )
        mock_downloader_class.return_value = mock_downloader

        result = self.runner.invoke(app, ["info", "Boeing/ct20stif"])

        assert result.exit_code == 0
        assert "Boeing/ct20stif" in result.stdout
        assert "52329" in result.stdout
        assert "Download URLs" in result.stdout

    @patch("ssdownload.cli.SuiteSparseDownloader")
    def test_info_command_not_found(self, mock_downloader_class):
        """Test info command with non-existent matrix."""
        mock_downloader = MagicMock()
        mock_downloader.list_matrices.return_value = ([], 0)
        mock_downloader_class.return_value = mock_downloader

        result = self.runner.invoke(app, ["info", "NonExistent/matrix"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_command_help_messages(self):
        """Test that all commands have proper help messages."""
        commands = ["download", "bulk", "list", "info", "clean-cache"]

        for cmd in commands:
            result = self.runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0
            assert len(result.stdout) > 50  # Should have substantial help text

    @patch("ssdownload.cli.Config.get_default_cache_dir")
    def test_clean_cache_no_cache_file(self, mock_cache_dir):
        """Test clean-cache command when no cache file exists."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            mock_cache_dir.return_value = cache_dir

            result = self.runner.invoke(app, ["clean-cache", "--yes"])

            assert result.exit_code == 0
            assert "No cache file found" in result.stdout
            assert "cache is already clean" in result.stdout

    @patch("ssdownload.cli.Config.get_default_cache_dir")
    def test_clean_cache_with_existing_file(self, mock_cache_dir):
        """Test clean-cache command with existing cache file."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache_file = cache_dir / "ssstats_cache.json"

            # Create a fake cache file
            cache_file.write_text('{"test": "data"}')

            mock_cache_dir.return_value = cache_dir

            result = self.runner.invoke(app, ["clean-cache", "--yes"])

            assert result.exit_code == 0
            assert "Cache cleared successfully" in result.stdout
            assert (
                "Next matrix operation will download fresh index data" in result.stdout
            )
            assert not cache_file.exists()

    @patch("ssdownload.cli.Config.get_default_cache_dir")
    def test_clean_cache_shows_cache_info(self, mock_cache_dir):
        """Test clean-cache command shows cache file information."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache_file = cache_dir / "ssstats_cache.json"

            # Create a cache file with known content
            test_data = '{"test": "data"}' * 100  # Make it bigger
            cache_file.write_text(test_data)

            mock_cache_dir.return_value = cache_dir

            result = self.runner.invoke(app, ["clean-cache", "--yes"])

            assert result.exit_code == 0
            assert str(cache_file) in result.stdout
            assert "KB" in result.stdout or "MB" in result.stdout

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_download_with_flat_option(self, mock_asyncio_run, mock_downloader):
        """Test download command with --flat option."""
        mock_asyncio_run.return_value = Path("./ct20stif.mat")

        result = self.runner.invoke(app, ["download", "ct20stif", "--flat"])

        assert result.exit_code == 0

        # Verify SuiteSparseDownloader was called with flat_structure=True
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert call_kwargs["flat_structure"] is True

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_bulk_with_flat_option(self, mock_asyncio_run, mock_downloader):
        """Test bulk command with --flat option."""
        mock_asyncio_run.return_value = [Path("./matrix1.mat"), Path("./matrix2.mat")]

        result = self.runner.invoke(app, ["bulk", "--spd", "--flat"])

        assert result.exit_code == 0

        # Verify SuiteSparseDownloader was called with flat_structure=True
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert call_kwargs["flat_structure"] is True

    @patch("ssdownload.cli.SuiteSparseDownloader")
    @patch("ssdownload.cli.asyncio.run")
    def test_download_without_flat_option_default(
        self, mock_asyncio_run, mock_downloader
    ):
        """Test download command without --flat option (default behavior)."""
        mock_asyncio_run.return_value = Path("./Boeing/ct20stif.mat")

        result = self.runner.invoke(app, ["download", "ct20stif"])

        assert result.exit_code == 0

        # Verify SuiteSparseDownloader was called with flat_structure=False (default)
        mock_downloader.assert_called_once()
        call_kwargs = mock_downloader.call_args.kwargs
        assert call_kwargs["flat_structure"] is False
