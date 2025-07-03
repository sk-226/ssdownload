"""Command-line interface for SuiteSparse Matrix Collection Downloader."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from .cli_utils import build_filter
from .client import SuiteSparseDownloader
from .config import Config
from .filters import Filter

app = typer.Typer(
    name="ssdl",
    help="Download sparse matrices from SuiteSparse Matrix Collection",
    no_args_is_help=True,
)

console = Console()


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
    filter_obj = build_filter(
        spd=spd,
        size=size,
        rows=rows,
        cols=cols,
        nnz=nnz,
        field=field,
        group=group,
        name=name,
        kind=kind,
        structure=structure,
    )

    downloader = SuiteSparseDownloader(
        cache_dir=output,
        workers=workers,
        verify_checksums=verify,
        extract_archives=True,  # Always extract by default
        keep_archives=keep_archive,
        flat_structure=flat,
    )

    try:
        results = asyncio.run(
            downloader.bulk_download(filter_obj, format, None, max_files)
        )
        console.print(f"✓ Downloaded {len(results)} matrices")
    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


@app.command()
def list(
    spd: bool = typer.Option(
        False, "--spd", help="Symmetric positive definite matrices only"
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
    limit: int | None = typer.Option(
        20, "--limit", "-l", help="Maximum number of results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed information"
    ),
):
    """List matrices matching filter criteria."""
    # Build filter
    filter_obj = build_filter(
        spd=spd,
        size=size,
        rows=rows,
        cols=cols,
        nnz=nnz,
        field=field,
        group=group,
        name=name,
        kind=kind,
        structure=structure,
    )

    downloader = SuiteSparseDownloader()

    try:
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
        else:
            table.add_column("Group/Name", style="cyan")
            table.add_column("Size", justify="right")
            table.add_column("NNZ", justify="right")
            table.add_column("Field", style="blue")

        for matrix in matrices:
            group = matrix.get("group", "")
            name = matrix.get("name", "")
            rows = matrix.get("num_rows", matrix.get("rows", 0))
            cols = matrix.get("num_cols", matrix.get("cols", 0))
            nnz = matrix.get("nnz", matrix.get("nonzeros", 0))
            field = matrix.get("field", "")
            spd_flag = matrix.get("spd", False)

            if verbose:
                table.add_row(
                    group,
                    name,
                    str(rows),
                    str(cols),
                    str(nnz),
                    field,
                    "✓" if spd_flag else "",
                )
            else:
                size_str = f"{rows}×{cols}" if rows and cols else ""
                table.add_row(
                    f"{group}/{name}",
                    size_str,
                    str(nnz) if nnz else "",
                    field,
                )

        console.print(table)

    except Exception as e:
        console.print(f"✗ Error: {e}", style="red")
        raise typer.Exit(1) from e


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

        # Add rows with proper formatting
        for label, value in display_fields:
            if value is not None:
                if isinstance(value, bool):
                    formatted_value = "✓" if value else "✗"
                elif isinstance(value, int | float) and not isinstance(value, bool):
                    if isinstance(value, float) and label not in [
                        "Pattern Symmetry",
                        "Numerical Symmetry",
                    ]:
                        formatted_value = f"{value:,.0f}"
                    else:
                        formatted_value = str(value)
                else:
                    formatted_value = str(value)

                table.add_row(label, formatted_value)

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
    """Clear the system cache (matrix index cache)."""

    # Get the cache directory and cache file
    cache_dir = Config.get_default_cache_dir()
    cache_file = cache_dir / "ssstats_cache.json"

    if not cache_file.exists():
        console.print("✓ No cache file found - cache is already clean", style="green")
        return

    # Show cache info
    cache_size = cache_file.stat().st_size
    cache_size_str = (
        f"{cache_size / 1024:.1f} KB"
        if cache_size < 1024 * 1024
        else f"{cache_size / (1024 * 1024):.1f} MB"
    )

    console.print(f"Cache file: {cache_file}")
    console.print(f"Cache size: {cache_size_str}")

    # Confirm deletion
    if not confirm:
        should_delete = typer.confirm("Are you sure you want to clear the cache?")
        if not should_delete:
            console.print("Cache cleanup cancelled", style="yellow")
            return

    # Delete the cache file
    try:
        cache_file.unlink()
        console.print("✓ Cache cleared successfully", style="green")
        console.print(
            "Next matrix operation will download fresh index data", style="dim"
        )
    except Exception as e:
        console.print(f"✗ Error clearing cache: {e}", style="red")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
