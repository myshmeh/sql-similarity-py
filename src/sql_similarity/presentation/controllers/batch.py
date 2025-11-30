"""Controller for batch (directory) comparison mode."""

import argparse
import os
import sys

from sql_similarity.presentation.controllers.base import BaseController
from sql_similarity.presentation.exit_codes import ExitCode
from sql_similarity.presentation.batch_formatter import (
    format_batch_csv,
    format_batch_json,
    format_batch_table,
)
from sql_similarity.service.batch import (
    BatchComparisonResult,
    compare_all_pairs,
    filter_by_max_edits,
    filter_by_top,
)


class BatchController(BaseController):
    """Controller for batch (directory) comparison mode.

    Handles:
    - Directory scanning and pairwise comparison
    - Filtering by max_edits and top
    - Table, JSON, and CSV output formats
    - Partial success with errors
    """

    def execute(self, args: argparse.Namespace) -> int:
        """Execute batch comparison and return exit code.

        Args:
            args: Parsed arguments with path1, max_edits, top, json, csv attributes.

        Returns:
            ExitCode value indicating success or specific error.
        """
        directory = args.path1
        max_edits = args.max_edits
        top = args.top

        # Validate filter arguments
        if max_edits is not None and max_edits < 0:
            print(
                "Error: --max-edits must be a non-negative integer", file=sys.stderr
            )
            return ExitCode.BATCH_INVALID_ARGS

        if top is not None and top < 1:
            print("Error: --top must be a positive integer (>= 1)", file=sys.stderr)
            return ExitCode.BATCH_INVALID_ARGS

        # Check directory exists
        if not os.path.exists(directory):
            print(f"Error: Directory not found: {directory}", file=sys.stderr)
            return ExitCode.BATCH_DIR_NOT_FOUND

        # Run batch comparison
        result = compare_all_pairs(directory)

        # Check for no SQL files
        if not result.files:
            print(f"Error: No .sql files found in {directory}", file=sys.stderr)
            return ExitCode.BATCH_NO_FILES

        # Apply filters (max-edits first, then top)
        filtered_comparisons = result.comparisons
        if max_edits is not None:
            filtered_comparisons = filter_by_max_edits(
                filtered_comparisons, max_edits
            )
        if top is not None:
            filtered_comparisons = filter_by_top(filtered_comparisons, top)

        # Create filtered result for output
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
            print(
                format_batch_json(
                    filtered_result,
                    max_edits=max_edits,
                    top=top,
                    total_comparisons=total_before_filter,
                )
            )
        elif args.csv:
            print(format_batch_csv(filtered_result))
        else:
            print(
                format_batch_table(filtered_result, max_edits=max_edits, top=top)
            )

        # Determine exit code
        if result.errors:
            return ExitCode.BATCH_PARTIAL
        else:
            return ExitCode.BATCH_SUCCESS
