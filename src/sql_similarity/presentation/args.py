"""Argument parser factory for CLI commands."""

import argparse

# Version from pyproject.toml
__version__ = "0.1.0"


def get_version() -> str:
    """Return the CLI version string."""
    return __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and return configured argument parser.

    Returns:
        ArgumentParser with all CLI arguments configured.
    """
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
        "-j",
        "--json",
        action="store_true",
        help="Output in JSON format",
    )
    output_format.add_argument(
        "-c",
        "--csv",
        action="store_true",
        help="Output in CSV format (batch mode only)",
    )

    parser.add_argument(
        "-m",
        "--max-edits",
        type=int,
        default=None,
        help="Only show pairs with edit count <= value (batch mode)",
    )
    parser.add_argument(
        "-t",
        "--top",
        type=int,
        default=None,
        help="Only show the N most similar pairs (batch mode)",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"sql-similarity {__version__}",
    )

    return parser
