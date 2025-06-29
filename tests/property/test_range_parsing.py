"""Property-based tests for range parsing utilities."""

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from ssdownload.cli_utils import parse_range


class TestRangeParsingProperties:
    """Test mathematical properties of range parsing."""

    @given(value=st.integers(min_value=0, max_value=10**9))
    def test_single_value_parsing(self, value):
        """Test that single values create proper ranges."""
        result = parse_range(str(value))

        # Property: Single value should create (value, value) tuple
        assert result == (value, value)

        # Property: Result should be a valid range
        assert result[0] <= result[1]

    @given(
        min_val=st.integers(min_value=0, max_value=10**6),
        max_val=st.integers(min_value=0, max_value=10**6),
    )
    def test_range_parsing_properties(self, min_val, max_val):
        """Test properties of range parsing."""
        assume(min_val <= max_val)

        range_str = f"{min_val}:{max_val}"
        result = parse_range(range_str)

        # Property: Parsed range should match input
        assert result == (min_val, max_val)

        # Property: Result should be ordered
        assert result[0] <= result[1]

    @given(max_val=st.integers(min_value=1, max_value=10**6))
    def test_open_start_range(self, max_val):
        """Test open start ranges."""
        range_str = f":{max_val}"
        result = parse_range(range_str)

        # Property: Open start should have None as first element
        assert result == (None, max_val)

        # Property: Second element should be the specified max
        assert result[1] == max_val

    @given(min_val=st.integers(min_value=0, max_value=10**6))
    def test_open_end_range(self, min_val):
        """Test open end ranges."""
        range_str = f"{min_val}:"
        result = parse_range(range_str)

        # Property: Open end should have None as second element
        assert result == (min_val, None)

        # Property: First element should be the specified min
        assert result[0] == min_val

    @given(
        base=st.integers(min_value=1, max_value=999),
        exp1=st.integers(min_value=0, max_value=6),
        exp2=st.integers(min_value=0, max_value=6),
    )
    def test_scientific_notation_parsing(self, base, exp1, exp2):
        """Test scientific notation parsing properties."""
        assume(exp1 <= exp2)  # Ensure proper ordering

        val1 = base * (10**exp1)
        val2 = base * (10**exp2)

        # Test scientific notation formats
        range_str = f"{base}e{exp1}:{base}e{exp2}"
        result = parse_range(range_str)

        # Property: Scientific notation should be correctly parsed
        assert result == (val1, val2)

        # Property: Result maintains mathematical ordering
        assert result[0] <= result[1]

    @given(
        value=st.floats(
            min_value=0.1, max_value=10**6, allow_nan=False, allow_infinity=False
        )
    )
    def test_float_parsing_properties(self, value):
        """Test floating point value parsing."""
        # Skip values that might have precision issues
        assume(abs(value) >= 0.1)
        assume(abs(value) <= 10**6)

        result = parse_range(str(value))

        # Property: Float values should be converted to int for ranges
        expected_int = int(float(str(value)))
        assert result == (expected_int, expected_int)

    def test_range_parsing_invariants(self):
        """Test invariants that should always hold."""
        test_cases = ["100", "100:500", ":500", "100:", "1e3:5e3", "0:0"]

        for case in test_cases:
            result = parse_range(case)

            # Invariant: Result is always a 2-tuple
            assert isinstance(result, tuple)
            assert len(result) == 2

            # Invariant: Non-None values are numeric
            for val in result:
                if val is not None:
                    assert isinstance(val, int | float)

            # Invariant: If both values exist, min <= max
            if result[0] is not None and result[1] is not None:
                assert result[0] <= result[1]

    @given(
        invalid_input=st.text().filter(
            lambda x: (x and ":" not in x and not _is_valid_number_string(x))
        )
    )
    def test_invalid_input_handling(self, invalid_input):
        """Test behavior with invalid inputs."""
        # Property: Invalid inputs should raise ValueError
        with pytest.raises(ValueError):
            parse_range(invalid_input)


def _is_valid_number_string(s: str) -> bool:
    """Check if string represents a valid number that parse_range can handle."""
    try:
        float(s)
        return True
    except ValueError:
        return False
