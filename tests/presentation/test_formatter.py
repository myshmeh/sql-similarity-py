"""Tests for output formatters."""

import json
import pytest

from sql_similarity.domain.comparator import ComparisonResult, EditOperation
from sql_similarity.presentation.formatter import format_human, format_json


class TestFormatHuman:
    """Tests for format_human() function."""

    def test_format_human_includes_score(self):
        """format_human() should include 'Similarity Score: X.XXX' line."""
        result = ComparisonResult(
            distance=3,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ],
            score=0.847
        )

        output = format_human(result)

        assert "Similarity Score: 0.847" in output

    def test_format_human_includes_distance(self):
        """format_human() should include 'Tree Edit Distance: N' line."""
        result = ComparisonResult(
            distance=3,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ],
            score=0.847
        )

        output = format_human(result)

        assert "Tree Edit Distance: 3" in output

    def test_format_human_includes_operations_header(self):
        """format_human() should include 'Operations:' header."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(type="match", source_node="Snowflake_file", target_node="Snowflake_file")
            ],
            score=1.0
        )

        output = format_human(result)

        assert "Operations:" in output

    def test_format_human_formats_match_operation(self):
        """format_human() should format MATCH operations correctly."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(type="match", source_node="Select_clause", target_node="Select_clause")
            ],
            score=1.0
        )

        output = format_human(result)

        assert "MATCH:  Select_clause" in output

    def test_format_human_formats_rename_operation(self):
        """format_human() should format RENAME operations with arrow."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="rename", source_node="users", target_node="customers")
            ],
            score=0.9
        )

        output = format_human(result)

        assert "RENAME: users -> customers" in output

    def test_format_human_formats_insert_operation(self):
        """format_human() should format INSERT operations."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="insert", source_node=None, target_node="Where_clause")
            ],
            score=0.9
        )

        output = format_human(result)

        assert "INSERT: Where_clause" in output

    def test_format_human_formats_delete_operation(self):
        """format_human() should format DELETE operations."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(type="delete", source_node="Order_by_clause", target_node=None)
            ],
            score=0.9
        )

        output = format_human(result)

        assert "DELETE: Order_by_clause" in output

    def test_format_human_handles_empty_operations(self):
        """format_human() should handle empty operations list."""
        result = ComparisonResult(distance=0, operations=[], score=1.0)

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
            ],
            score=0.847
        )

        output = format_json(result)
        parsed = json.loads(output)

        assert isinstance(parsed, dict)

    def test_format_json_includes_score(self):
        """format_json() should include score field."""
        result = ComparisonResult(
            distance=5,
            operations=[],
            score=0.5
        )

        output = format_json(result)
        parsed = json.loads(output)

        assert "score" in parsed
        assert parsed["score"] == 0.5

    def test_format_json_includes_distance(self):
        """format_json() should include distance field."""
        result = ComparisonResult(
            distance=5,
            operations=[],
            score=0.5
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
            ],
            score=1.0
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
            ],
            score=1.0
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
            ],
            score=0.9
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
            ],
            score=0.9
        )

        output = format_json(result)
        parsed = json.loads(output)
        op = parsed["operations"][0]

        assert op["type"] == "delete"
        assert op["source"] == "Order_by_clause"
        assert op["target"] is None

    def test_format_json_handles_empty_operations(self):
        """format_json() should handle empty operations list."""
        result = ComparisonResult(distance=0, operations=[], score=1.0)

        output = format_json(result)
        parsed = json.loads(output)

        assert parsed["distance"] == 0
        assert parsed["operations"] == []


class TestDetailedOperationFormatting:
    """Tests for detailed operation formatting with node_type and tree_path (US2)."""

    def test_format_human_includes_node_type(self):
        """format_human() should include node type in detailed output."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(
                    type="rename",
                    source_node="users",
                    target_node="customers",
                    node_type="terminal",
                    tree_path="Select_statement > From_clause > Object_ref"
                )
            ],
            score=0.9
        )

        output = format_human(result)

        assert "terminal" in output.lower() or "TERMINAL" in output

    def test_format_human_includes_tree_path(self):
        """format_human() should include tree path in detailed output."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(
                    type="insert",
                    source_node=None,
                    target_node="Where_clause",
                    node_type="rule",
                    tree_path="Select_statement > Select_optional_clauses"
                )
            ],
            score=0.9
        )

        output = format_human(result)

        assert "Select_statement" in output

    def test_format_json_includes_node_type(self):
        """format_json() should include node_type field in operations."""
        result = ComparisonResult(
            distance=1,
            operations=[
                EditOperation(
                    type="delete",
                    source_node="Order_by_clause",
                    target_node=None,
                    node_type="rule",
                    tree_path="Select_statement > Select_optional_clauses"
                )
            ],
            score=0.9
        )

        output = format_json(result)
        parsed = json.loads(output)
        op = parsed["operations"][0]

        assert "node_type" in op
        assert op["node_type"] == "rule"

    def test_format_json_includes_tree_path(self):
        """format_json() should include tree_path field in operations."""
        result = ComparisonResult(
            distance=0,
            operations=[
                EditOperation(
                    type="match",
                    source_node="Select_clause",
                    target_node="Select_clause",
                    node_type="rule",
                    tree_path="Select_statement"
                )
            ],
            score=1.0
        )

        output = format_json(result)
        parsed = json.loads(output)
        op = parsed["operations"][0]

        assert "tree_path" in op
        assert op["tree_path"] == "Select_statement"

    def test_edit_operation_has_node_type_field(self):
        """EditOperation should have node_type field."""
        op = EditOperation(
            type="match",
            source_node="Foo",
            target_node="Foo",
            node_type="rule",
            tree_path="Root"
        )

        assert op.node_type == "rule"

    def test_edit_operation_has_tree_path_field(self):
        """EditOperation should have tree_path field."""
        op = EditOperation(
            type="match",
            source_node="Foo",
            target_node="Foo",
            node_type="rule",
            tree_path="Root > Parent"
        )

        assert op.tree_path == "Root > Parent"

    def test_edit_operation_node_type_defaults_to_none(self):
        """EditOperation node_type should default to None for backwards compatibility."""
        op = EditOperation(
            type="match",
            source_node="Foo",
            target_node="Foo"
        )

        assert op.node_type is None

    def test_edit_operation_tree_path_defaults_to_none(self):
        """EditOperation tree_path should default to None for backwards compatibility."""
        op = EditOperation(
            type="match",
            source_node="Foo",
            target_node="Foo"
        )

        assert op.tree_path is None
