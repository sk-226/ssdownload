"""Tests for filters module."""

from ssdownload.filters import Filter


class TestFilter:
    """Test Filter class."""

    def test_empty_filter_matches_all(self):
        """Empty filter should match all matrices."""
        filter_obj = Filter()
        matrix_info = {
            "name": "test_matrix",
            "group": "test_group",
            "num_rows": 1000,
            "nnz": 5000,
            "spd": True,
        }
        assert filter_obj.matches(matrix_info)

    def test_spd_filter(self):
        """Test SPD filtering."""
        filter_obj = Filter(spd=True)

        # Should match SPD matrix (symmetric + posdef + square)
        spd_matrix = {
            "symmetric": True,
            "spd": True,
            "num_rows": 100,
            "num_cols": 100,
            "name": "test",
        }
        assert filter_obj.matches(spd_matrix)

        # Should not match non-SPD matrix
        non_spd_matrix = {"spd": False, "symmetric": False, "name": "test"}
        assert not filter_obj.matches(non_spd_matrix)

        # Should not match non-symmetric matrix (spd should be False for non-symmetric)
        non_symmetric = {
            "symmetric": False,
            "spd": False,  # SPD requires symmetric, so this should be False
            "num_rows": 100,
            "num_cols": 100,
            "name": "test",
        }
        assert not filter_obj.matches(non_symmetric)

        # Should not match non-square matrix (spd should be False for non-square)
        non_square = {
            "symmetric": True,
            "spd": False,  # SPD requires square matrix, so this should be False
            "num_rows": 100,
            "num_cols": 200,
            "name": "test",
        }
        assert not filter_obj.matches(non_square)

    def test_size_range_filter(self):
        """Test size range filtering."""
        filter_obj = Filter(n_rows=(100, 1000))

        # Should match matrix in range
        in_range = {"num_rows": 500, "name": "test"}
        assert filter_obj.matches(in_range)

        # Should not match matrix below range
        below_range = {"num_rows": 50, "name": "test"}
        assert not filter_obj.matches(below_range)

        # Should not match matrix above range
        above_range = {"num_rows": 2000, "name": "test"}
        assert not filter_obj.matches(above_range)

    def test_open_ended_range(self):
        """Test open-ended range filters."""
        # Only minimum
        min_filter = Filter(nnz=(1000, None))
        assert min_filter.matches({"nnz": 2000, "name": "test"})
        assert not min_filter.matches({"nnz": 500, "name": "test"})

        # Only maximum
        max_filter = Filter(nnz=(None, 1000))
        assert max_filter.matches({"nnz": 500, "name": "test"})
        assert not max_filter.matches({"nnz": 2000, "name": "test"})

    def test_string_filters(self):
        """Test string-based filters."""
        filter_obj = Filter(group="Boeing", field="real")

        # Should match
        matching = {
            "group": "Boeing",
            "field": "real",
            "name": "test",
        }
        assert filter_obj.matches(matching)

        # Should not match wrong group
        wrong_group = {
            "group": "HB",
            "field": "real",
            "name": "test",
        }
        assert not filter_obj.matches(wrong_group)

    def test_partial_string_matching(self):
        """Test that string filters use partial matching."""
        filter_obj = Filter(name="stif")

        # Should match partial name
        partial_match = {"name": "ct20stif", "group": "Boeing"}
        assert filter_obj.matches(partial_match)

        # Should not match non-matching name
        no_match = {"name": "other_matrix", "group": "Boeing"}
        assert not filter_obj.matches(no_match)

    def test_case_insensitive_matching(self):
        """Test that string matching is case insensitive."""
        filter_obj = Filter(group="boeing")

        # Should match different case
        different_case = {"group": "Boeing", "name": "test"}
        assert filter_obj.matches(different_case)

    def test_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        filter_obj = Filter(spd=True, n_rows=(100, 1000), field="real", group="Boeing")

        # Should match all criteria (SPD requires symmetric + spd + square)
        all_match = {
            "symmetric": True,
            "spd": True,
            "num_rows": 500,
            "num_cols": 500,  # Must be square for SPD
            "field": "real",
            "group": "Boeing",
            "name": "test",
        }
        assert filter_obj.matches(all_match)

        # Should not match if one criterion fails
        one_fail = {
            "spd": False,  # Fails SPD check
            "num_rows": 500,
            "field": "real",
            "group": "Boeing",
            "name": "test",
        }
        assert not filter_obj.matches(one_fail)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        filter_obj = Filter(
            spd=True,
            n_rows=(100, 1000),
            field="real",
        )

        expected = {
            "spd": True,
            "n_rows": (100, 1000),
            "field": "real",
        }

        assert filter_obj.to_dict() == expected

    def test_missing_fields_dont_match(self):
        """Test that missing fields in matrix info don't cause matches."""
        filter_obj = Filter(nnz=(1000, None))

        # Matrix without nnz field should not match
        no_nnz = {"name": "test", "group": "test"}
        assert not filter_obj.matches(no_nnz)

    def test_alternative_field_names(self):
        """Test that alternative field names are handled."""
        filter_obj = Filter(n_rows=(100, 1000))

        # Should work with 'rows' instead of 'num_rows'
        alt_name = {"rows": 500, "name": "test"}
        assert filter_obj.matches(alt_name)
