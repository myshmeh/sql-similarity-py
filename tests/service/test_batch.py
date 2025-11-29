"""Tests for batch comparison service."""

import pytest
from pathlib import Path

from sql_similarity.service.batch import (
    BatchComparisonResult,
    PairComparison,
    FileError,
    scan_directory,
    compare_all_pairs,
    filter_by_max_distance,
    filter_by_top,
)
from sql_similarity.domain.comparator import EditOperation


class TestBatchComparisonResultDataclass:
    """Tests for BatchComparisonResult dataclass (T003)."""

    def test_can_create_batch_comparison_result(self):
        """BatchComparisonResult should be instantiable with required fields."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[],
            errors=[],
        )
        assert result.directory == "/path/to/dir"
        assert result.files == ["a.sql", "b.sql"]
        assert result.comparisons == []
        assert result.errors == []

    def test_batch_comparison_result_with_comparisons(self):
        """BatchComparisonResult should store comparisons list."""
        comparison = PairComparison(
            file1="a.sql",
            file2="b.sql",
            distance=5,
            operations=[],
            score=0.5,
        )
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[comparison],
            errors=[],
        )
        assert len(result.comparisons) == 1
        assert result.comparisons[0].distance == 5

    def test_batch_comparison_result_with_errors(self):
        """BatchComparisonResult should store errors list."""
        error = FileError(file="bad.sql", error="Parse error")
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "bad.sql"],
            comparisons=[],
            errors=[error],
        )
        assert len(result.errors) == 1
        assert result.errors[0].file == "bad.sql"


class TestPairComparisonDataclass:
    """Tests for PairComparison dataclass (T004)."""

    def test_can_create_pair_comparison(self):
        """PairComparison should be instantiable with required fields."""
        comparison = PairComparison(
            file1="query1.sql",
            file2="query2.sql",
            distance=3,
            operations=[],
            score=0.7,
        )
        assert comparison.file1 == "query1.sql"
        assert comparison.file2 == "query2.sql"
        assert comparison.distance == 3
        assert comparison.operations == []
        assert comparison.score == 0.7

    def test_pair_comparison_with_operations(self):
        """PairComparison should store operations list."""
        operation = EditOperation(
            type="rename",
            source_node="users",
            target_node="customers",
            node_type="terminal",
            tree_path="Snowflake_file > Select_statement",
        )
        comparison = PairComparison(
            file1="a.sql",
            file2="b.sql",
            distance=1,
            operations=[operation],
            score=0.9,
        )
        assert len(comparison.operations) == 1
        assert comparison.operations[0].type == "rename"


class TestFileErrorDataclass:
    """Tests for FileError dataclass (T005)."""

    def test_can_create_file_error(self):
        """FileError should be instantiable with required fields."""
        error = FileError(
            file="broken.sql",
            error="Failed to parse: line 1:0 unexpected token",
        )
        assert error.file == "broken.sql"
        assert "unexpected token" in error.error

    def test_file_error_stores_full_message(self):
        """FileError should store complete error message."""
        error_msg = "Failed to parse: line 5:10 missing FROM clause"
        error = FileError(file="invalid.sql", error=error_msg)
        assert error.error == error_msg


# ============================================================================
# US1 Tests: Compare All SQL Files in Directory
# ============================================================================


class TestScanDirectory:
    """Tests for scan_directory() function (T007-T008)."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_scan_directory_finds_sql_files(self, fixtures_dir):
        """scan_directory() should find all .sql files (T007)."""
        files = scan_directory(fixtures_dir)

        assert isinstance(files, list)
        assert len(files) > 0
        assert all(f.endswith(".sql") for f in files)

    def test_scan_directory_returns_sorted_files(self, fixtures_dir):
        """scan_directory() should return files sorted alphabetically."""
        files = scan_directory(fixtures_dir)

        assert files == sorted(files)

    def test_scan_directory_ignores_non_sql_files(self, tmp_path):
        """scan_directory() should ignore non-.sql files (T008)."""
        # Create mixed files
        (tmp_path / "query.sql").write_text("SELECT 1")
        (tmp_path / "readme.md").write_text("# README")
        (tmp_path / "data.json").write_text("{}")
        (tmp_path / "script.py").write_text("print(1)")

        files = scan_directory(tmp_path)

        assert files == ["query.sql"]

    def test_scan_directory_case_insensitive_extension(self, tmp_path):
        """scan_directory() should find .SQL and .Sql files."""
        (tmp_path / "lower.sql").write_text("SELECT 1")
        (tmp_path / "upper.SQL").write_text("SELECT 2")
        (tmp_path / "mixed.Sql").write_text("SELECT 3")

        files = scan_directory(tmp_path)

        assert len(files) == 3

    def test_scan_directory_empty_directory(self, tmp_path):
        """scan_directory() should return empty list for empty directory."""
        files = scan_directory(tmp_path)

        assert files == []


