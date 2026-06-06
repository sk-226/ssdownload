"""CLI utility functions for SuiteSparse downloader."""

import math
from typing import Any

from .filters import Filter


def parse_range(value: str) -> tuple[int | None, int | None]:
    """Parse a range string like '1000:5000' or ':5000' or '1000:'."""
    if not value or value.strip() == "":
        raise ValueError("Empty range value")

    if ":" not in value:
        # Single value, treat as exact match
        try:
            float_val = float(value)
            if not math.isfinite(float_val):
                raise ValueError(f"Invalid range value: {value} (infinity or NaN)")
            val = int(float_val)
            return (val, val)
        except ValueError as e:
            raise ValueError(f"Invalid range value: {value}") from e

    parts = value.split(":", 1)

    # Handle the case where value is just ":"
    if not parts[0] and not parts[1]:
        raise ValueError("Invalid range: both min and max are empty")

    min_val = None
    if parts[0]:
        try:
            float_min = float(parts[0])
            if not math.isfinite(float_min):
                raise ValueError(f"Invalid min value: {parts[0]} (infinity or NaN)")
            min_val = int(float_min)
        except ValueError as e:
            raise ValueError(f"Invalid min value: {parts[0]}") from e

    max_val = None
    if parts[1]:
        try:
            float_max = float(parts[1])
            if not math.isfinite(float_max):
                raise ValueError(f"Invalid max value: {parts[1]} (infinity or NaN)")
            max_val = int(float_max)
        except ValueError as e:
            raise ValueError(f"Invalid max value: {parts[1]}") from e

    return (min_val, max_val)


def parse_float_range(value: str) -> tuple[float | None, float | None]:
    """Parse a range string into float values, e.g. '1e3:1e6' or ':1e4'."""
    if not value or value.strip() == "":
        raise ValueError("Empty range value")

    if ":" not in value:
        try:
            float_val = float(value)
            if not math.isfinite(float_val):
                raise ValueError(f"Invalid range value: {value} (infinity or NaN)")
            return (float_val, float_val)
        except ValueError as e:
            raise ValueError(f"Invalid range value: {value}") from e

    parts = value.split(":", 1)

    if not parts[0] and not parts[1]:
        raise ValueError("Invalid range: both min and max are empty")

    min_val = None
    if parts[0]:
        try:
            min_val = float(parts[0])
            if not math.isfinite(min_val):
                raise ValueError(f"Invalid min value: {parts[0]} (infinity or NaN)")
        except ValueError as e:
            raise ValueError(f"Invalid min value: {parts[0]}") from e

    max_val = None
    if parts[1]:
        try:
            max_val = float(parts[1])
            if not math.isfinite(max_val):
                raise ValueError(f"Invalid max value: {parts[1]} (infinity or NaN)")
        except ValueError as e:
            raise ValueError(f"Invalid max value: {parts[1]}") from e

    return (min_val, max_val)


def build_filter(
    spd: bool = False,
    size: str | None = None,
    rows: str | None = None,
    cols: str | None = None,
    nnz: str | None = None,
    field: str | None = None,
    group: str | None = None,
    name: str | None = None,
    kind: str | None = None,
    structure: str | None = None,
    condition_number: str | None = None,
    matrix_norm: str | None = None,
    numerical_rank: str | None = None,
    null_space_dim: str | None = None,
    num_strong_components: str | None = None,
    num_dmperm_blocks: str | None = None,
    structural_rank: str | None = None,
    cholesky_candidate: bool | None = None,
) -> Filter | None:
    """Build a Filter object from CLI arguments."""
    filter_kwargs: dict[str, Any] = {}

    if spd:
        filter_kwargs["spd"] = True
    if field:
        filter_kwargs["field"] = field
    if group:
        filter_kwargs["group"] = group
    if name:
        filter_kwargs["name"] = name
    if kind:
        filter_kwargs["kind"] = kind
    if structure:
        filter_kwargs["structure"] = structure
    if cholesky_candidate is not None:
        filter_kwargs["cholesky_candidate"] = cholesky_candidate

    # Parse range filters (integer)
    if size:
        filter_kwargs["n_rows"] = parse_range(size)
        filter_kwargs["n_cols"] = parse_range(size)
    if rows:
        filter_kwargs["n_rows"] = parse_range(rows)
    if cols:
        filter_kwargs["n_cols"] = parse_range(cols)
    if nnz:
        filter_kwargs["nnz"] = parse_range(nnz)

    # Parse range filters for page-scraped fields (float/int)
    if condition_number:
        filter_kwargs["condition_number"] = parse_float_range(condition_number)
    if matrix_norm:
        filter_kwargs["matrix_norm"] = parse_float_range(matrix_norm)
    if numerical_rank:
        filter_kwargs["numerical_rank"] = parse_range(numerical_rank)
    if null_space_dim:
        filter_kwargs["null_space_dim"] = parse_range(null_space_dim)
    if num_strong_components:
        filter_kwargs["num_strong_components"] = parse_range(num_strong_components)
    if num_dmperm_blocks:
        filter_kwargs["num_dmperm_blocks"] = parse_range(num_dmperm_blocks)
    if structural_rank:
        filter_kwargs["structural_rank"] = parse_range(structural_rank)

    return Filter(**filter_kwargs) if filter_kwargs else None
