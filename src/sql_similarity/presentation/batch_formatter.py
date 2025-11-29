"""Output formatters for batch comparison results."""

import csv
import json
from io import StringIO

from sql_similarity.service.batch import BatchComparisonResult


def format_batch_table(
    result: BatchComparisonResult,
    max_distance: int | None = None,
    top: int | None = None,
) -> str:
    """Format batch comparison result as a human-readable table.

    Args:
        result: BatchComparisonResult with comparisons and errors.
        max_distance: Optional filter applied (for display in header).
        top: Optional top-k filter applied (for display in header).

    Returns:
        Human-readable string with header, table, and errors section.
    """
    lines = []

    # Build header with filter info
    header_parts = [f"Batch Comparison: {result.directory}"]
    filter_info = []
    if max_distance is not None:
        filter_info.append(f"max distance: {max_distance}")
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

    if max_distance is not None or top is not None:
        lines.append(
            f"Files: {total_files} | Showing: {total_comparisons} of {total_possible} comparisons | Errors: {total_errors}"
        )
    else:
        lines.append(
            f"Files: {total_files} | Comparisons: {total_comparisons} | Errors: {total_errors}"
        )

    lines.append("")

    # Table header
    col1_width = 20
    col2_width = 20
    col3_width = 8
    col4_width = 10
    lines.append(f"{'File 1':<{col1_width}}{'File 2':<{col2_width}}{'Score':>{col3_width}}{'Distance':>{col4_width}}")
    lines.append("─" * (col1_width + col2_width + col3_width + col4_width))

    # Table rows (already sorted by score descending)
    for comparison in result.comparisons:
        file1 = comparison.file1[:col1_width - 1] if len(comparison.file1) >= col1_width else comparison.file1
        file2 = comparison.file2[:col2_width - 1] if len(comparison.file2) >= col2_width else comparison.file2
        lines.append(f"{file1:<{col1_width}}{file2:<{col2_width}}{comparison.score:>{col3_width}.3f}{comparison.distance:>{col4_width}}")

    # Errors section
    if result.errors:
        lines.append("")
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  - {error.file}: {error.error}")

    return "\n".join(lines)


def format_batch_json(
    result: BatchComparisonResult,
    max_distance: int | None = None,
    top: int | None = None,
    total_comparisons: int | None = None,
) -> str:
    """Format batch comparison result as JSON.

    Args:
        result: BatchComparisonResult with comparisons and errors.
        max_distance: Optional filter applied (for metadata).
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
                "distance": c.distance,
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
    if max_distance is not None or top is not None:
        data["max_distance_filter"] = max_distance
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
    writer.writerow(["file1", "file2", "score", "distance"])

    # Write comparison rows
    for c in result.comparisons:
        writer.writerow([c.file1, c.file2, c.score, c.distance])

    return output.getvalue().strip()
