"""Tests for output formatters."""

import json
import pytest

from sql_similarity.domain.comparator import ComparisonResult, EditOperation
from sql_similarity.presentation.formatter import format_human, format_json


class TestFormatHuman:
    """Tests for format_human() function."""

    def test_format_human_includes_distance(self):
        """format_human() should include 'Tree Edit Distance: N' line."""
        result = ComparisonResult(
            distance=3,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ]
        )

        output = format_human(result)

        assert "Tree Edit Distance: 3" in output

    def test_format_human_includes_operations_header(self):
        """format_human() should include 'Operations:' header."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ]
        )

        output = format_human(result)

        assert "Operations:" in output

    def test_format_human_formats_match_operation(self):
        """format_human() should format MATCH operations correctly."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(type="match", source_node="Select_clause", target_node="Select_clause")
            ]
        )

        output = format_human(result)

        assert "MATCH:  Select_clause" in output

    def test_format_human_formats_rename_operation(self):
        """format_human() should format RENAME operations with arrow."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="rename", source_node="users", target_node="customers")
            ]
        )

        output = format_human(result)

        assert "RENAME: users -> customers" in output

    def test_format_human_formats_insert_operation(self):
        """format_human() should format INSERT operations."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="insert", source_node=None, target_node="Where_clause")
            ]
        )

        output = format_human(result)

        assert "INSERT: Where_clause" in output

    def test_format_human_formats_delete_operation(self):
        """format_human() should format DELETE operations."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="delete", source_node="Order_by_clause", target_node=None)
            ]
        )

        output = format_human(result)

        assert "DELETE: Order_by_clause" in output

    def test_format_human_handles_empty_operations(self):
        """format_human() should handle empty operations list."""
        result = ComparisonResult(distance=0, operations=[])

        output = format_human(result)

        assert "Tree Edit Distance: 0" in output
        assert "Operations:" in output


class TestFormatJson:
    """Tests for format_json() function."""

    def test_format_json_returns_valid_json(self):
        """format_json() should return valid JSON string."""
        result = ComparisonResult(
            distance=3,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ]
        )

        output = format_json(result)
        parsed = json.loads(output)

        assert isinstance(parsed, dict)

    def test_format_json_includes_distance(self):
        """format_json() should include distance field."""
        result = ComparisonResult(
            distance=5,
            operations=[]
        )

        output = format_json(result)
        parsed = json.loads(output)

        assert "distance" in parsed
        assert parsed["distance"] == 5

    def test_format_json_includes_operations_array(self):
        """format_json() should include operations array."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ]
        )

        output = format_json(result)
        parsed = json.loads(output)

        assert "operations" in parsed
        assert isinstance(parsed["operations"], list)

    def test_format_json_operation_has_type_source_target(self):
        """format_json() operations should have type, source, target fields."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ]
        )

        output = format_json(result)
        parsed = json.loads(output)
        op = parsed["operations"][0]

        assert op["type"] == "match"
        assert op["source"] == "Snowflake_file"
        assert op["target"] == "Snowflake_file"

    def test_format_json_insert_has_null_source(self):
        """format_json() INSERT operations should have null source."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="insert", source_node=None, target_node="Where_clause")
            ]
        )

        output = format_json(result)
        parsed = json.loads(output)
        op = parsed["operations"][0]

        assert op["type"] == "insert"
        assert op["source"] is None
        assert op["target"] == "Where_clause"

    def test_format_json_delete_has_null_target(self):
        """format_json() DELETE operations should have null target."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="delete", source_node="Order_by_clause", target_node=None)
            ]
        )

        output = format_json(result)
        parsed = json.loads(output)
        op = parsed["operations"][0]

        assert op["type"] == "delete"
        assert op["source"] == "Order_by_clause"
        assert op["target"] is None

    def test_format_json_handles_empty_operations(self):
        """format_json() should handle empty operations list."""
        result = ComparisonResult(distance=0, operations=[])

        output = format_json(result)
        parsed = json.loads(output)

        assert parsed["distance"] == 0
        assert parsed["operations"] == []
