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
        condition_number: Tuple of (min, max) for condition number (from page)
        matrix_norm: Tuple of (min, max) for matrix 2-norm (from page)
        numerical_rank: Tuple of (min, max) for numerical rank (from page)
        null_space_dim: Tuple of (min, max) for null space dimension (from page)
        num_strong_components: Tuple of (min, max) for strongly connected components (from page)
        num_dmperm_blocks: Tuple of (min, max) for Dmperm blocks (from page)
        structural_rank: Tuple of (min, max) for structural rank (from page)
        cholesky_candidate: Filter for Cholesky candidate matrices (from page)
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
    condition_number: tuple[float | None, float | None] | None = None
    matrix_norm: tuple[float | None, float | None] | None = None
    numerical_rank: tuple[int | None, int | None] | None = None
    null_space_dim: tuple[int | None, int | None] | None = None
    num_strong_components: tuple[int | None, int | None] | None = None
    num_dmperm_blocks: tuple[int | None, int | None] | None = None
    structural_rank: tuple[int | None, int | None] | None = None
    cholesky_candidate: bool | None = None

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

        # Page-scraped filters (condition number, norm, rank, etc.)
        if self.condition_number is not None:
            cond = matrix_info.get("condition_number")
            if not self._check_range(cond, self.condition_number):
                return False

        if self.matrix_norm is not None:
            norm = matrix_info.get("matrix_norm")
            if not self._check_range(norm, self.matrix_norm):
                return False

        if self.numerical_rank is not None:
            rank = matrix_info.get("numerical_rank")
            if not self._check_range(rank, self.numerical_rank):
                return False

        if self.null_space_dim is not None:
            nsd = matrix_info.get("null_space_dim")
            if not self._check_range(nsd, self.null_space_dim):
                return False

        if self.num_strong_components is not None:
            nsc = matrix_info.get("num_strong_components")
            if not self._check_range(nsc, self.num_strong_components):
                return False

        if self.num_dmperm_blocks is not None:
            ndb = matrix_info.get("num_dmperm_blocks")
            if not self._check_range(ndb, self.num_dmperm_blocks):
                return False

        if self.structural_rank is not None:
            sr = matrix_info.get("structural_rank")
            if not self._check_range(sr, self.structural_rank):
                return False

        if self.cholesky_candidate is not None:
            cc = matrix_info.get("cholesky_candidate")
            if cc is None or cc != self.cholesky_candidate:
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

    def requires_page_data(self) -> bool:
        """Check if this filter requires data from matrix web pages.

        Returns:
            True if any page-scraped filter fields are set
        """
        return any(
            getattr(self, field) is not None
            for field in (
                "condition_number",
                "matrix_norm",
                "numerical_rank",
                "null_space_dim",
                "num_strong_components",
                "num_dmperm_blocks",
                "structural_rank",
                "cholesky_candidate",
            )
        )

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

        if self.condition_number is not None:
            result["condition_number"] = self.condition_number

        if self.matrix_norm is not None:
            result["matrix_norm"] = self.matrix_norm

        if self.numerical_rank is not None:
            result["numerical_rank"] = self.numerical_rank

        if self.null_space_dim is not None:
            result["null_space_dim"] = self.null_space_dim

        if self.num_strong_components is not None:
            result["num_strong_components"] = self.num_strong_components

        if self.num_dmperm_blocks is not None:
            result["num_dmperm_blocks"] = self.num_dmperm_blocks

        if self.structural_rank is not None:
            result["structural_rank"] = self.structural_rank

        if self.cholesky_candidate is not None:
            result["cholesky_candidate"] = self.cholesky_candidate

        return result
