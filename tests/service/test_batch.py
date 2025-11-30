"""Tests for batch comparison service."""

import pytest
from pathlib import Path

from sql_similarity.service.batch import (
    BatchComparisonResult,
    PairComparison,
    FileError,
    scan_directory,
    compare_all_pairs,
    filter_by_max_edits,
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
            edit_count=5,
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
        assert result.comparisons[0].edit_count == 5

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
            edit_count=3,
            operations=[],
            score=0.7,
        )
        assert comparison.file1 == "query1.sql"
        assert comparison.file2 == "query2.sql"
        assert comparison.edit_count == 3
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
            edit_count=1,
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
        """compare_all_pairs() should sort results by score descending (T010)."""
        # Create files with varying complexity to get different edit counts
        (tmp_path / "simple1.sql").write_text("SELECT id FROM users")
        (tmp_path / "simple2.sql").write_text("SELECT id FROM users")  # identical
        (tmp_path / "complex.sql").write_text(
            "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )

        result = compare_all_pairs(tmp_path)

        # Verify sorted by score descending (most similar first)
        scores = [c.score for c in result.comparisons]
        assert scores == sorted(scores, reverse=True)
        # First comparison should be the most similar (simple1 vs simple2)
        assert result.comparisons[0].edit_count == 0

    def test_compare_all_pairs_handles_empty_files(self, tmp_path):
        """compare_all_pairs() should handle empty SQL files gracefully.

        Note: sqlparse is a non-validating parser, so "invalid" SQL like
        'SELEC id FORM users' is still parsed (just with different structure).
        Empty files trigger the raise_on_error=True path in parse_sql.
        """
        (tmp_path / "valid.sql").write_text("SELECT id FROM users")
        (tmp_path / "empty.sql").write_text("")  # Empty SQL file

        result = compare_all_pairs(tmp_path)

        # Should have recorded the error for empty file
        assert len(result.errors) == 1
        assert result.errors[0].file == "empty.sql"
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


class TestFilterByMaxEdits:
    """Tests for filter_by_max_edits() function (T022)."""

    def test_filter_by_max_edits_keeps_matching_pairs(self):
        """filter_by_max_edits() should keep pairs within threshold."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", edit_count=3, operations=[], score=0.7),
            PairComparison(file1="a.sql", file2="c.sql", edit_count=5, operations=[], score=0.5),
            PairComparison(file1="b.sql", file2="c.sql", edit_count=10, operations=[], score=0.0),
        ]

        filtered = filter_by_max_edits(comparisons, max_edits=5)

        assert len(filtered) == 2
        assert all(c.edit_count <= 5 for c in filtered)

    def test_filter_by_max_edits_removes_exceeding_pairs(self):
        """filter_by_max_edits() should remove pairs exceeding threshold."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", edit_count=10, operations=[], score=0.0),
            PairComparison(file1="a.sql", file2="c.sql", edit_count=20, operations=[], score=0.0),
        ]

        filtered = filter_by_max_edits(comparisons, max_edits=5)

        assert len(filtered) == 0

    def test_filter_by_max_edits_includes_equal_threshold(self):
        """filter_by_max_edits() should include pairs exactly at threshold."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", edit_count=5, operations=[], score=0.5),
        ]

        filtered = filter_by_max_edits(comparisons, max_edits=5)

        assert len(filtered) == 1


class TestFilterByTop:
    """Tests for filter_by_top() function (T023)."""

    def test_filter_by_top_returns_first_n_items(self):
        """filter_by_top() should return first N items."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", edit_count=3, operations=[], score=0.7),
            PairComparison(file1="a.sql", file2="c.sql", edit_count=5, operations=[], score=0.5),
            PairComparison(file1="b.sql", file2="c.sql", edit_count=10, operations=[], score=0.0),
        ]

        filtered = filter_by_top(comparisons, top=2)

        assert len(filtered) == 2
        assert filtered[0].edit_count == 3
        assert filtered[1].edit_count == 5

    def test_filter_by_top_returns_all_if_fewer_items(self):
        """filter_by_top() should return all items if fewer than N."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", edit_count=3, operations=[], score=0.7),
        ]

        filtered = filter_by_top(comparisons, top=5)

        assert len(filtered) == 1


class TestCombinedFilters:
    """Tests for combined filters (T024)."""

    def test_combined_filters_max_edits_then_top(self):
        """Combined filters should apply max-edits first, then top."""
        comparisons = [
            PairComparison(file1="a.sql", file2="b.sql", edit_count=3, operations=[], score=0.7),
            PairComparison(file1="a.sql", file2="c.sql", edit_count=5, operations=[], score=0.5),
            PairComparison(file1="b.sql", file2="c.sql", edit_count=7, operations=[], score=0.3),
            PairComparison(file1="a.sql", file2="d.sql", edit_count=15, operations=[], score=0.0),
        ]

        # First filter by max_edits 10 (keeps 3 items)
        filtered = filter_by_max_edits(comparisons, max_edits=10)
        # Then take top 2
        filtered = filter_by_top(filtered, top=2)

        assert len(filtered) == 2
        assert filtered[0].edit_count == 3
        assert filtered[1].edit_count == 5


# ============================================================================
# US1 Enhancement: Recursive Directory Scanning Tests (T051-T054)
# ============================================================================


class TestRecursiveDirectoryScanning:
    """Tests for recursive directory scanning (T051-T054)."""

    def test_scan_directory_finds_sql_files_in_subdirectories(self, tmp_path):
        """scan_directory() should find SQL files in subdirectories (T051)."""
        # Create nested structure
        (tmp_path / "root.sql").write_text("SELECT 1")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.sql").write_text("SELECT 2")

        files = scan_directory(tmp_path)

        assert len(files) == 2
        # Should find both root and nested files
        assert "root.sql" in files
        assert "subdir/nested.sql" in files

    def test_scan_directory_returns_relative_paths(self, tmp_path):
        """scan_directory() should return relative paths for nested files (T052)."""
        # Create subdirectory with SQL file
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "daily.sql").write_text("SELECT * FROM daily")

        files = scan_directory(tmp_path)

        # Should return relative path with subdirectory prefix
        assert "reports/daily.sql" in files
        # Should NOT return just the filename
        assert "daily.sql" not in files

    def test_scan_directory_handles_deeply_nested_directories(self, tmp_path):
        """scan_directory() should find files at arbitrary depth (T053)."""
        # Create deeply nested structure: a/b/c/d/query.sql
        deep_path = tmp_path / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        (deep_path / "query.sql").write_text("SELECT 1")
        # Also add a file at root for comparison
        (tmp_path / "root.sql").write_text("SELECT 2")

        files = scan_directory(tmp_path)

        assert len(files) == 2
        assert "root.sql" in files
        assert "a/b/c/d/query.sql" in files

    def test_compare_all_pairs_works_with_files_from_different_subdirectories(self, tmp_path):
        """compare_all_pairs() should compare files across subdirectories (T054)."""
        # Create files in different locations
        (tmp_path / "root.sql").write_text("SELECT id FROM users")

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "daily.sql").write_text("SELECT id FROM users")  # Similar to root

        etl_dir = tmp_path / "etl"
        etl_dir.mkdir()
        (etl_dir / "load.sql").write_text("INSERT INTO orders SELECT * FROM staging")

        result = compare_all_pairs(tmp_path)

        # 3 files = 3 combinations
        assert len(result.comparisons) == 3

        # Check that relative paths are used in comparisons
        all_files = set()
        for comp in result.comparisons:
            all_files.add(comp.file1)
            all_files.add(comp.file2)

        assert "root.sql" in all_files
        assert "reports/daily.sql" in all_files
        assert "etl/load.sql" in all_files

    def test_scan_directory_maintains_alphabetical_sort_with_subdirs(self, tmp_path):
        """scan_directory() should sort relative paths alphabetically."""
        # Create files in various locations
        (tmp_path / "z_root.sql").write_text("SELECT 1")
        (tmp_path / "a_root.sql").write_text("SELECT 2")

        sub = tmp_path / "middle"
        sub.mkdir()
        (sub / "file.sql").write_text("SELECT 3")

        files = scan_directory(tmp_path)

        assert files == sorted(files)
        # 'a_root.sql' should come before 'middle/file.sql' before 'z_root.sql'
        assert files == ["a_root.sql", "middle/file.sql", "z_root.sql"]
