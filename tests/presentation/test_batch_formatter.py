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


class TestFormatBatchTable:
    """Tests for format_batch_table() function."""

    def test_format_batch_table_includes_score_column(self):
        """format_batch_table() should include Score column in header."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[
                PairComparison(file1="a.sql", file2="b.sql", edit_count=5, operations=[], score=0.847)
            ],
            errors=[],
        )

        output = format_batch_table(result)

        assert "Score" in output
        assert "0.847" in output

    def test_format_batch_table_score_column_formatting(self):
        """format_batch_table() should format score with 3 decimal places."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[
                PairComparison(file1="a.sql", file2="b.sql", edit_count=0, operations=[], score=1.0)
            ],
            errors=[],
        )

        output = format_batch_table(result)

        assert "1.000" in output


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
            edit_count=1,
            operations=operations,
            score=0.9,
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

    def test_format_batch_json_includes_score(self):
        """format_batch_json() should include score field in comparisons."""
        comparison = PairComparison(
            file1="a.sql",
            file2="b.sql",
            edit_count=2,
            operations=[],
            score=0.847,
        )
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[comparison],
            errors=[],
        )

        json_output = format_batch_json(result)
        parsed = json.loads(json_output)

        assert "score" in parsed["comparisons"][0]
        assert parsed["comparisons"][0]["score"] == 0.847

    def test_format_batch_json_includes_filter_metadata(self):
        """format_batch_json() should include filter metadata (T038)."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[],
            errors=[],
        )

        json_output = format_batch_json(
            result, max_edits=10, top=5, total_comparisons=20
        )
        parsed = json.loads(json_output)

        assert parsed["max_edits_filter"] == 10
        assert parsed["top_filter"] == 5
        assert parsed["total_comparisons"] == 20
        assert parsed["shown_comparisons"] == 0

    def test_format_batch_json_structure(self):
        """format_batch_json() should have correct structure."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql", "c.sql"],
            comparisons=[
                PairComparison(file1="a.sql", file2="b.sql", edit_count=5, operations=[], score=0.5)
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
        """format_batch_csv() should output correct headers including score."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["a.sql", "b.sql"],
            comparisons=[
                PairComparison(file1="a.sql", file2="b.sql", edit_count=5, operations=[], score=0.5)
            ],
            errors=[],
        )

        csv_output = format_batch_csv(result)
        lines = csv_output.strip().split("\n")

        assert lines[0] == "file1,file2,score,edit_count"
        assert lines[1] == "a.sql,b.sql,0.5,5"

    def test_format_batch_csv_handles_filenames_with_commas(self):
        """format_batch_csv() should handle filenames with commas (T040)."""
        result = BatchComparisonResult(
            directory="/path/to/dir",
            files=["query,with,commas.sql", "normal.sql"],
            comparisons=[
                PairComparison(
                    file1="query,with,commas.sql",
                    file2="normal.sql",
                    edit_count=3,
                    operations=[],
                    score=0.7,
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
        assert lines[0] == "file1,file2,score,edit_count"
