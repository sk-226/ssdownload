"""CLI utility functions for SuiteSparse downloader."""

from typing import Any

from .filters import Filter


def parse_range(value: str) -> tuple[int | None, int | None]:
    """Parse a range string like '1000:5000' or ':5000' or '1000:'."""
    if ":" not in value:
        # Single value, treat as exact match
        val = int(float(value))
        return (val, val)

    parts = value.split(":", 1)
    min_val = None if not parts[0] else int(float(parts[0]))
    max_val = None if not parts[1] else int(float(parts[1]))

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
