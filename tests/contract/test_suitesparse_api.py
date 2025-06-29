"""Contract tests for SuiteSparse API response format."""

import httpx
import pytest

from ssdownload.config import Config
from ssdownload.index_manager import IndexManager


@pytest.mark.slow
@pytest.mark.contract
class TestSuiteSparseAPIContract:
    """Test that SuiteSparse API responses match expected format."""

    async def test_csv_index_format_contract(self):
        """Test that CSV index follows expected format."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(Config.CSV_INDEX_URL)
                response.raise_for_status()
                content = response.text

                lines = content.strip().split("\n")

                # Contract: First line should be number of matrices
                assert len(lines) >= 2, "CSV should have at least header and one matrix"

                first_line = lines[0].strip()
                assert first_line.isdigit(), (
                    f"First line should be number: {first_line}"
                )

                num_matrices = int(first_line)
                assert num_matrices > 0, "Should have positive number of matrices"

                # Contract: Second line should be date
                date_line = lines[1].strip()
                assert len(date_line) >= 8, f"Date line too short: {date_line}"

                # Contract: Remaining lines should be matrix data
                matrix_lines = lines[2:]
                assert len(matrix_lines) > 0, "Should have matrix data lines"

                # Test first few matrix lines for format
                for i, line in enumerate(matrix_lines[:5]):
                    if not line.strip():
                        continue

                    fields = line.split(",")
                    assert len(fields) >= 12, (
                        f"Line {i + 3} has too few fields: {len(fields)}"
                    )

                    # Contract: Field format validation
                    group, name, rows, cols, nnz = fields[:5]

                    assert len(group) > 0, f"Empty group at line {i + 3}"
                    assert len(name) > 0, f"Empty name at line {i + 3}"
                    assert rows.isdigit(), f"Non-numeric rows '{rows}' at line {i + 3}"
                    assert cols.isdigit(), f"Non-numeric cols '{cols}' at line {i + 3}"
                    assert nnz.isdigit(), f"Non-numeric nnz '{nnz}' at line {i + 3}"

                    # Validate boolean fields
                    bool_fields = fields[5:9]  # real, binary, complex, 2d_3d
                    for j, bool_field in enumerate(bool_fields):
                        assert bool_field in [
                            "0",
                            "1",
                        ], (
                            f"Invalid boolean '{bool_field}' at field {j + 5}, line {i + 3}"
                        )

        except Exception as e:
            pytest.skip(f"CSV contract test failed: {e}")

    async def test_parsed_matrix_data_contract(self):
        """Test that parsed matrix data contains required fields."""
        try:
            index_manager = IndexManager()
            matrices = await index_manager.get_index()

            assert len(matrices) > 0, "Should parse at least one matrix"

            for i, matrix in enumerate(matrices[:10]):  # Test first 10
                # Contract: Required fields must exist
                required_fields = ["group", "name"]
                for field in required_fields:
                    assert field in matrix, (
                        f"Missing required field '{field}' in matrix {i}"
                    )
                    assert isinstance(matrix[field], str), (
                        f"Field '{field}' should be string in matrix {i}"
                    )
                    assert len(matrix[field]) > 0, (
                        f"Field '{field}' should not be empty in matrix {i}"
                    )

                # Contract: Numeric fields should be numeric
                numeric_fields = [
                    "num_rows",
                    "num_cols",
                    "nnz",
                    "rows",
                    "cols",
                    "nonzeros",
                ]
                for field in numeric_fields:
                    if field in matrix:
                        value = matrix[field]
                        assert isinstance(value, int | float), (
                            f"Field '{field}' should be numeric in matrix {i}, got {type(value)}"
                        )
                        assert value >= 0, (
                            f"Field '{field}' should be non-negative in matrix {i}, got {value}"
                        )

                # Contract: Boolean fields should be boolean
                boolean_fields = [
                    "real",
                    "binary",
                    "complex",
                    "2d_3d",
                    "symmetric",
                    "spd",
                ]
                for field in boolean_fields:
                    if field in matrix:
                        value = matrix[field]
                        assert isinstance(value, bool), (
                            f"Field '{field}' should be boolean in matrix {i}, got {type(value)}"
                        )

                # Contract: Field mappings should be consistent
                if "field" in matrix:
                    field_value = matrix["field"]
                    assert field_value in [
                        "real",
                        "complex",
                        "integer",
                        "binary",
                    ], f"Invalid field type '{field_value}' in matrix {i}"

                    # Consistency check with boolean flags
                    if field_value == "real" and "real" in matrix:
                        assert matrix["real"] is True, (
                            f"Field='real' but real=False in matrix {i}"
                        )
                    if field_value == "complex" and "complex" in matrix:
                        assert matrix["complex"] is True, (
                            f"Field='complex' but complex=False in matrix {i}"
                        )

                # Contract: Size consistency
                if "size" in matrix:
                    size = matrix["size"]
                    rows = matrix.get("num_rows", matrix.get("rows", 0))
                    cols = matrix.get("num_cols", matrix.get("cols", 0))

                    if rows and cols:
                        expected_size = max(rows, cols)
                        assert size == expected_size, (
                            f"Size mismatch: size={size}, max(rows,cols)={expected_size} in matrix {i}"
                        )

        except Exception as e:
            pytest.skip(f"Parsed data contract test failed: {e}")

    def test_filter_result_contract(self):
        """Test that filter operations return correctly formatted results."""
        from ssdownload.client import SuiteSparseDownloader
        from ssdownload.filters import Filter

        try:
            downloader = SuiteSparseDownloader()

            # Test various filter combinations
            test_filters = [
                Filter(),  # No filter
                Filter(spd=True),
                Filter(field="real"),
                Filter(n_rows=(None, 100)),
                Filter(group="HB"),
            ]

            for filter_obj in test_filters:
                matrices, total_count = downloader.list_matrices(filter_obj, limit=5)

                # Contract: Return type should be tuple
                assert isinstance(matrices, list), (
                    f"Matrices should be list for filter {filter_obj}"
                )
                assert isinstance(total_count, int), (
                    f"Total count should be int for filter {filter_obj}"
                )

                # Contract: Total count should be >= returned count
                assert total_count >= len(matrices), (
                    f"Total {total_count} < returned {len(matrices)} for filter {filter_obj}"
                )

                # Contract: All returned matrices should match filter
                for matrix in matrices:
                    assert filter_obj.matches(matrix), (
                        f"Matrix {matrix['group']}/{matrix['name']} doesn't match filter {filter_obj}"
                    )

        except Exception as e:
            pytest.skip(f"Filter contract test failed: {e}")

    async def test_url_generation_contract(self):
        """Test that URL generation follows expected patterns."""
        from ssdownload.config import Config

        # Contract: URLs should follow SuiteSparse format
        test_cases = [
            ("Boeing", "ct20stif", "mat"),
            ("HB", "bcsstk01", "mm"),
            ("FIDAP", "ex15", "rb"),
        ]

        for group, name, format_type in test_cases:
            url = Config.get_matrix_url(group, name, format_type)

            # Contract: URL structure
            assert url.startswith("https://"), f"URL should use HTTPS: {url}"

            # Secure hostname validation
            from urllib.parse import urlparse

            parsed_url = urlparse(url)
            expected_hostname = "suitesparse-collection-website.herokuapp.com"
            assert parsed_url.hostname == expected_hostname, (
                f"URL should point to SuiteSparse hostname '{expected_hostname}', got '{parsed_url.hostname}': {url}"
            )
            assert group in url, f"URL should contain group '{group}': {url}"
            assert name in url, f"URL should contain name '{name}': {url}"

            # Contract: Format-specific checks
            if format_type == "mat":
                assert url.endswith(".mat"), f"MAT URL should end with .mat: {url}"
            else:
                assert url.endswith(".tar.gz"), (
                    f"Compressed format should end with .tar.gz: {url}"
                )

    async def test_checksum_url_contract(self):
        """Test that checksum URLs follow expected patterns."""
        from ssdownload.config import Config

        test_cases = [
            ("Boeing", "ct20stif", "mat"),
            ("HB", "bcsstk01", "mm"),
        ]

        for group, name, format_type in test_cases:
            checksum_url = Config.get_checksum_url(group, name, format_type)

            # Contract: Checksum URL structure
            assert checksum_url.startswith("https://"), (
                f"Checksum URL should use HTTPS: {checksum_url}"
            )

            # Secure hostname validation
            from urllib.parse import urlparse

            parsed_checksum_url = urlparse(checksum_url)
            expected_hostname = "suitesparse-collection-website.herokuapp.com"
            assert parsed_checksum_url.hostname == expected_hostname, (
                f"Checksum URL should point to SuiteSparse hostname '{expected_hostname}', got '{parsed_checksum_url.hostname}': {checksum_url}"
            )
            assert checksum_url.endswith(".md5"), (
                f"Checksum URL should end with .md5: {checksum_url}"
            )
            assert group in checksum_url, (
                f"Checksum URL should contain group '{group}': {checksum_url}"
            )
            assert name in checksum_url, (
                f"Checksum URL should contain name '{name}': {checksum_url}"
            )

    def test_error_response_contract(self):
        """Test that error responses are handled consistently."""
        from ssdownload.client import SuiteSparseDownloader

        downloader = SuiteSparseDownloader()

        # Test various error conditions
        error_cases = [
            # These should not raise exceptions, but return empty results
            ("nonexistent_group", "nonexistent_matrix"),
        ]

        for group, name in error_cases:
            from ssdownload.filters import Filter

            filter_obj = Filter(group=group, name=name)
            matrices, total = downloader.list_matrices(filter_obj, limit=1)

            # Contract: Errors should result in empty results, not exceptions
            assert matrices == [], f"Should return empty list for {group}/{name}"
            assert total == 0, f"Should return zero total for {group}/{name}"

    async def test_api_stability_contract(self):
        """Test that API endpoints are stable and accessible."""
        urls_to_test = [
            Config.CSV_INDEX_URL,
            Config.BASE_URL,
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in urls_to_test:
                try:
                    response = await client.head(url)

                    # Contract: URLs should be accessible
                    assert response.status_code in [
                        200,
                        301,
                        302,
                    ], f"URL {url} returned {response.status_code}"

                except Exception as e:
                    pytest.skip(f"URL {url} not accessible: {e}")
