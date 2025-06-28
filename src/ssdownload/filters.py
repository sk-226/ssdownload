"""Filter classes for SuiteSparse Matrix Collection."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Filter:
    """Filter for SuiteSparse Matrix Collection matrices.

    Attributes:
        spd: Filter for symmetric positive definite matrices
        n_rows: Tuple of (min, max) for number of rows
        n_cols: Tuple of (min, max) for number of columns
        nnz: Tuple of (min, max) for number of nonzeros
        field: Filter by field type ('real', 'complex', 'integer', 'binary')
        group: Filter by matrix group/collection name
        name: Filter by matrix name (can be partial match)
        kind: Filter by matrix kind ('directed graph', 'undirected graph', etc.)
        posdef: Filter for positive definite matrices
        structure: Filter by matrix structure ('symmetric', 'unsymmetric', etc.)
    """

    spd: bool | None = None
    n_rows: tuple[int | None, int | None] | None = None
    n_cols: tuple[int | None, int | None] | None = None
    nnz: tuple[int | None, int | None] | None = None
    field: str | None = None
    group: str | None = None
    name: str | None = None
    kind: str | None = None
    posdef: bool | None = None
    structure: str | None = None

    def matches(self, matrix_info: dict[str, Any]) -> bool:
        """Check if a matrix matches this filter.

        Args:
            matrix_info: Dictionary containing matrix metadata

        Returns:
            True if matrix matches all filter criteria
        """
        # Check SPD (Symmetric Positive Definite) - must be symmetric AND positive definite AND real
        if self.spd is not None:
            if self.spd:
                # When SPD is required, use the calculated SPD flag
                spd_flag = matrix_info.get("spd", False)
                if not spd_flag:
                    return False
            else:
                # When SPD is explicitly False, exclude SPD matrices
                spd_flag = matrix_info.get("spd", False)
                if spd_flag:
                    return False

        # Check positive definite flag
        if self.posdef is not None and matrix_info.get("posdef") != self.posdef:
            return False

        # Check number of rows
        if self.n_rows is not None:
            rows = matrix_info.get("num_rows", matrix_info.get("rows"))
            if not self._check_range(rows, self.n_rows):
                return False

        # Check number of columns
        if self.n_cols is not None:
            cols = matrix_info.get("num_cols", matrix_info.get("cols"))
            if not self._check_range(cols, self.n_cols):
                return False

        # Check number of nonzeros
        if self.nnz is not None:
            nonzeros = matrix_info.get("nnz", matrix_info.get("nonzeros"))
            if not self._check_range(nonzeros, self.nnz):
                return False

        # Check field type
        if self.field is not None:
            field_type = matrix_info.get("field", "").lower()
            if self.field.lower() not in field_type:
                return False

        # Check group
        if self.group is not None:
            group_name = matrix_info.get("group", "")
            if self.group.lower() not in group_name.lower():
                return False

        # Check name
        if self.name is not None:
            matrix_name = matrix_info.get("name", "")
            if self.name.lower() not in matrix_name.lower():
                return False

        # Check kind
        if self.kind is not None:
            kind_type = matrix_info.get("kind", "").lower()
            if self.kind.lower() not in kind_type:
                return False

        # Check structure
        if self.structure is not None:
            struct_type = matrix_info.get("structure", "").lower()
            if self.structure.lower() not in struct_type:
                return False

        return True

    def _check_range(
        self,
        value: int | float | None,
        range_filter: tuple[int | float | None, int | float | None],
    ) -> bool:
        """Check if a value falls within a range filter.

        Args:
            value: The value to check
            range_filter: Tuple of (min, max) where either can be None

        Returns:
            True if value is within range
        """
        if value is None:
            return False

        min_val, max_val = range_filter

        if min_val is not None and value < min_val:
            return False

        if max_val is not None and value > max_val:
            return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert filter to dictionary representation."""
        result: dict[str, Any] = {}

        if self.spd is not None:
            result["spd"] = self.spd

        if self.posdef is not None:
            result["posdef"] = self.posdef

        if self.n_rows is not None:
            result["n_rows"] = self.n_rows

        if self.n_cols is not None:
            result["n_cols"] = self.n_cols

        if self.nnz is not None:
            result["nnz"] = self.nnz

        if self.field is not None:
            result["field"] = self.field

        if self.group is not None:
            result["group"] = self.group

        if self.name is not None:
            result["name"] = self.name

        if self.kind is not None:
            result["kind"] = self.kind

        if self.structure is not None:
            result["structure"] = self.structure

        return result
