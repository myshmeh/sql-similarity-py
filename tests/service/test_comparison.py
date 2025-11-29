"""Tests for ComparisonService."""

import pytest
from pathlib import Path

from sql_similarity.service.comparison import ComparisonService
from sql_similarity.domain.comparator import ComparisonResult, EditOperation


class TestComparisonServiceCompare:
    """Tests for ComparisonService.compare() method."""

    @pytest.fixture
    def service(self):
        """Create a ComparisonService instance."""
        return ComparisonService()

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_compare_returns_comparison_result(self, service, fixtures_dir):
        """compare() should return a ComparisonResult object."""
        file1 = fixtures_dir / "simple_select.sql"
        file2 = fixtures_dir / "simple_select.sql"

        result = service.compare(file1, file2)

        assert isinstance(result, ComparisonResult)

    def test_compare_identical_files_returns_zero_distance(self, service, fixtures_dir):
        """compare() should return distance 0 for identical files."""
        file1 = fixtures_dir / "simple_select.sql"
        file2 = fixtures_dir / "simple_select.sql"

        result = service.compare(file1, file2)

        assert result.distance == 0

    def test_compare_identical_files_has_only_match_operations(self, service, fixtures_dir):
        """compare() should return only MATCH operations for identical files."""
        file1 = fixtures_dir / "simple_select.sql"
        file2 = fixtures_dir / "simple_select.sql"

        result = service.compare(file1, file2)

        assert all(op.type == "match" for op in result.operations)

    def test_compare_different_files_returns_positive_distance(self, service, fixtures_dir):
        """compare() should return positive distance for different files."""
        file1 = fixtures_dir / "simple_select.sql"
        file2 = fixtures_dir / "complex_join.sql"

        result = service.compare(file1, file2)

        assert result.distance > 0

    def test_compare_different_files_has_edit_operations(self, service, fixtures_dir):
        """compare() should return edit operations for different files."""
        file1 = fixtures_dir / "simple_select.sql"
        file2 = fixtures_dir / "complex_join.sql"

        result = service.compare(file1, file2)

        assert isinstance(result.operations, list)
        assert len(result.operations) > 0
        assert all(isinstance(op, EditOperation) for op in result.operations)

    def test_compare_operations_have_valid_types(self, service, fixtures_dir):
        """compare() operations should have valid types."""
        file1 = fixtures_dir / "simple_select.sql"
        file2 = fixtures_dir / "complex_join.sql"

        result = service.compare(file1, file2)

        valid_types = {"match", "rename", "insert", "delete"}
        for op in result.operations:
            assert op.type in valid_types

    def test_compare_accepts_path_objects(self, service, fixtures_dir):
        """compare() should accept Path objects."""
        file1 = Path(fixtures_dir / "simple_select.sql")
        file2 = Path(fixtures_dir / "simple_select.sql")

        result = service.compare(file1, file2)

        assert isinstance(result, ComparisonResult)

    def test_compare_accepts_string_paths(self, service, fixtures_dir):
        """compare() should accept string paths."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = service.compare(file1, file2)

        assert isinstance(result, ComparisonResult)
