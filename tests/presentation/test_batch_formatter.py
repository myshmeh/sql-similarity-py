"""Tests for batch output formatters."""

import json
import pytest

from sql_similarity.service.batch import BatchComparisonResult, PairComparison, FileError
from sql_similarity.domain.comparator import EditOperation
from sql_similarity.presentation.batch_formatter import (
    format_batch_table,
    format_batch_json,
    format_batch_csv,
)


class TestFormatBatchJson:
    """Tests for format_batch_json() function (T037-T038)."""

    def test_format_batch_json_includes_operations_array(self):
        """format_batch_json() should include operations array (T037)."""
        operations = [
            EditOperation(
                type="match",
                source_node="Snowflake_file",
                target_node="Snowflake_file",
                node_type="rule",
                tree_path="",
            ),
            EditOperation(
                type="rename",
                source_node="users",
                target_node="customers",
                node_type="terminal",
                tree_path="Select_statement > From_clause",
            ),
        ]
        comparison = PairComparison(
            file1="a.sql",
            file2="b.sql",
            distance=1,
            operations=operations,
        )
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[comparison],
            errors=[],
        )

        json_output = format_batch_json(result)
        parsed = json.loads(json_output)

        assert "comparisons" in parsed
        assert len(parsed["comparisons"]) == 1
        assert "operations" in parsed["comparisons"][0]
        assert len(parsed["comparisons"][0]["operations"]) == 2
        # Verify operation structure
        op = parsed["comparisons"][0]["operations"][0]
        assert "type" in op
        assert "source" in op
        assert "target" in op
        assert "node_type" in op
        assert "tree_path" in op

    def test_format_batch_json_includes_filter_metadata(self):
        """format_batch_json() should include filter metadata (T038)."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[],
            errors=[],
        )

        json_output = format_batch_json(
            result, max_distance=10, top=5, total_comparisons=20
        )
        parsed = json.loads(json_output)

        assert parsed["max_distance_filter"] == 10
        assert parsed["top_filter"] == 5
        assert parsed["total_comparisons"] == 20
        assert parsed["shown_comparisons"] == 0

    def test_format_batch_json_structure(self):
        """format_batch_json() should have correct structure."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql", "c.sql"],
            comparisons=[
                PairComparison(file1="a.sql", file2="b.sql", distance=5, operations=[])
            ],
            errors=[FileError(file="invalid.sql", error="Parse error")],
        )

        json_output = format_batch_json(result)
        parsed = json.loads(json_output)

        assert parsed["directory"] == "/path/to/dir"
        assert parsed["total_files"] == 3
        assert "comparisons" in parsed
        assert "errors" in parsed
        assert parsed["errors"][0]["file"] == "invalid.sql"


class TestFormatBatchCsv:
    """Tests for format_batch_csv() function (T039-T040)."""

    def test_format_batch_csv_outputs_correct_headers(self):
        """format_batch_csv() should output correct headers (T039)."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[
                PairComparison(file1="a.sql", file2="b.sql", distance=5, operations=[])
            ],
            errors=[],
        )

        csv_output = format_batch_csv(result)
        lines = csv_output.strip().split("\n")

        assert lines[0] == "file1,file2,distance"
        assert lines[1] == "a.sql,b.sql,5"

    def test_format_batch_csv_handles_filenames_with_commas(self):
        """format_batch_csv() should handle filenames with commas (T040)."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["query,with,commas.sql", "normal.sql"],
            comparisons=[
                PairComparison(
                    file1="query,with,commas.sql",
                    file2="normal.sql",
                    distance=3,
                    operations=[],
                )
            ],
            errors=[],
        )

        csv_output = format_batch_csv(result)
        lines = csv_output.strip().split("\n")

        # The filename with commas should be properly quoted
        assert "query,with,commas.sql" in csv_output
        # Should still be parseable as CSV
        assert len(lines) == 2

    def test_format_batch_csv_empty_comparisons(self):
        """format_batch_csv() should handle empty comparisons."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql"],
            comparisons=[],
            errors=[],
        )

        csv_output = format_batch_csv(result)
        lines = csv_output.strip().split("\n")

        # Should only have header
        assert len(lines) == 1
        assert lines[0] == "file1,file2,distance"
