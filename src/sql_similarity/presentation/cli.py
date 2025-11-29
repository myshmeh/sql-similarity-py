"""CLI entry point for sql-similarity tool."""

import argparse
import os
import sys

from sql_similarity.service.comparison import (
    ComparisonService,
    FileNotFoundError,
    SQLParseError,
)
from sql_similarity.service.batch import compare_all_pairs, filter_by_max_distance, filter_by_top
from sql_similarity.presentation.formatter import format_human, format_json
from sql_similarity.presentation.batch_formatter import format_batch_table, format_batch_json, format_batch_csv

# Version from pyproject.toml
__version__ = "0.1.0"

# Exit codes per CLI interface contract (pair mode)
EXIT_SUCCESS = 0
EXIT_FILE_NOT_FOUND = 1
EXIT_PARSE_ERROR = 2
EXIT_INVALID_ARGS = 3

# Exit codes for batch mode
EXIT_BATCH_SUCCESS = 0
EXIT_BATCH_PARTIAL = 1  # Some files had errors
EXIT_BATCH_NO_FILES = 2  # No SQL files found
EXIT_BATCH_DIR_NOT_FOUND = 3  # Directory not found
EXIT_BATCH_INVALID_ARGS = 4  # Invalid arguments


def main():
    """Main entry point for the sql-similarity CLI."""
    parser = argparse.ArgumentParser(
        prog="sql-similarity",
        description="Compare SQL files using tree edit distance",
    )
    parser.add_argument(
        "path1",
        help="Path to first SQL file or directory",
    )
    parser.add_argument(
        "path2",
        nargs="?",
        default=None,
        help="Path to second SQL file (required for pair mode)",
    )
    # Output format options (mutually exclusive)
    output_format = parser.add_mutually_exclusive_group()
    output_format.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output in JSON format",
    )
    output_format.add_argument(
        "-c", "--csv",
        action="store_true",
        help="Output in CSV format (batch mode only)",
    )
    parser.add_argument(
        "-m", "--max-distance",
        type=int,
        default=None,
        help="Only show pairs with distance <= value (batch mode)",
    )
    parser.add_argument(
        "-t", "--top",
        type=int,
        default=None,
        help="Only show the N most similar pairs (batch mode)",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"sql-similarity {__version__}",
    )

    args = parser.parse_args()

    # Detect mode: directory (batch) vs files (pair)
    # Check if path exists first for proper error handling
    if not os.path.exists(args.path1):
        # If path2 is None, assume batch mode was intended
        if args.path2 is None:
            print(f"Error: Directory not found: {args.path1}", file=sys.stderr)
            sys.exit(EXIT_BATCH_DIR_NOT_FOUND)
        else:
            # Pair mode - let run_pair_mode handle the error
            run_pair_mode(args)
    elif os.path.isdir(args.path1):
        run_batch_mode(args)
    else:
        run_pair_mode(args)


def run_pair_mode(args):
    """Run pair comparison mode."""
    if args.path2 is None:
        print("Error: Two files required for pair comparison", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    try:
        service = ComparisonService()
        result = service.compare(args.path1, args.path2)

        if args.json:
            print(format_json(result))
        else:
            print(format_human(result))

        sys.exit(EXIT_SUCCESS)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_FILE_NOT_FOUND)

    except SQLParseError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(EXIT_PARSE_ERROR)


def run_batch_mode(args):
    """Run batch comparison mode for a directory."""
    directory = args.path1
    max_distance = args.max_distance
    top = args.top

    # Validate filter arguments
    if max_distance is not None and max_distance < 0:
        print("Error: --max-distance must be a non-negative integer", file=sys.stderr)
        sys.exit(EXIT_BATCH_INVALID_ARGS)

    if top is not None and top < 1:
        print("Error: --top must be a positive integer (>= 1)", file=sys.stderr)
        sys.exit(EXIT_BATCH_INVALID_ARGS)

    # Check directory exists
    if not os.path.exists(directory):
        print(f"Error: Directory not found: {directory}", file=sys.stderr)
        sys.exit(EXIT_BATCH_DIR_NOT_FOUND)

    # Run batch comparison
    result = compare_all_pairs(directory)

    # Check for no SQL files
    if not result.files:
        print(f"Error: No .sql files found in {directory}", file=sys.stderr)
        sys.exit(EXIT_BATCH_NO_FILES)

    # Apply filters (max-distance first, then top)
    filtered_comparisons = result.comparisons
    if max_distance is not None:
        filtered_comparisons = filter_by_max_distance(filtered_comparisons, max_distance)
    if top is not None:
        filtered_comparisons = filter_by_top(filtered_comparisons, top)

    # Create filtered result for output
    from sql_similarity.service.batch import BatchComparisonResult
    filtered_result = BatchComparisonResult(
        directory=result.directory,
        files=result.files,
        comparisons=filtered_comparisons,
        errors=result.errors,
    )

    # Calculate total comparisons before filtering for metadata
    total_before_filter = len(result.comparisons)

    # Output result in requested format
    if args.json:
        print(format_batch_json(
            filtered_result,
            max_distance=max_distance,
            top=top,
            total_comparisons=total_before_filter,
        ))
    elif args.csv:
        print(format_batch_csv(filtered_result))
    else:
        print(format_batch_table(filtered_result, max_distance=max_distance, top=top))

    # Determine exit code
    if result.errors:
        sys.exit(EXIT_BATCH_PARTIAL)
    else:
        sys.exit(EXIT_BATCH_SUCCESS)


if __name__ == "__main__":
    main()
