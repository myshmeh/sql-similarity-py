"""Comparison service orchestrating SQL file comparison workflow."""

from pathlib import Path
from typing import Union

from sql_similarity.domain.parser import parse_sql, ParseError
from sql_similarity.domain.comparator import ComparisonResult, compare_trees


class FileNotFoundError(Exception):
    """Exception raised when a SQL file is not found."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"File not found: {path}")


class SQLParseError(Exception):
    """Exception raised when SQL parsing fails."""

    def __init__(self, filename: str, parse_error: ParseError):
        self.filename = filename
        self.parse_error = parse_error
        super().__init__(f"Failed to parse {filename}: {parse_error}")


class ComparisonService:
    """Service for comparing two SQL files.

    Orchestrates the workflow: read files → parse → compare → return result.
    """

    def compare(
        self, file1: Union[str, Path], file2: Union[str, Path]
    ) -> ComparisonResult:
        """Compare two SQL files and return the comparison result.

        Args:
            file1: Path to first SQL file.
            file2: Path to second SQL file.

        Returns:
            ComparisonResult with edit_count and edit operations.

        Raises:
            FileNotFoundError: If either file does not exist.
            SQLParseError: If either file contains invalid SQL.
        """
        path1 = Path(file1)
        path2 = Path(file2)

        # Check files exist
        if not path1.exists():
            raise FileNotFoundError(str(file1))
        if not path2.exists():
            raise FileNotFoundError(str(file2))

        # Read files
        sql1 = path1.read_text()
        sql2 = path2.read_text()

        # Parse SQL to trees with error checking
        try:
            tree1 = parse_sql(sql1, raise_on_error=True)
        except ParseError as e:
            raise SQLParseError(path1.name, e)

        try:
            tree2 = parse_sql(sql2, raise_on_error=True)
        except ParseError as e:
            raise SQLParseError(path2.name, e)

        # Compare trees using sqlglot diff
        return compare_trees(tree1, tree2)
