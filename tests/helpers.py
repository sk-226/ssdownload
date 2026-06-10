"""Shared test helpers."""

from click import unstyle
from click.testing import Result


def plain_output(result: Result) -> str:
    """Return CLI output without ANSI styling."""
    return unstyle(result.stdout)