class TestCompareAllPairs:
    """Tests for compare_all_pairs() function (T009-T011)."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_compare_all_pairs_generates_correct_combinations(self, tmp_path):
        """compare_all_pairs() should generate all unique pairs (T009)."""
        # Create 3 files -> should get 3 pairs: (a,b), (a,c), (b,c)
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")
        (tmp_path / "c.sql").write_text("SELECT 3")

        result = compare_all_pairs(tmp_path)

        # 3 files = 3 combinations
        assert len(result.comparisons) == 3
        pairs = {(c.file1, c.file2) for c in result.comparisons}
        assert ("a.sql", "b.sql") in pairs
        assert ("a.sql", "c.sql") in pairs
        assert ("b.sql", "c.sql") in pairs

    def test_compare_all_pairs_returns_sorted_results(self, tmp_path):
        """compare_all_pairs() should sort results by distance ascending (T010)."""
        # Create files with varying complexity to get different distances
        (tmp_path / "simple1.sql").write_text("SELECT id FROM users")
        (tmp_path / "simple2.sql").write_text("SELECT id FROM users")  # identical
        (tmp_path / "complex.sql").write_text(
            "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )

        result = compare_all_pairs(tmp_path)

        # Verify sorted by distance ascending
        distances = [c.distance for c in result.comparisons]
        assert distances == sorted(distances)
        # First comparison should be the most similar (simple1 vs simple2)
        assert result.comparisons[0].distance == 0

    def test_compare_all_pairs_handles_parse_errors(self, tmp_path):
        """compare_all_pairs() should handle parse errors gracefully (T011)."""
        (tmp_path / "valid.sql").write_text("SELECT id FROM users")
        (tmp_path / "invalid.sql").write_text("SELEC id FORM users")  # Invalid SQL

        result = compare_all_pairs(tmp_path)

        # Should have recorded the error
        assert len(result.errors) == 1
        assert result.errors[0].file == "invalid.sql"
        # Should still have processed valid files
        assert "valid.sql" in result.files

    def test_compare_all_pairs_includes_operations(self, tmp_path):
        """compare_all_pairs() should include operations in each comparison."""
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT name FROM customers")

        result = compare_all_pairs(tmp_path)

        assert len(result.comparisons) == 1
        assert isinstance(result.comparisons[0].operations, list)
        # Should have some operations for different queries
        assert len(result.comparisons[0].operations) > 0

    def test_compare_all_pairs_with_single_file(self, tmp_path):
        """compare_all_pairs() should return empty comparisons for single file."""
        (tmp_path / "only.sql").write_text("SELECT 1")

        result = compare_all_pairs(tmp_path)

        assert result.files == ["only.sql"]
        assert result.comparisons == []
        assert result.errors == []

    def test_compare_all_pairs_returns_batch_result(self, tmp_path):
        """compare_all_pairs() should return BatchComparisonResult."""
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")

        result = compare_all_pairs(tmp_path)

        assert isinstance(result, BatchComparisonResult)
        assert result.directory == str(tmp_path)
        assert len(result.files) == 2


# ============================================================================
# US2 Tests: Filter Results
# ============================================================================


class TestFilterByMaxDistance:
    """Tests for filter_by_max_distance() function (T022)."""

    def test_filter_by_max_distance_keeps_matching_pairs(self):
        """filter_by_max_distance() should keep pairs within threshold."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", distance=3, operations=[], score=0.7),
            PairComparison(file1="a.sql", file2="c.sql", distance=5, operations=[], score=0.5),
            PairComparison(file1="b.sql", file2="c.sql", distance=10, operations=[], score=0.0),
        ]

        filtered = filter_by_max_distance(comparisons, max_distance=5)

        assert len(filtered) == 2
        assert all(c.distance <= 5 for c in filtered)

    def test_filter_by_max_distance_removes_exceeding_pairs(self):
        """filter_by_max_distance() should remove pairs exceeding threshold."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", distance=10, operations=[], score=0.0),
            PairComparison(file1="a.sql", file2="c.sql", distance=20, operations=[], score=0.0),
        ]

        filtered = filter_by_max_distance(comparisons, max_distance=5)

        assert len(filtered) == 0

    def test_filter_by_max_distance_includes_equal_threshold(self):
        """filter_by_max_distance() should include pairs exactly at threshold."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", distance=5, operations=[], score=0.5),
        ]

        filtered = filter_by_max_distance(comparisons, max_distance=5)

        assert len(filtered) == 1


class TestFilterByTop:
    """Tests for filter_by_top() function (T023)."""

    def test_filter_by_top_returns_first_n_items(self):
        """filter_by_top() should return first N items."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", distance=3, operations=[], score=0.7),
            PairComparison(file1="a.sql", file2="c.sql", distance=5, operations=[], score=0.5),
            PairComparison(file1="b.sql", file2="c.sql", distance=10, operations=[], score=0.0),
        ]

        filtered = filter_by_top(comparisons, top=2)

        assert len(filtered) == 2
        assert filtered[0].distance == 3
        assert filtered[1].distance == 5

    def test_filter_by_top_returns_all_if_fewer_items(self):
        """filter_by_top() should return all items if fewer than N."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", distance=3, operations=[], score=0.7),
        ]

        filtered = filter_by_top(comparisons, top=5)

        assert len(filtered) == 1


class TestCombinedFilters:
    """Tests for combined filters (T024)."""

    def test_combined_filters_max_distance_then_top(self):
        """Combined filters should apply max-distance first, then top."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", distance=3, operations=[], score=0.7),
            PairComparison(file1="a.sql", file2="c.sql", distance=5, operations=[], score=0.5),
            PairComparison(file1="b.sql", file2="c.sql", distance=7, operations=[], score=0.3),
            PairComparison(file1="a.sql", file2="d.sql", distance=15, operations=[], score=0.0),
        ]

        # First filter by max_distance 10 (keeps 3 items)
        filtered = filter_by_max_distance(comparisons, max_distance=10)
        # Then take top 2
        filtered = filter_by_top(filtered, top=2)

        assert len(filtered) == 2
        assert filtered[0].distance == 3
        assert filtered[1].distance == 5
