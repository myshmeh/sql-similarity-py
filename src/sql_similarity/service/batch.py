"""Batch comparison service for directory-wide SQL file comparison."""

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Union

from sql_similarity.domain.comparator import EditOperation, compute_distance, interpret_mapping
from sql_similarity.domain.parser import parse_sql, ParseError


@dataclass
class FileError:
    """Error information for a file that failed to process.

    Attributes:
        file: Path to the file (relative to directory).
        error: Error message.
    """

    file: str
    error: str


@dataclass
class PairComparison:
    """Result of comparing two SQL files.

    Attributes:
        file1: Path to first file (relative to directory).
        file2: Path to second file (relative to directory).
        distance: Tree edit distance between the files.
        operations: List of edit operations (aligns with original command output).
    """

    file1: str
    file2: str
    distance: int
    operations: list[EditOperation]


@dataclass
class BatchComparisonResult:
    """Result of batch comparison across a directory.

    Attributes:
        directory: Path to the scanned directory.
        files: List of SQL files found.
        comparisons: List of pairwise comparison results.
        errors: List of files that failed to parse.
    """

    directory: str
    files: list[str]
    comparisons: list[PairComparison]
    errors: list[FileError]


def scan_directory(directory: Union[str, Path]) -> list[str]:
    """Scan a directory for SQL files.

    Args:
        directory: Path to directory to scan.

    Returns:
        List of SQL filenames (not full paths), sorted alphabetically.
        Only files with .sql extension (case-insensitive) are included.
    """
    dir_path = Path(directory)
    sql_files = []

    for file_path in dir_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".sql":
            sql_files.append(file_path.name)

    return sorted(sql_files)


def compare_all_pairs(directory: Union[str, Path]) -> BatchComparisonResult:
    """Compare all pairs of SQL files in a directory.

    Args:
        directory: Path to directory containing SQL files.

    Returns:
        BatchComparisonResult with all pairwise comparisons sorted by distance.
    """
    dir_path = Path(directory)
    files = scan_directory(dir_path)
    errors: list[FileError] = []
    parsed_trees: dict[str, object] = {}

    # Parse all files first, collecting errors
    for filename in files:
        file_path = dir_path / filename
        try:
            sql_content = file_path.read_text()
            tree = parse_sql(sql_content, raise_on_error=True)
            parsed_trees[filename] = tree
        except ParseError as e:
            errors.append(FileError(file=filename, error=str(e)))

    # Generate all unique pairs from successfully parsed files
    valid_files = list(parsed_trees.keys())
    comparisons: list[PairComparison] = []

    for file1, file2 in combinations(sorted(valid_files), 2):
        tree1 = parsed_trees[file1]
        tree2 = parsed_trees[file2]

        distance, mapping = compute_distance(tree1, tree2)
        operations = interpret_mapping(mapping)

        comparisons.append(
            PairComparison(
                file1=file1,
                file2=file2,
                distance=distance,
                operations=operations,
            )
        )

    # Sort by distance ascending (most similar first)
    comparisons.sort(key=lambda c: c.distance)

    return BatchComparisonResult(
        directory=str(directory),
        files=files,
        comparisons=comparisons,
        errors=errors,
    )


def filter_by_max_distance(
    comparisons: list[PairComparison], max_distance: int
) -> list[PairComparison]:
    """Filter comparisons to only include those within a distance threshold.

    Args:
        comparisons: List of PairComparison objects.
        max_distance: Maximum distance to include (inclusive).

    Returns:
        Filtered list of comparisons with distance <= max_distance.
    """
    return [c for c in comparisons if c.distance <= max_distance]


def filter_by_top(
    comparisons: list[PairComparison], top: int
) -> list[PairComparison]:
    """Filter comparisons to only include the top N most similar pairs.

    Args:
        comparisons: List of PairComparison objects (should already be sorted).
        top: Number of top pairs to return.

    Returns:
        First N comparisons from the list.
    """
    return comparisons[:top]
