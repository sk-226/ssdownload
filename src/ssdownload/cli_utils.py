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

    # Parse range filters
    if size:
        filter_kwargs["n_rows"] = parse_range(size)
        filter_kwargs["n_cols"] = parse_range(size)
    if rows:
        filter_kwargs["n_rows"] = parse_range(rows)
    if cols:
        filter_kwargs["n_cols"] = parse_range(cols)
    if nnz:
        filter_kwargs["nnz"] = parse_range(nnz)

    return Filter(**filter_kwargs) if filter_kwargs else None
