"""Tests for cli_utils module."""

from ssdownload.cli_utils import build_filter, parse_range
from ssdownload.filters import Filter


class TestCliUtils:
    """Test CLI utility functions."""

    def test_parse_range_single_value(self):
        """Test parsing single value as range."""
        result = parse_range("1000")
        assert result == (1000, 1000)

    def test_parse_range_both_values(self):
        """Test parsing range with both min and max."""
        result = parse_range("1000:5000")
        assert result == (1000, 5000)

    def test_parse_range_min_only(self):
        """Test parsing range with only minimum value."""
        result = parse_range("1000:")
        assert result == (1000, None)

    def test_parse_range_max_only(self):
        """Test parsing range with only maximum value."""
        result = parse_range(":5000")
        assert result == (None, 5000)

    def test_parse_range_scientific_notation(self):
        """Test parsing range with scientific notation."""
        result = parse_range("1e3:5e3")
        assert result == (1000, 5000)

    def test_parse_range_float_values(self):
        """Test parsing range with float values."""
        result = parse_range("1000.5:5000.7")
        assert result == (1000, 5000)  # Should convert to int

    def test_build_filter_empty(self):
        """Test building filter with no arguments."""
        result = build_filter()
        assert result is None

    def test_build_filter_spd_only(self):
        """Test building filter with only SPD flag."""
        result = build_filter(spd=True)
        assert isinstance(result, Filter)
        assert result.spd is True
        assert result.posdef is None

    def test_build_filter_string_fields(self):
        """Test building filter with string fields."""
        result = build_filter(
            field="real",
            group="Boeing",
            name="ct20stif",
            kind="structural",
            structure="symmetric",
        )
        assert isinstance(result, Filter)
        assert result.field == "real"
        assert result.group == "Boeing"
        assert result.name == "ct20stif"
        assert result.kind == "structural"
        assert result.structure == "symmetric"

    def test_build_filter_size_range(self):
        """Test building filter with size range."""
        result = build_filter(size="1000:5000")
        assert isinstance(result, Filter)
        assert result.n_rows == (1000, 5000)
        assert result.n_cols == (1000, 5000)

    def test_build_filter_separate_row_col_ranges(self):
        """Test building filter with separate row and column ranges."""
        result = build_filter(rows="1000:2000", cols="3000:4000")
        assert isinstance(result, Filter)
        assert result.n_rows == (1000, 2000)
        assert result.n_cols == (3000, 4000)

    def test_build_filter_nnz_range(self):
        """Test building filter with nnz range."""
        result = build_filter(nnz=":1000000")
        assert isinstance(result, Filter)
        assert result.nnz == (None, 1000000)

    def test_build_filter_size_overrides_separate_ranges(self):
        """Test that size parameter overrides separate row/col ranges."""
        result = build_filter(size="1000:5000", rows="2000:3000", cols="4000:6000")
        assert isinstance(result, Filter)
        # rows and cols should override size
        assert result.n_rows == (2000, 3000)
        assert result.n_cols == (4000, 6000)

    def test_build_filter_all_parameters(self):
        """Test building filter with all parameters."""
        result = build_filter(
            spd=True,
            size="1000:5000",
            rows="2000:3000",
            cols="4000:6000",
            nnz=":1000000",
            field="real",
            group="Boeing",
            name="ct20stif",
            kind="structural",
            structure="symmetric",
        )
        assert isinstance(result, Filter)
        assert result.spd is True
        assert result.n_rows == (2000, 3000)  # Should override size
        assert result.n_cols == (4000, 6000)  # Should override size
        assert result.nnz == (None, 1000000)
        assert result.field == "real"
        assert result.group == "Boeing"
        assert result.name == "ct20stif"
        assert result.kind == "structural"
        assert result.structure == "symmetric"

    def test_build_filter_false_flags_ignored(self):
        """Test that false flags are ignored."""
        result = build_filter(spd=False)
        assert result is None  # No filters set

    def test_build_filter_empty_strings_ignored(self):
        """Test that empty strings are ignored."""
        result = build_filter(field="", group="", name="")
        assert result is None  # No filters set
