"""CLI entry point for sql-similarity tool."""

import argparse
import os
import sys

from sql_similarity.presentation.args import create_parser
from sql_similarity.presentation.controllers import BatchController, PairController
from sql_similarity.presentation.exit_codes import ExitCode


def is_batch_mode(args: argparse.Namespace) -> bool:
    """Determine if batch mode should be used.

    Args:
        args: Parsed arguments with path1 and path2.

    Returns:
        True if path1 is a directory and path2 is None.
    """
    return os.path.isdir(args.path1) and args.path2 is None


def main() -> None:
    """Main entry point for sql-similarity CLI.

    1. Creates argument parser
    2. Parses arguments
    3. Detects mode (pair vs batch)
    4. Dispatches to appropriate controller
    5. Exits with controller's return code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Handle nonexistent path before mode detection
    if not os.path.exists(args.path1):
        if args.path2 is None:
            # Assume batch mode was intended
            print(f"Error: Directory not found: {args.path1}", file=sys.stderr)
            sys.exit(ExitCode.BATCH_DIR_NOT_FOUND)
        else:
            # Pair mode - let controller handle the error
            controller = PairController()
            sys.exit(controller.execute(args))

    # Detect mode and dispatch to appropriate controller
    if is_batch_mode(args):
        controller = BatchController()
    else:
        controller = PairController()

    sys.exit(controller.execute(args))


if __name__ == "__main__":
    main()
