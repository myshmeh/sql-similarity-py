"""CLI entry point for sql-similarity tool."""

import argparse
import sys

from sql_similarity.service.comparison import ComparisonService
from sql_similarity.presentation.formatter import format_human, format_json


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

    args = parser.parse_args()

    service = ComparisonService()
    result = service.compare(args.file1, args.file2)

    if args.json:
        print(format_json(result))
    else:
        print(format_human(result))

    sys.exit(0)


if __name__ == "__main__":
    main()
