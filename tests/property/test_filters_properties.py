"""Property-based tests for filter functionality."""

from hypothesis import assume, given
from hypothesis import strategies as st

from ssdownload.filters import Filter


class TestFilterProperties:
    """Test mathematical properties and invariants of filters."""

    @given(
        min_size=st.integers(1, 10000),
        max_size=st.integers(1, 10000),
    )
    def test_size_filter_range_properties(self, min_size, max_size):
        """Test that size filters maintain mathematical properties."""
        assume(min_size <= max_size)

        # Size is typically the max of rows and cols, so we test both dimensions
        filter_obj = Filter(n_rows=(min_size, max_size), n_cols=(min_size, max_size))

        # Property: Filter should accept matrices within range
        matrix_in_range = {
            "num_rows": (min_size + max_size) // 2,
            "num_cols": (min_size + max_size) // 2,
        }
        assert filter_obj.matches(matrix_in_range)

        # Property: Filter should reject matrices outside range (if possible)
        if min_size > 1:
            matrix_too_small = {
                "num_rows": min_size - 1,
                "num_cols": min_size - 1,
            }
            assert not filter_obj.matches(matrix_too_small)

    @given(field_type=st.sampled_from(["real", "complex", "integer", "binary"]))
    def test_field_filter_consistency(self, field_type):
        """Test field filter consistency."""
        filter_obj = Filter(field=field_type)

        # Property: Matching field should always pass
        matrix_matching = {"field": field_type}
        assert filter_obj.matches(matrix_matching)

        # Property: Non-matching field should always fail
        other_fields = {"real", "complex", "integer", "binary"} - {field_type}
        for other_field in other_fields:
            matrix_non_matching = {"field": other_field}
            assert not filter_obj.matches(matrix_non_matching)

    @given(
        spd_flag=st.booleans(),
        matrix_spd=st.booleans(),
    )
    def test_spd_filter_logic(self, spd_flag, matrix_spd):
        """Test SPD filter logical properties."""
        filter_obj = Filter(spd=spd_flag)
        matrix = {"spd": matrix_spd}

        # Property: SPD filter logic
        if spd_flag:
            # If filter requires SPD, only SPD matrices should match
            assert filter_obj.matches(matrix) == matrix_spd
        else:
            # If filter explicitly excludes SPD, non-SPD matrices should match
            assert filter_obj.matches(matrix) == (not matrix_spd)

    @given(
        rows_min=st.integers(1, 1000),
        rows_max=st.integers(1000, 10000),
        cols_min=st.integers(1, 1000),
        cols_max=st.integers(1000, 10000),
    )
    def test_separate_dimension_filters(self, rows_min, rows_max, cols_min, cols_max):
        """Test that separate row/column filters work independently."""
        filter_obj = Filter(
            n_rows=(rows_min, rows_max),
            n_cols=(cols_min, cols_max),
        )

        # Property: Matrix must satisfy both constraints
        matrix_valid = {
            "num_rows": (rows_min + rows_max) // 2,
            "num_cols": (cols_min + cols_max) // 2,
        }
        assert filter_obj.matches(matrix_valid)

        # Property: Violating row constraint should fail
        matrix_bad_rows = {
            "num_rows": rows_max + 1,
            "num_cols": (cols_min + cols_max) // 2,
        }
        assert not filter_obj.matches(matrix_bad_rows)

    @given(
        name_pattern=st.text(
            min_size=1,
            max_size=10,
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
        )
    )
    def test_name_filter_case_insensitive(self, name_pattern):
        """Test name filter case insensitivity."""
        filter_obj = Filter(name=name_pattern)

        # Property: Case variations should all match
        matrix_lower = {"name": name_pattern.lower()}
        matrix_upper = {"name": name_pattern.upper()}
        matrix_title = {"name": name_pattern.title()}

        # All case variations should match if the pattern is alphabetic
        if name_pattern.isalpha() and name_pattern.lower() != name_pattern.upper():
            assert filter_obj.matches(matrix_lower)
            assert filter_obj.matches(matrix_upper)
            assert filter_obj.matches(matrix_title)

    def test_filter_composition_properties(self):
        """Test properties of filter composition."""
        # Property: Multiple filters should be AND-ed together
        filter_spd = Filter(spd=True)
        filter_real = Filter(field="real")
        filter_combined = Filter(spd=True, field="real")

        matrix_spd_real = {"spd": True, "field": "real"}
        matrix_spd_complex = {"spd": True, "field": "complex"}
        matrix_nonspd_real = {"spd": False, "field": "real"}

        # Property: Combined filter is more restrictive
        assert filter_combined.matches(matrix_spd_real)
        assert not filter_combined.matches(matrix_spd_complex)
        assert not filter_combined.matches(matrix_nonspd_real)

        # Property: Individual filters are less restrictive
        assert filter_spd.matches(matrix_spd_real)
        assert filter_spd.matches(matrix_spd_complex)
        assert filter_real.matches(matrix_spd_real)
        assert filter_real.matches(matrix_nonspd_real)

    @given(
        nnz_min=st.integers(1, 100000),
        nnz_max=st.integers(100000, 1000000),
    )
    def test_nnz_filter_boundary_conditions(self, nnz_min, nnz_max):
        """Test non-zero elements filter boundary conditions."""
        filter_obj = Filter(nnz=(nnz_min, nnz_max))

        # Property: Boundary values should be included
        matrix_min_boundary = {"nnz": nnz_min}
        matrix_max_boundary = {"nnz": nnz_max}
        assert filter_obj.matches(matrix_min_boundary)
        assert filter_obj.matches(matrix_max_boundary)

        # Property: Values outside boundaries should be excluded
        if nnz_min > 1:
            matrix_below_min = {"nnz": nnz_min - 1}
            assert not filter_obj.matches(matrix_below_min)

        matrix_above_max = {"nnz": nnz_max + 1}
        assert not filter_obj.matches(matrix_above_max)
