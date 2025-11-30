"""Output formatters for batch comparison results."""

import csv
import json
import shutil
from io import StringIO

from sql_similarity.service.batch import BatchComparisonResult


def _get_file_column_widths(result: "BatchComparisonResult") -> tuple[int, int]:
    """Calculate column widths for file names based on terminal size and content.

    Returns widths that adapt to terminal size while respecting content needs.
    """
    # Fixed columns: Score (8) + Distance (10) + some padding (4)
    fixed_width = 8 + 10 + 4

    # Get terminal width, default to 80 if unavailable
    try:
        terminal_width = shutil.get_terminal_size().columns
    except Exception:
        terminal_width = 80

    # Available space for file columns
    available = terminal_width - fixed_width

    # Minimum width for each file column
    min_width = 15

    # Calculate max filename lengths from actual data
    max_file1_len = max((len(c.file1) for c in result.comparisons), default=10) + 1
    max_file2_len = max((len(c.file2) for c in result.comparisons), default=10) + 1

    # Split available space proportionally, but cap at actual content needs
    half_available = available // 2

    col1_width = min(max(min_width, max_file1_len), half_available)
    col2_width = min(max(min_width, max_file2_len), half_available)

    # If one column needs less, give extra to the other
    if col1_width < half_available and col2_width == half_available:
        col2_width = min(max_file2_len, available - col1_width)
    elif col2_width < half_available and col1_width == half_available:
        col1_width = min(max_file1_len, available - col2_width)

    return col1_width, col2_width


def format_batch_table(
    result: BatchComparisonResult,
    max_edits: int | None = None,
    top: int | None = None,
) -> str:
    """Format batch comparison result as a human-readable table.

    Args:
        result: BatchComparisonResult with comparisons and errors.
        max_edits: Optional filter applied (for display in header).
        top: Optional top-k filter applied (for display in header).

    Returns:
        Human-readable string with header, table, and errors section.
    """
    lines = []

    # Build header with filter info
    header_parts = [f"Batch Comparison: {result.directory}"]
    filter_info = []
    if max_edits is not None:
        filter_info.append(f"max edits: {max_edits}")
    if top is not None:
        filter_info.append(f"top {top}")
    if filter_info:
        header_parts[0] += f" ({', '.join(filter_info)})"
    lines.append(header_parts[0])

    # Summary line
    total_files = len(result.files)
    total_comparisons = len(result.comparisons)
    total_errors = len(result.errors)

    # Calculate total possible comparisons for "showing X of Y" display
    valid_files = total_files - total_errors
    total_possible = (valid_files * (valid_files - 1)) // 2 if valid_files > 1 else 0

    if max_edits is not None or top is not None:
        lines.append(
            f"Files: {total_files} | Showing: {total_comparisons} of {total_possible} comparisons | Errors: {total_errors}"
        )
    else:
        lines.append(
            f"Files: {total_files} | Comparisons: {total_comparisons} | Errors: {total_errors}"
        )

    lines.append("")

    # Table header with dynamic column widths
    col1_width, col2_width = _get_file_column_widths(result)
    col3_width = 8
    col4_width = 10
    lines.append(f"{'File 1':<{col1_width}}{'File 2':<{col2_width}}{'Score':>{col3_width}}{'Edits':>{col4_width}}")
    lines.append("─" * (col1_width + col2_width + col3_width + col4_width))

    # Table rows (already sorted by score descending)
    for comparison in result.comparisons:
        file1 = comparison.file1[:col1_width - 1] if len(comparison.file1) >= col1_width else comparison.file1
        file2 = comparison.file2[:col2_width - 1] if len(comparison.file2) >= col2_width else comparison.file2
        lines.append(f"{file1:<{col1_width}}{file2:<{col2_width}}{comparison.score:>{col3_width}.3f}{comparison.edit_count:>{col4_width}}")

    # Errors section
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  - {error.file}: {error.error}")

    return "\n".join(lines)


def format_batch_json(
    result: BatchComparisonResult,
    max_edits: int | None = None,
    top: int | None = None,
    total_comparisons: int | None = None,
) -> str:
    """Format batch comparison result as JSON.

    Args:
        result: BatchComparisonResult with comparisons and errors.
        max_edits: Optional filter applied (for metadata).
        top: Optional top-k filter applied (for metadata).
        total_comparisons: Total comparisons before filtering (for metadata).

    Returns:
        JSON string with full comparison data including operations.
    """
    data = {
        "directory": result.directory,
        "total_files": len(result.files),
        "total_comparisons": total_comparisons if total_comparisons is not None else len(result.comparisons),
        "comparisons": [
            {
                "file1": c.file1,
                "file2": c.file2,
                "score": c.score,
                "edit_count": c.edit_count,
                "operations": [
                    {
                        "type": op.type,
                        "source": op.source_node,
                        "target": op.target_node,
                        "node_type": op.node_type,
                        "tree_path": op.tree_path,
                    }
                    for op in c.operations
                ],
            }
            for c in result.comparisons
        ],
        "errors": [
            {"file": e.file, "error": e.error}
            for e in result.errors
        ],
    }

    # Add filter metadata if filters were applied
    if max_edits is not None or top is not None:
        data["max_edits_filter"] = max_edits
        data["top_filter"] = top
        data["shown_comparisons"] = len(result.comparisons)

    return json.dumps(data, indent=2)


def format_batch_csv(result: BatchComparisonResult) -> str:
    """Format batch comparison result as CSV.

    Args:
        result: BatchComparisonResult with comparisons.

    Returns:
        CSV string with header and comparison rows.
    """
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")

    # Write header
    writer.writerow(["file1", "file2", "score", "edit_count"])

    # Write comparison rows
    for c in result.comparisons:
        writer.writerow([c.file1, c.file2, c.score, c.edit_count])

    return output.getvalue().strip()
