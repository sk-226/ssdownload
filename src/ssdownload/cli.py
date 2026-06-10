"""Command-line interface for SuiteSparse Matrix Collection Downloader."""

from __future__ import annotations

import asyncio
import builtins
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .cli_utils import build_filter
from .client import SuiteSparseDownloader
from .config import Config
from .filters import Filter
from .page_scraper import PageScraper

app = typer.Typer(
    name="ssdl",
    help="Download sparse matrices from SuiteSparse Matrix Collection",
    no_args_is_help=True,
)

console = Console()


def _version_callback(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        typer.echo(f"ssdl {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Download sparse matrices from SuiteSparse Matrix Collection."""


def _build_filter_or_exit(**kwargs: Any) -> Filter | None:
    """Build a filter and report invalid CLI filter combinations."""
    try:
        return build_filter(**kwargs)
    except ValueError as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(2) from e


@app.command()
def download(
    identifier: str = typer.Argument(..., help="Matrix name or group/name"),
    group: str | None = typer.Option(
        None,
        "--group",
        "-g",
        help="Matrix group name (optional if identifier contains group/name)",
    ),
    format: str = typer.Option(
        "mat", "--format", "-f", help="File format (mat, mm, rb)"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output directory (default: current directory)"
    ),
    workers: int = typer.Option(
        4, "--workers", "-w", help="Number of concurrent workers"
    ),
    verify: bool = typer.Option(False, "--verify", help="Enable checksum verification"),
    keep_archive: bool = typer.Option(
        False,
        "--keep-archive",
        help="Keep original tar.gz files after extraction (MM/RB formats)",
    ),
    flat: bool = typer.Option(
        False,
        "--flat",
        help="Save files directly in output directory without group subdirectories",
    ),
):
    """Download a single matrix by name (auto-detects group) or by group/name."""
    downloader = SuiteSparseDownloader(
        cache_dir=output,
        workers=workers,
        verify_checksums=verify,
        extract_archives=True,  # Always extract by default
        keep_archives=keep_archive,
        flat_structure=flat,
    )

    try:
        # Parse identifier to determine if it contains group/name or just name
        if "/" in identifier and group is None:
            # Format: group/name
            group_name, matrix_name = identifier.split("/", 1)
            result = asyncio.run(downloader.download(group_name, matrix_name, format))
        elif group is not None:
            # Explicit group provided
            result = asyncio.run(downloader.download(group, identifier, format))
        else:
            # Just matrix name - search for group automatically
            console.print(f"🔍 Searching for matrix '{identifier}'...")
            result = asyncio.run(downloader.download_by_name(identifier, format))

        console.print(f"✓ Downloaded: {result}")
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
def get(
    name: str = typer.Argument(..., help="Matrix name"),
    format: str = typer.Option(
        "mat", "--format", "-f", help="File format (mat, mm, rb)"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output directory (default: current directory)"
    ),
    workers: int = typer.Option(
        4, "--workers", "-w", help="Number of concurrent workers"
    ),
    verify: bool = typer.Option(False, "--verify", help="Enable checksum verification"),
):
    """Download a matrix by name only (automatically find group)."""
    downloader = SuiteSparseDownloader(
        cache_dir=output,
        workers=workers,
        verify_checksums=verify,
    )

    try:
        console.print(f"🔍 Searching for matrix '{name}'...")
        result = asyncio.run(downloader.download_by_name(name, format))
        console.print(f"✓ Downloaded: {result}")
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
def groups():
    """List all available matrix groups."""
    downloader = SuiteSparseDownloader()

    try:
        groups = asyncio.run(downloader._get_available_groups())
        sorted_groups = sorted(groups)

        console.print(f"\n[bold]Available Groups ({len(sorted_groups)} total):[/bold]")

        # Display in columns
        from rich.columns import Columns

        group_list = [f"[cyan]{group}[/cyan]" for group in sorted_groups]
        console.print(Columns(group_list, equal=True, expand=True))

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
def bulk(
    spd: bool = typer.Option(
        False, "--spd", help="Symmetric positive definite matrices only"
    ),
    square: bool = typer.Option(False, "--square", help="Square matrices only"),
    rectangle: bool = typer.Option(
        False, "--rectangle", help="Rectangular matrices only"
    ),
    size: str | None = typer.Option(
        None, "--size", help="Matrix size range (e.g., '1000:5000')"
    ),
    rows: str | None = typer.Option(None, "--rows", help="Number of rows range"),
    cols: str | None = typer.Option(None, "--cols", help="Number of columns range"),
    nnz: str | None = typer.Option(None, "--nnz", help="Number of nonzeros range"),
    field: str | None = typer.Option(
        None, "--field", help="Field type (real, complex, integer, binary)"
    ),
    group: str | None = typer.Option(
        None, "--group", help="Matrix group/collection name"
    ),
    name: str | None = typer.Option(None, "--name", help="Matrix name pattern"),
    kind: str | None = typer.Option(None, "--kind", help="Matrix kind"),
    structure: str | None = typer.Option(None, "--structure", help="Matrix structure"),
    condition_number: str | None = typer.Option(
        None, "--cond", help="Condition number range (e.g., ':1e4' or '1e2:1e6')"
    ),
    matrix_norm: str | None = typer.Option(
        None, "--norm", help="Matrix 2-norm range (e.g., ':1e5')"
    ),
    numerical_rank: str | None = typer.Option(
        None, "--rank", help="Numerical rank range"
    ),
    null_space_dim: str | None = typer.Option(
        None, "--null-dim", help="Null space dimension range"
    ),
    num_strong_components: str | None = typer.Option(
        None, "--scc", help="Number of strongly connected components range"
    ),
    num_dmperm_blocks: str | None = typer.Option(
        None, "--dmperm-blocks", help="Number of Dmperm blocks range"
    ),
    structural_rank_opt: str | None = typer.Option(
        None, "--structural-rank", help="Structural rank range"
    ),
    cholesky: bool | None = typer.Option(
        None, "--cholesky/--no-cholesky", help="Filter by Cholesky candidate status"
    ),
    format: str = typer.Option(
        "mat", "--format", "-f", help="File format (mat, mm, rb)"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output directory (default: current directory)"
    ),
    workers: int = typer.Option(
        4, "--workers", "-w", help="Number of concurrent workers"
    ),
    max_files: int | None = typer.Option(
        None, "--max-files", help="Maximum number of files to download"
    ),
    verify: bool = typer.Option(False, "--verify", help="Enable checksum verification"),
    keep_archive: bool = typer.Option(
        False,
        "--keep-archive",
        help="Keep original tar.gz files after extraction (MM/RB formats)",
    ),
    flat: bool = typer.Option(
        False,
        "--flat",
        help="Save files directly in output directory without group subdirectories",
    ),
):
    """Download multiple matrices matching filter criteria."""
    # Build filter
    filter_obj = _build_filter_or_exit(
        spd=spd,
        square=square,
        rectangle=rectangle,
        size=size,
        rows=rows,
        cols=cols,
        nnz=nnz,
        field=field,
        group=group,
        name=name,
        kind=kind,
        structure=structure,
        condition_number=condition_number,
        matrix_norm=matrix_norm,
        numerical_rank=numerical_rank,
        null_space_dim=null_space_dim,
        num_strong_components=num_strong_components,
        num_dmperm_blocks=num_dmperm_blocks,
        structural_rank=structural_rank_opt,
        cholesky_candidate=cholesky,
    )

    downloader = SuiteSparseDownloader(
        cache_dir=output,
        workers=workers,
        verify_checksums=verify,
        extract_archives=True,  # Always extract by default
        keep_archives=keep_archive,
        flat_structure=flat,
    )

    needs_page = filter_obj is not None and filter_obj.requires_page_data()

    async def run_bulk() -> builtins.list[Path]:
        if needs_page and filter_obj is not None:
            index_downloader = SuiteSparseDownloader()
            matrices = await _list_with_page_filter(
                index_downloader, filter_obj, max_files
            )
            if not matrices:
                return []
            return await downloader.bulk_download(
                format_type=format,
                output_dir=None,
                matrices=matrices,
            )
        return await downloader.bulk_download(filter_obj, format, None, max_files)

    try:
        results = asyncio.run(run_bulk())
        console.print(f"✓ Downloaded {len(results)} matrices")
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
def list(
    spd: bool = typer.Option(
        False, "--spd", help="Symmetric positive definite matrices only"
    ),
    square: bool = typer.Option(False, "--square", help="Square matrices only"),
    rectangle: bool = typer.Option(
        False, "--rectangle", help="Rectangular matrices only"
    ),
    size: str | None = typer.Option(
        None, "--size", help="Matrix size range (e.g., '1000:5000')"
    ),
    rows: str | None = typer.Option(None, "--rows", help="Number of rows range"),
    cols: str | None = typer.Option(None, "--cols", help="Number of columns range"),
    nnz: str | None = typer.Option(None, "--nnz", help="Number of nonzeros range"),
    field: str | None = typer.Option(
        None, "--field", help="Field type (real, complex, integer, binary)"
    ),
    group: str | None = typer.Option(
        None, "--group", help="Matrix group/collection name"
    ),
    name: str | None = typer.Option(None, "--name", help="Matrix name pattern"),
    kind: str | None = typer.Option(None, "--kind", help="Matrix kind"),
    structure: str | None = typer.Option(None, "--structure", help="Matrix structure"),
    condition_number: str | None = typer.Option(
        None, "--cond", help="Condition number range (e.g., ':1e4' or '1e2:1e6')"
    ),
    matrix_norm: str | None = typer.Option(
        None, "--norm", help="Matrix 2-norm range (e.g., ':1e5')"
    ),
    numerical_rank: str | None = typer.Option(
        None, "--rank", help="Numerical rank range"
    ),
    null_space_dim: str | None = typer.Option(
        None, "--null-dim", help="Null space dimension range"
    ),
    num_strong_components: str | None = typer.Option(
        None, "--scc", help="Number of strongly connected components range"
    ),
    num_dmperm_blocks: str | None = typer.Option(
        None, "--dmperm-blocks", help="Number of Dmperm blocks range"
    ),
    structural_rank_opt: str | None = typer.Option(
        None, "--structural-rank", help="Structural rank range"
    ),
    cholesky: bool | None = typer.Option(
        None, "--cholesky/--no-cholesky", help="Filter by Cholesky candidate status"
    ),
    limit: int | None = typer.Option(
        20, "--limit", "-l", help="Maximum number of results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
):
    """List matrices matching filter criteria."""
    # Build filter
    filter_obj = _build_filter_or_exit(
        spd=spd,
        square=square,
        rectangle=rectangle,
        size=size,
        rows=rows,
        cols=cols,
        nnz=nnz,
        field=field,
        group=group,
        name=name,
        kind=kind,
        structure=structure,
        condition_number=condition_number,
        matrix_norm=matrix_norm,
        numerical_rank=numerical_rank,
        null_space_dim=null_space_dim,
        num_strong_components=num_strong_components,
        num_dmperm_blocks=num_dmperm_blocks,
        structural_rank=structural_rank_opt,
        cholesky_candidate=cholesky,
    )

    downloader = SuiteSparseDownloader()

    try:
        needs_page = filter_obj is not None and filter_obj.requires_page_data()

        if needs_page and filter_obj is not None:
            # Two-phase filtering: CSV first, then page scraping
            page_results = asyncio.run(_list_with_page_filter(downloader, filter_obj))
            total_count = len(page_results)
            if limit is not None:
                page_results = page_results[:limit]
            matrices = page_results
        else:
            matrices, total_count = downloader.list_matrices(filter_obj, limit)

        if not matrices:
            console.print("No matrices found matching criteria")
            return

        # Create table with improved title
        displayed_count = len(matrices)
        if total_count > displayed_count:
            title = f"SuiteSparse Matrices (showing {displayed_count} of {total_count} total, use --limit to see more)"
        else:
            title = f"SuiteSparse Matrices ({total_count} total)"

        table = Table(title=title)

        if verbose:
            table.add_column("Group", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Rows", justify="right")
            table.add_column("Cols", justify="right")
            table.add_column("NNZ", justify="right")
            table.add_column("Field", style="blue")
            table.add_column("SPD", justify="center")
            if needs_page:
                table.add_column("Cond#", justify="right", style="yellow")
        else:
            table.add_column("Group/Name", style="cyan")
            table.add_column("Size", justify="right")
            table.add_column("NNZ", justify="right")
            table.add_column("Field", style="blue")
            if needs_page:
                table.add_column("Cond#", justify="right", style="yellow")

        for matrix in matrices:
            group = matrix.get("group", "")
            name = matrix.get("name", "")
            rows = matrix.get("num_rows", matrix.get("rows", 0))
            cols = matrix.get("num_cols", matrix.get("cols", 0))
            nnz = matrix.get("nnz", matrix.get("nonzeros", 0))
            field = matrix.get("field", "")
            spd_flag = matrix.get("spd", False)
            cond = matrix.get("condition_number")
            cond_str = f"{cond:.2e}" if cond is not None else ""

            if verbose:
                row_data = [
                    group,
                    name,
                    str(rows),
                    str(cols),
                    str(nnz),
                    field,
                    "✓" if spd_flag else "",
                ]
                if needs_page:
                    row_data.append(cond_str)
                table.add_row(*row_data)
            else:
                size_str = f"{rows}×{cols}" if rows and cols else ""
                row_data = [
                    f"{group}/{name}",
                    size_str,
                    str(nnz) if nnz else "",
                    field,
                ]
                if needs_page:
                    row_data.append(cond_str)
                table.add_row(*row_data)

        console.print(table)

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


async def _list_with_page_filter(
    downloader: SuiteSparseDownloader,
    filter_obj: Filter,
    limit: int | None = None,
) -> builtins.list[dict[str, Any]]:
    """Two-phase filtering: CSV-based first, then page-scraping for extended fields."""
    from .filters import Filter as FilterClass

    # Phase 1: Filter by CSV fields only
    csv_filter = FilterClass(
        spd=filter_obj.spd,
        n_rows=filter_obj.n_rows,
        n_cols=filter_obj.n_cols,
        nnz=filter_obj.nnz,
        field=filter_obj.field,
        group=filter_obj.group,
        name=filter_obj.name,
        kind=filter_obj.kind,
        posdef=filter_obj.posdef,
        structure=filter_obj.structure,
    )
    csv_candidates = await downloader.find_matrices(csv_filter)

    if not csv_candidates:
        return []

    console.print(
        f"[dim]Phase 1: {len(csv_candidates)} candidates from CSV index. "
        f"Fetching page data for extended filtering...[/dim]"
    )

    # Phase 2: Enrich with page data and apply full filter
    scraper = PageScraper()
    enriched = await scraper.enrich_matrices(csv_candidates)
    results = [m for m in enriched if filter_obj.matches(m)]
    if limit is not None:
        results = results[:limit]
    return results


@app.command()
def info(
    identifier: str = typer.Argument(..., help="Matrix name or group/name"),
    group: str | None = typer.Option(
        None,
        "--group",
        "-g",
        help="Matrix group name (optional if identifier contains group/name)",
    ),
):
    """Show detailed information about a specific matrix."""
    downloader = SuiteSparseDownloader()

    try:
        # Parse identifier to determine group and name
        if "/" in identifier and group is None:
            # Format: group/name
            group_name, matrix_name = identifier.split("/", 1)
        elif group is not None:
            # Explicit group provided
            group_name, matrix_name = group, identifier
        else:
            # Just matrix name - search for it
            console.print(f"🔍 Searching for matrix '{identifier}'...")
            # Use name filter to find the matrix
            name_filter = Filter(name=identifier)
            matrices, _ = downloader.list_matrices(name_filter, limit=10)

            # Find exact match
            exact_matches = [m for m in matrices if m.get("name") == identifier]
            if not exact_matches:
                console.print(f"Matrix '{identifier}' not found")
                raise typer.Exit(1)
            elif len(exact_matches) > 1:
                console.print(f"Multiple matrices named '{identifier}' found:")
                for m in exact_matches:
                    console.print(f"  {m.get('group', '')}/{m.get('name', '')}")
                console.print(
                    "Please specify the group with --group or use group/name format"
                )
                raise typer.Exit(1)

            matrix = exact_matches[0]
            group_name = matrix.get("group", "")
            matrix_name = matrix.get("name", "")

        if "matrix" not in locals():
            # Find the specific matrix using group and name
            filter_obj = Filter(group=group_name, name=matrix_name)
            matrices, _ = downloader.list_matrices(filter_obj, limit=1)

            if not matrices:
                console.print(f"Matrix {group_name}/{matrix_name} not found")
                raise typer.Exit(1)

            matrix = matrices[0]

        # Enrich with page data
        console.print("[dim]Fetching extended info from matrix page...[/dim]")
        scraper = PageScraper()
        matrix = asyncio.run(scraper.enrich_matrix_info(matrix))

        # Display detailed information
        table = Table(title=f"Matrix Information: {group_name}/{matrix_name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        # Define clean, non-duplicate field mapping
        display_fields = [
            # Basic identification
            ("Matrix ID", matrix.get("matrix_id", "Unknown")),
            ("Group", matrix.get("group")),
            ("Name", matrix.get("name")),
            # Dimensions and structure
            ("Dimensions", f"{matrix.get('rows', 0)}×{matrix.get('cols', 0)}"),
            ("Nonzeros (NNZ)", f"{matrix.get('nnz', 0):,}"),
            ("Pattern Entries", f"{matrix.get('pattern_entries', 0):,}"),
            # Mathematical properties
            ("Symmetric", matrix.get("symmetric")),
            ("Positive Definite", matrix.get("posdef")),
            ("SPD (Symmetric Positive Definite)", matrix.get("spd")),
            (
                "Pattern Symmetry",
                f"{matrix.get('pattern_symmetry', 0) * 100:.0f}%"
                if matrix.get("pattern_symmetry") is not None
                else "Unknown",
            ),
            (
                "Numerical Symmetry",
                f"{matrix.get('numerical_symmetry', 0) * 100:.0f}%"
                if matrix.get("numerical_symmetry") is not None
                else "Unknown",
            ),
            # Field type and properties
            ("Field Type", matrix.get("field", "Unknown")),
            ("Real", matrix.get("real")),
            ("Binary", matrix.get("binary")),
            ("Complex", matrix.get("complex")),
            ("2D/3D Discretization", matrix.get("2d_3d")),
            # Problem classification
            ("Problem Type", matrix.get("kind", "Unknown")),
        ]

        # Page-scraped structural info
        page_structural_fields = [
            ("Structural Rank", matrix.get("structural_rank")),
            ("Structural Rank Full", matrix.get("structural_rank_full")),
            ("Num Dmperm Blocks", matrix.get("num_dmperm_blocks")),
            ("Strongly Connected Components", matrix.get("num_strong_components")),
            ("Num Explicit Zeros", matrix.get("num_explicit_zeros")),
            ("Cholesky Candidate", matrix.get("cholesky_candidate")),
        ]

        # Page-scraped SVD statistics
        page_svd_fields = [
            ("Matrix Norm", matrix.get("matrix_norm")),
            ("Min Singular Value", matrix.get("min_singular_value")),
            ("Condition Number", matrix.get("condition_number")),
            ("Numerical Rank", matrix.get("numerical_rank")),
            ("sprank(A)-rank(A)", matrix.get("rank_deficiency")),
            ("Null Space Dimension", matrix.get("null_space_dim")),
            ("Full Numerical Rank", matrix.get("full_numerical_rank")),
        ]

        # Page-scraped basic info
        page_basic_fields = [
            ("Date", matrix.get("date")),
            ("Author", matrix.get("author")),
            ("Editor", matrix.get("editor")),
        ]

        def format_value(label: str, value: Any) -> str | None:
            if value is None:
                return None
            if isinstance(value, bool):
                return "✓" if value else "✗"
            if isinstance(value, float):
                if label in ("Pattern Symmetry", "Numerical Symmetry"):
                    return str(value)
                return f"{value:.6e}"
            if isinstance(value, int) and not isinstance(value, bool):
                return f"{value:,}"
            return str(value)

        for label, value in display_fields:
            formatted = format_value(label, value)
            if formatted is not None:
                table.add_row(label, formatted)

        # Add a section separator and page-scraped fields if any exist
        has_structural = any(v is not None for _, v in page_structural_fields)
        has_svd = any(v is not None for _, v in page_svd_fields)
        has_basic = any(v is not None for _, v in page_basic_fields)

        if has_basic:
            table.add_row("─── Additional ───", "", style="dim")
            for label, value in page_basic_fields:
                formatted = format_value(label, value)
                if formatted is not None:
                    table.add_row(label, formatted)

        if has_structural:
            table.add_row("─── Structural ───", "", style="dim")
            for label, value in page_structural_fields:
                formatted = format_value(label, value)
                if formatted is not None:
                    table.add_row(label, formatted)

        if has_svd:
            table.add_row("─── SVD Statistics ───", "", style="dim")
            for label, value in page_svd_fields:
                formatted = format_value(label, value)
                if formatted is not None:
                    table.add_row(label, formatted)

        console.print(table)

        # Show download URLs
        console.print("\n[bold]Download URLs:[/bold]")
        for fmt in ["mat", "mm", "rb"]:
            url = Config.get_matrix_url(group_name, matrix_name, fmt)
            console.print(f"  {fmt.upper()}: {url}")

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command("clean-cache")
def clean_cache(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Clear the system cache (matrix index and page info caches)."""

    cache_dir = Config.get_default_cache_dir()
    cache_files = [
        ("CSV index cache", cache_dir / "ssstats_cache.json"),
        ("Page info cache", cache_dir / PageScraper.PAGE_CACHE_FILENAME),
    ]

    existing = [(label, f) for label, f in cache_files if f.exists()]

    if not existing:
        console.print("✓ No cache files found - cache is already clean", style="green")
        return

    # Show cache info
    total_size = 0
    for label, cache_file in existing:
        size = cache_file.stat().st_size
        total_size += size
        size_str = (
            f"{size / 1024:.1f} KB"
            if size < 1024 * 1024
            else f"{size / (1024 * 1024):.1f} MB"
        )
        console.print(f"  {label}: {cache_file} ({size_str})")

    # Confirm deletion
    if not confirm:
        should_delete = typer.confirm("Are you sure you want to clear the cache?")
        if not should_delete:
            console.print("Cache cleanup cancelled", style="yellow")
            return

    # Delete cache files
    try:
        for label, cache_file in existing:
            cache_file.unlink()
            console.print(f"✓ {label} cleared", style="green")
        console.print("Next operation will download fresh data as needed", style="dim")
    except Exception as e:
        console.print(f"✗ Error clearing cache: {e}", style="red")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
