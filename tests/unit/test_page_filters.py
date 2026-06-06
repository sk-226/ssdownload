"""Tests for page-scraped filter fields and parse_float_range."""

import pytest

from ssdownload.cli_utils import parse_float_range
from ssdownload.filters import Filter


class TestParseFloatRange:
    def test_single_value(self):
        assert parse_float_range("1e4") == (1e4, 1e4)

    def test_full_range(self):
        assert parse_float_range("1e2:1e6") == (1e2, 1e6)

    def test_open_start(self):
        assert parse_float_range(":1e4") == (None, 1e4)

    def test_open_end(self):
        assert parse_float_range("1e2:") == (1e2, None)

    def test_negative_values(self):
        assert parse_float_range("-1.5:2.5") == (-1.5, 2.5)

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_float_range("")

    def test_colon_only_raises(self):
        with pytest.raises(ValueError):
            parse_float_range(":")


class TestPageScrapedFilters:
    def test_condition_number_filter(self):
        f = Filter(condition_number=(None, 1e4))
        assert f.matches({"condition_number": 5000.0})
        assert not f.matches({"condition_number": 20000.0})

    def test_condition_number_missing_field(self):
        f = Filter(condition_number=(None, 1e4))
        assert not f.matches({})

    def test_matrix_norm_filter(self):
        f = Filter(matrix_norm=(1e2, 1e6))
        assert f.matches({"matrix_norm": 5.82e05})
        assert not f.matches({"matrix_norm": 1e7})

    def test_numerical_rank_filter(self):
        f = Filter(numerical_rank=(100, 500))
        assert f.matches({"numerical_rank": 468})
        assert not f.matches({"numerical_rank": 50})

    def test_null_space_dim_filter(self):
        f = Filter(null_space_dim=(0, 0))
        assert f.matches({"null_space_dim": 0})
        assert not f.matches({"null_space_dim": 5})

    def test_strong_components_filter(self):
        f = Filter(num_strong_components=(1, 10))
        assert f.matches({"num_strong_components": 1})
        assert not f.matches({"num_strong_components": 100})

    def test_dmperm_blocks_filter(self):
        f = Filter(num_dmperm_blocks=(1, 5))
        assert f.matches({"num_dmperm_blocks": 1})
        assert not f.matches({"num_dmperm_blocks": 10})

    def test_structural_rank_filter(self):
        f = Filter(structural_rank=(100, None))
        assert f.matches({"structural_rank": 468})
        assert not f.matches({"structural_rank": 50})

    def test_cholesky_candidate_filter(self):
        f = Filter(cholesky_candidate=True)
        assert f.matches({"cholesky_candidate": True})
        assert not f.matches({"cholesky_candidate": False})
        assert not f.matches({})

    def test_combined_csv_and_page_filters(self):
        f = Filter(spd=True, condition_number=(None, 1e5))
        matrix = {
            "spd": True,
            "symmetric": True,
            "posdef": True,
            "real": True,
            "condition_number": 11002.55,
        }
        assert f.matches(matrix)

        matrix_high_cond = dict(matrix)
        matrix_high_cond["condition_number"] = 1e6
        assert not f.matches(matrix_high_cond)

    def test_requires_page_data(self):
        assert not Filter().requires_page_data()
        assert not Filter(spd=True).requires_page_data()
        assert Filter(condition_number=(None, 1e4)).requires_page_data()
        assert Filter(matrix_norm=(1e2, 1e6)).requires_page_data()
        assert Filter(cholesky_candidate=True).requires_page_data()
        assert Filter(structural_rank=(100, None)).requires_page_data()

    def test_to_dict_includes_page_fields(self):
        f = Filter(
            condition_number=(None, 1e4),
            matrix_norm=(1e2, 1e6),
            cholesky_candidate=True,
        )
        d = f.to_dict()
        assert d["condition_number"] == (None, 1e4)
        assert d["matrix_norm"] == (1e2, 1e6)
        assert d["cholesky_candidate"] is True
