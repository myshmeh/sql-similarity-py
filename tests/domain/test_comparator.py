"""Tests for tree comparator using sqlglot diff."""

import pytest
from sqlglot import exp

from sql_similarity.domain.parser import parse_sql
from sql_similarity.domain.comparator import (
    compare_trees,
    compute_score,
    interpret_edits,
    count_nodes,
    EditOperation,
    ComparisonResult,
)


class TestCompareTrees:
    """Tests for compare_trees() function."""

    def test_compare_trees_returns_comparison_result(self):
        """compare_trees() should return a ComparisonResult."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        result = compare_trees(tree1, tree2)

        assert isinstance(result, ComparisonResult)
        assert hasattr(result, "edit_count")
        assert hasattr(result, "operations")
        assert hasattr(result, "score")

    def test_compare_trees_identical_returns_score_1(self):
        """compare_trees() should return score 1.0 for identical trees."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        result = compare_trees(tree1, tree2)

        assert result.score == 1.0
        assert result.edit_count == 0

    def test_compare_trees_different_returns_score_less_than_1(self):
        """compare_trees() should return score < 1.0 for different trees."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id, name FROM customers WHERE active = true")

        result = compare_trees(tree1, tree2)

        assert result.score < 1.0
        assert result.edit_count > 0

    def test_compare_trees_both_none_returns_score_1(self):
        """compare_trees() should return score 1.0 when both trees are None."""
        result = compare_trees(None, None)

        assert result.score == 1.0
        assert result.edit_count == 0
        assert result.operations == []


class TestInterpretEdits:
    """Tests for interpret_edits() function."""

    def test_interpret_edits_returns_edit_operations(self):
        """interpret_edits() should return list of EditOperation objects."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM users")

        result = compare_trees(tree1, tree2)
        operations = result.operations

        assert isinstance(operations, list)
        assert all(isinstance(op, EditOperation) for op in operations)

    def test_interpret_edits_contains_match_operations_for_identical(self):
        """interpret_edits() should include match operations for identical nodes."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        result = compare_trees(tree1, tree2)

        # Identical trees should have only MATCH operations
        assert all(op.type == "match" for op in result.operations)

    def test_interpret_edits_contains_various_operation_types(self):
        """interpret_edits() should include various operation types for different trees."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        result = compare_trees(tree1, tree2)

        # Should have various operation types
        op_types = {op.type for op in result.operations}
        # At minimum should have some operations
        assert len(op_types) > 0


class TestEditOperation:
    """Tests for EditOperation dataclass."""

    def test_edit_operation_has_required_fields(self):
        """EditOperation should have type, source_node, target_node fields."""
        op = EditOperation(type="match", source_node="Foo", target_node="Foo")

        assert op.type == "match"
        assert op.source_node == "Foo"
        assert op.target_node == "Foo"

    def test_edit_operation_allows_none_for_insert(self):
        """EditOperation should allow None source_node for INSERT."""
        op = EditOperation(type="insert", source_node=None, target_node="NewNode")

        assert op.type == "insert"
        assert op.source_node is None
        assert op.target_node == "NewNode"

    def test_edit_operation_allows_none_for_delete(self):
        """EditOperation should allow None target_node for DELETE."""
        op = EditOperation(type="delete", source_node="OldNode", target_node=None)

        assert op.type == "delete"
        assert op.source_node == "OldNode"
        assert op.target_node is None

    def test_edit_operation_supports_move_type(self):
        """EditOperation should support 'move' operation type."""
        op = EditOperation(type="move", source_node="Column", target_node="Column")

        assert op.type == "move"

    def test_edit_operation_has_node_type_field(self):
        """EditOperation should have node_type field."""
        op = EditOperation(
            type="match",
            source_node="Select",
            target_node="Select",
            node_type="Select",
        )
        assert op.node_type == "Select"


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_comparison_result_has_edit_count_and_operations(self):
        """ComparisonResult should have edit_count and operations fields."""
        ops = [EditOperation(type="match", source_node="A", target_node="A")]
        result = ComparisonResult(edit_count=0, operations=ops, score=1.0)

        assert result.edit_count == 0
        assert result.operations == ops

    def test_comparison_result_operations_can_be_empty(self):
        """ComparisonResult operations can be empty list."""
        result = ComparisonResult(edit_count=0, operations=[], score=1.0)

        assert result.edit_count == 0
        assert result.operations == []

    def test_comparison_result_has_score_field(self):
        """ComparisonResult should have score field."""
        ops = [EditOperation(type="match", source_node="A", target_node="A")]
        result = ComparisonResult(edit_count=0, operations=ops, score=1.0)

        assert result.score == 1.0

    def test_comparison_result_score_can_be_fractional(self):
        """ComparisonResult score can be a fractional value."""
        result = ComparisonResult(edit_count=5, operations=[], score=0.847)

        assert result.score == 0.847


class TestCountNodes:
    """Tests for count_nodes() function."""

    def test_count_nodes_returns_positive_integer(self):
        """count_nodes() should return a positive integer."""
        tree = parse_sql("SELECT id FROM users")
        size = count_nodes(tree)

        assert isinstance(size, int)
        assert size > 0

    def test_count_nodes_counts_all_nodes(self):
        """count_nodes() should count all nodes in expression tree."""
        tree = parse_sql("SELECT 1")
        size = count_nodes(tree)

        # Should have at least: root + some child expressions
        assert size > 1

    def test_count_nodes_larger_for_complex_query(self):
        """count_nodes() should return larger value for more complex queries."""
        simple_tree = parse_sql("SELECT 1")
        complex_tree = parse_sql("SELECT id, name FROM users WHERE active = true")

        simple_size = count_nodes(simple_tree)
        complex_size = count_nodes(complex_tree)

        assert complex_size > simple_size

    def test_count_nodes_identical_for_identical_queries(self):
        """count_nodes() should return same value for identical queries."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        assert count_nodes(tree1) == count_nodes(tree2)

    def test_count_nodes_returns_0_for_none(self):
        """count_nodes() should return 0 for None input."""
        size = count_nodes(None)

        assert size == 0


class TestComputeScore:
    """Tests for compute_score() function."""

    def test_compute_score_returns_1_for_all_keeps(self):
        """compute_score() should return 1.0 when all operations are keeps."""
        score = compute_score(keeps=10, total=10)
        assert score == 1.0

    def test_compute_score_returns_0_for_no_keeps(self):
        """compute_score() should return 0.0 when no keeps."""
        score = compute_score(keeps=0, total=10)
        assert score == 0.0

    def test_compute_score_returns_1_for_empty(self):
        """compute_score() should return 1.0 when total is 0."""
        score = compute_score(keeps=0, total=0)
        assert score == 1.0

    def test_compute_score_returns_fractional_value(self):
        """compute_score() should return correct fractional score."""
        # keeps=5, total=10, score = 5/10 = 0.5
        score = compute_score(keeps=5, total=10)
        assert score == 0.5

    def test_compute_score_between_0_and_1(self):
        """compute_score() should always return value between 0 and 1."""
        assert 0.0 <= compute_score(0, 10) <= 1.0
        assert 0.0 <= compute_score(5, 10) <= 1.0
        assert 0.0 <= compute_score(10, 10) <= 1.0
        assert 0.0 <= compute_score(3, 10) <= 1.0
