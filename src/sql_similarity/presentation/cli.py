"""CLI entry point for sql-similarity tool."""

import argparse
import sys

from sql_similarity.service.comparison import (
    ComparisonService,
    FileNotFoundError,
    SQLParseError,
)
from sql_similarity.presentation.formatter import format_human, format_json

# Version from pyproject.toml
__version__ = "0.1.0"

# Exit codes per CLI interface contract
EXIT_SUCCESS = 0
EXIT_FILE_NOT_FOUND = 1
EXIT_PARSE_ERROR = 2
EXIT_INVALID_ARGS = 3


def main():
    """Main entry point for the sql-similarity CLI."""
    parser = argparse.ArgumentParser(
        prog="sql-similarity",
        description="Compare SQL files using tree edit distance",
    )
    parser.add_argument("file1", help="Path to first SQL file")
    parser.add_argument("file2", help="Path to second SQL file")
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output in JSON format",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"sql-similarity {__version__}",
    )

    args = parser.parse_args()

    try:
        service = ComparisonService()
        result = service.compare(args.file1, args.file2)

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


if __name__ == "__main__":
    main()
