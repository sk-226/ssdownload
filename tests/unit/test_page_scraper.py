"""Tests for page_scraper module."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ssdownload.page_scraper import PageScraper

SAMPLE_HTML = """
<html>
<body>
<table class="table table-striped">
<tbody>
<tr><th>Name</th><td>nos5</td></tr>
<tr><th>Group</th><td>HB</td></tr>
<tr><th>Matrix ID</th><td>221</td></tr>
<tr><th>Date</th><td>1982</td></tr>
<tr><th>Author</th><td>H. Simon</td></tr>
<tr><th>Editor</th><td>I. Duff, R. Grimes, J. Lewis</td></tr>
</tbody>
</table>
<table class="table table-striped">
<tbody>
<tr><th>Structural Rank</th><td>468</td></tr>
<tr><th>Structural Rank Full</th><td>true</td></tr>
<tr><th>Num Dmperm Blocks</th><td>1</td></tr>
<tr><th>Strongly Connect Components</th><td>1</td></tr>
<tr><th>Num Explicit Zeros</th><td>0</td></tr>
<tr><th>Pattern Symmetry</th><td>100%</td></tr>
<tr><th>Numeric Symmetry</th><td>100%</td></tr>
<tr><th>Cholesky Candidate</th><td>yes</td></tr>
<tr><th>Positive Definite</th><td>yes</td></tr>
<tr><th>Type</th><td>real</td></tr>
</tbody>
</table>
<table class="table table-striped">
<tbody>
<tr><th>Matrix Norm</th><td>5.820291e+05</td></tr>
<tr><th>Minimum Singular Value</th><td>5.289948e+01</td></tr>
<tr><th>Condition Number</th><td>1.100255e+04</td></tr>
<tr><th>Rank</th><td>468</td></tr>
<tr><th>sprank(A)-rank(A)</th><td>0</td></tr>
<tr><th>Null Space Dimension</th><td>0</td></tr>
<tr><th>Full Numerical Rank?</th><td>yes</td></tr>
</tbody>
</table>
</body>
</html>
"""

SAMPLE_HTML_NO_SVD = """
<html>
<body>
<table class="table table-striped">
<tbody>
<tr><th>Name</th><td>large_matrix</td></tr>
<tr><th>Group</th><td>SNAP</td></tr>
</tbody>
</table>
<table class="table table-striped">
<tbody>
<tr><th>Structural Rank</th><td></td></tr>
<tr><th>Strongly Connect Components</th><td>1,588</td></tr>
<tr><th>Num Explicit Zeros</th><td>0</td></tr>
<tr><th>Pattern Symmetry</th><td>55.7%</td></tr>
<tr><th>Cholesky Candidate</th><td>no</td></tr>
<tr><th>Positive Definite</th><td>no</td></tr>
<tr><th>Type</th><td>binary</td></tr>
</tbody>
</table>
</body>
</html>
"""


class TestPageScraper:
    def test_parse_page_html_full(self):
        scraper = PageScraper()
        result = scraper._parse_page_html(SAMPLE_HTML)

        assert result["structural_rank"] == 468
        assert result["structural_rank_full"] is True
        assert result["num_dmperm_blocks"] == 1
        assert result["num_strong_components"] == 1
        assert result["num_explicit_zeros"] == 0
        assert result["cholesky_candidate"] is True
        assert result["page_positive_definite"] is True
        assert result["rb_type"] == "real"

        assert result["matrix_norm"] == pytest.approx(5.820291e05)
        assert result["min_singular_value"] == pytest.approx(5.289948e01)
        assert result["condition_number"] == pytest.approx(1.100255e04)
        assert result["numerical_rank"] == 468
        assert result["rank_deficiency"] == 0
        assert result["null_space_dim"] == 0
        assert result["full_numerical_rank"] is True

        assert result["date"] == "1982"
        assert result["author"] == "H. Simon"
        assert result["editor"] == "I. Duff, R. Grimes, J. Lewis"

    def test_parse_page_html_no_svd(self):
        scraper = PageScraper()
        result = scraper._parse_page_html(SAMPLE_HTML_NO_SVD)

        assert "condition_number" not in result
        assert "matrix_norm" not in result
        assert "numerical_rank" not in result
        assert result["num_strong_components"] == 1588
        assert result["cholesky_candidate"] is False
        assert result["page_positive_definite"] is False

    def test_parse_value_types(self):
        scraper = PageScraper()
        assert scraper._parse_value("468", "int") == 468
        assert scraper._parse_value("1,588", "int") == 1588
        assert scraper._parse_value("5.82e+05", "float") == pytest.approx(5.82e05)
        assert scraper._parse_value("100%", "percent") == pytest.approx(1.0)
        assert scraper._parse_value("55.7%", "percent") == pytest.approx(0.557)
        assert scraper._parse_value("yes", "bool") is True
        assert scraper._parse_value("no", "bool") is False
        assert scraper._parse_value("true", "bool") is True
        assert scraper._parse_value("real", "str") == "real"
        assert scraper._parse_value("", "int") is None
        assert scraper._parse_value("", "float") is None

    @pytest.mark.asyncio
    async def test_enrich_matrix_info(self):
        scraper = PageScraper()

        mock_response = AsyncMock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = lambda: None

        matrix = {"group": "HB", "name": "nos5", "rows": 468, "cols": 468}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.get = AsyncMock(return_value=mock_response)

            enriched = await scraper.enrich_matrix_info(matrix)

        assert enriched["rows"] == 468
        assert enriched["condition_number"] == pytest.approx(1.100255e04)
        assert enriched["structural_rank"] == 468

    def test_disk_cache(self, tmp_path: Path):
        scraper = PageScraper(cache_dir=tmp_path)
        scraper._page_cache = {"HB/nos5": {"condition_number": 11002.55}}
        scraper._save_disk_cache()

        cache_file = tmp_path / PageScraper.PAGE_CACHE_FILENAME
        assert cache_file.exists()

        with open(cache_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["HB/nos5"]["condition_number"] == 11002.55

    def test_parse_page_html_empty(self):
        scraper = PageScraper()
        result = scraper._parse_page_html("<html><body></body></html>")
        assert result == {}
