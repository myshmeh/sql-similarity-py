"""Controller for pair (two-file) comparison mode."""

import argparse
import sys

from sql_similarity.presentation.controllers.base import BaseController
from sql_similarity.presentation.exit_codes import ExitCode
from sql_similarity.presentation.formatter import format_human, format_json
from sql_similarity.service.comparison import (
    ComparisonService,
    FileNotFoundError,
    SQLParseError,
)


class PairController(BaseController):
    """Controller for pair (two-file) comparison mode.

    Handles:
    - Two-file comparison via ComparisonService
    - Human-readable and JSON output formats
    - File not found and parse error handling
    """

    def execute(self, args: argparse.Namespace) -> int:
        """Execute pair comparison and return exit code.

        Args:
            args: Parsed arguments with path1, path2, and json attributes.

        Returns:
            ExitCode value indicating success or specific error.
        """
        if args.path2 is None:
            print("Error: Two files required for pair comparison", file=sys.stderr)
            return ExitCode.INVALID_ARGS

        try:
            service = ComparisonService()
            result = service.compare(args.path1, args.path2)

            if args.json:
                print(format_json(result))
            else:
                print(format_human(result))

            return ExitCode.SUCCESS

        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return ExitCode.FILE_NOT_FOUND

        except SQLParseError as e:
            print(f"Error: {e}", file=sys.stderr)
            return ExitCode.PARSE_ERROR
