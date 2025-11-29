"""Comparison service orchestrating SQL file comparison workflow."""

from pathlib import Path
from typing import Union

from sql_similarity.domain.parser import parse_sql
from sql_similarity.domain.comparator import (
    ComparisonResult,
    compute_distance,
    interpret_mapping,
)


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
            ComparisonResult with distance and edit operations.
        """
        # Read files
        sql1 = Path(file1).read_text()
        sql2 = Path(file2).read_text()

        # Parse SQL to trees
        tree1 = parse_sql(sql1)
        tree2 = parse_sql(sql2)

        # Compute distance and mapping
        distance, mapping = compute_distance(tree1, tree2)

        # Interpret mapping to edit operations
        operations = interpret_mapping(mapping)

        return ComparisonResult(distance=distance, operations=operations)
