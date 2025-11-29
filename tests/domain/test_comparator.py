"""Tests for tree comparator with sqlparse integration."""

import pytest
from sqlparse.sql import Statement, Token, TokenList

from sql_similarity.domain.parser import parse_sql
from sql_similarity.domain.comparator import (
    SqlparseConfig,
    compute_distance,
    compute_score,
    interpret_mapping,
    tree_size,
    EditOperation,
    ComparisonResult,
)


class TestSqlparseConfigChildren:
    """Tests for SqlparseConfig.children() method."""

    def test_children_returns_list_for_token_list(self):
        """children() should return token list for TokenList nodes."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Root Statement is a TokenList, should have children
        children = config.children(tree)
        assert isinstance(children, list)
        assert len(children) > 0

    def test_children_returns_empty_for_leaf_token(self):
        """children() should return empty list for Token (leaf node)."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Find a leaf Token (not a group)
        def find_leaf_token(node):
            if isinstance(node, TokenList):
                for child in node.tokens:
                    if not child.is_group:
                        return child
                    result = find_leaf_token(child)
                    if result:
                        return result
            return None

        leaf = find_leaf_token(tree)
        assert leaf is not None
        assert not leaf.is_group
        assert config.children(leaf) == []


class TestSqlparseConfigDelete:
    """Tests for SqlparseConfig.delete() method."""

    def test_delete_returns_uniform_cost_of_1(self):
        """delete() should return uniform cost of 1."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Should return 1 for any node
        assert config.delete(tree) == 1

    def test_delete_returns_1_for_leaf_token(self):
        """delete() should return 1 for leaf tokens too."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Find a leaf Token
        def find_leaf(node):
            if isinstance(node, TokenList):
                for child in node.tokens:
                    if not child.is_group:
                        return child
            return None

        leaf = find_leaf(tree)
        assert config.delete(leaf) == 1


class TestSqlparseConfigInsert:
    """Tests for SqlparseConfig.insert() method."""

    def test_insert_returns_uniform_cost_of_1(self):
        """insert() should return uniform cost of 1."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Should return 1 for any node
        assert config.insert(tree) == 1

    def test_insert_returns_1_for_leaf_token(self):
        """insert() should return 1 for leaf tokens too."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Find a leaf Token
        def find_leaf(node):
            if isinstance(node, TokenList):
                for child in node.tokens:
                    if not child.is_group:
                        return child
            return None

        leaf = find_leaf(tree)
        assert config.insert(leaf) == 1


class TestSqlparseConfigRename:
    """Tests for SqlparseConfig.rename() method."""

    def test_rename_returns_0_for_matching_labels(self):
        """rename() should return 0 when labels match."""
        config = SqlparseConfig()
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        # Both roots are Statement, should return 0
        assert config.rename(tree1, tree2) == 0

    def test_rename_returns_1_for_different_labels(self):
        """rename() should return 1 when labels differ."""
        config = SqlparseConfig()
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        # Find a TokenList child and a leaf Token
        def find_group_child(node):
            if isinstance(node, TokenList):
                for child in node.tokens:
                    if child.is_group:
                        return child
            return None

        def find_leaf(node):
            if isinstance(node, TokenList):
                for child in node.tokens:
                    if not child.is_group:
                        return child
            return None

        group = find_group_child(tree1)
        leaf = find_leaf(tree2)

        # Group vs leaf should have different labels
        if group and leaf:
            label1 = config._get_label(group)
            label2 = config._get_label(leaf)
            if label1 != label2:
                assert config.rename(group, leaf) == 1


class TestSqlparseConfigGetLabel:
    """Tests for SqlparseConfig._get_label() method."""

    def test_get_label_returns_class_name_for_token_list(self):
        """_get_label() should return class name for TokenList nodes."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Root is Statement, should return "Statement"
        label = config._get_label(tree)
        assert label == "Statement"

    def test_get_label_returns_normalized_value_for_leaf_tokens(self):
        """_get_label() should return normalized value for leaf Token nodes."""
        config = SqlparseConfig()
        tree = parse_sql("SELECT id FROM users")

        # Find the SELECT keyword token
        def find_select_token(node):
            if isinstance(node, TokenList):
                for child in node.tokens:
                    if not child.is_group and child.normalized == "SELECT":
                        return child
                    if child.is_group:
                        result = find_select_token(child)
                        if result:
                            return result
            return None

        select_token = find_select_token(tree)
        assert select_token is not None
        label = config._get_label(select_token)
        # Should be the actual token value, not the type
        assert label == "SELECT"


class TestComputeDistance:
    """Tests for compute_distance() function."""

    def test_compute_distance_returns_tuple(self):
        """compute_distance() should return (distance, mapping) tuple."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        result = compute_distance(tree1, tree2)

        assert isinstance(result, tuple)
        assert len(result) == 2
        distance, mapping = result
        assert isinstance(distance, (int, float))
        assert isinstance(mapping, list)

    def test_compute_distance_identical_trees_returns_zero(self):
        """compute_distance() should return 0 for identical trees."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        distance, mapping = compute_distance(tree1, tree2)

        assert distance == 0

    def test_compute_distance_different_trees_returns_positive(self):
        """compute_distance() should return positive value for different trees."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id, name FROM customers WHERE active = true")

        distance, mapping = compute_distance(tree1, tree2)

        assert distance > 0


class TestInterpretMapping:
    """Tests for interpret_mapping() function."""

    def test_interpret_mapping_returns_edit_operations(self):
        """interpret_mapping() should return list of EditOperation objects."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM users")

        distance, mapping = compute_distance(tree1, tree2)
        operations = interpret_mapping(mapping)

        assert isinstance(operations, list)
        assert all(isinstance(op, EditOperation) for op in operations)

    def test_interpret_mapping_contains_match_operations(self):
        """interpret_mapping() should include MATCH operations for matching nodes."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        distance, mapping = compute_distance(tree1, tree2)
        operations = interpret_mapping(mapping)

        # Identical trees should have only MATCH operations
        assert all(op.type == "match" for op in operations)

    def test_interpret_mapping_contains_rename_insert_delete(self):
        """interpret_mapping() should include rename/insert/delete for different trees."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        distance, mapping = compute_distance(tree1, tree2)
        operations = interpret_mapping(mapping)

        # Should have various operation types
        op_types = {op.type for op in operations}
        # At minimum should have matches (for structural similarities)
        assert "match" in op_types or "rename" in op_types


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

    def test_edit_operation_has_node_type_field(self):
        """EditOperation should have node_type field (group or token)."""
        op = EditOperation(
            type="match",
            source_node="Statement",
            target_node="Statement",
            node_type="group",
        )
        assert op.node_type == "group"

        op2 = EditOperation(
            type="match",
            source_node="SELECT",
            target_node="SELECT",
            node_type="token",
        )
        assert op2.node_type == "token"


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_comparison_result_has_distance_and_operations(self):
        """ComparisonResult should have distance and operations fields."""
        ops = [EditOperation(type="match", source_node="A", target_node="A")]
        result = ComparisonResult(distance=0, operations=ops, score=1.0)

        assert result.distance == 0
        assert result.operations == ops

    def test_comparison_result_operations_can_be_empty(self):
        """ComparisonResult operations can be empty list."""
        result = ComparisonResult(distance=0, operations=[], score=1.0)

        assert result.distance == 0
        assert result.operations == []

    def test_comparison_result_has_score_field(self):
        """ComparisonResult should have score field."""
        ops = [EditOperation(type="match", source_node="A", target_node="A")]
        result = ComparisonResult(distance=0, operations=ops, score=1.0)

        assert result.score == 1.0

    def test_comparison_result_score_can_be_fractional(self):
        """ComparisonResult score can be a fractional value."""
        result = ComparisonResult(distance=5, operations=[], score=0.847)

        assert result.score == 0.847


class TestTreeSize:
    """Tests for tree_size() function."""

    def test_tree_size_returns_positive_integer(self):
        """tree_size() should return a positive integer."""
        tree = parse_sql("SELECT id FROM users")
        size = tree_size(tree)

        assert isinstance(size, int)
        assert size > 0

    def test_tree_size_counts_all_nodes(self):
        """tree_size() should count both group and leaf token nodes."""
        tree = parse_sql("SELECT 1")
        size = tree_size(tree)

        # Should have at least: root + some tokens
        assert size > 1

    def test_tree_size_larger_for_complex_query(self):
        """tree_size() should return larger value for more complex queries."""
        simple_tree = parse_sql("SELECT 1")
        complex_tree = parse_sql("SELECT id, name FROM users WHERE active = true")

        simple_size = tree_size(simple_tree)
        complex_size = tree_size(complex_tree)

        assert complex_size > simple_size

    def test_tree_size_identical_for_identical_queries(self):
        """tree_size() should return same value for identical queries."""
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        assert tree_size(tree1) == tree_size(tree2)


class TestComputeScore:
    """Tests for compute_score() function."""

    def test_compute_score_returns_1_for_zero_distance(self):
        """compute_score() should return 1.0 when distance is 0."""
        score = compute_score(distance=0, size1=10, size2=10)
        assert score == 1.0

    def test_compute_score_returns_0_for_max_distance(self):
        """compute_score() should return 0.0 when distance equals max(size1, size2)."""
        # Max distance = max(5, 10) = 10
        score = compute_score(distance=10, size1=5, size2=10)
        assert score == 0.0

    def test_compute_score_returns_1_for_empty_trees(self):
        """compute_score() should return 1.0 when both trees are empty."""
        score = compute_score(distance=0, size1=0, size2=0)
        assert score == 1.0

    def test_compute_score_returns_fractional_value(self):
        """compute_score() should return correct fractional score."""
        # distance=5, max(10, 10)=10, score = 1 - 5/10 = 0.5
        score = compute_score(distance=5, size1=10, size2=10)
        assert score == 0.5

    def test_compute_score_uses_max_of_sizes(self):
        """compute_score() should use max(size1, size2) as denominator."""
        # distance=3, max(5, 10)=10, score = 1 - 3/10 = 0.7
        score = compute_score(distance=3, size1=5, size2=10)
        assert score == 0.7

    def test_compute_score_between_0_and_1(self):
        """compute_score() should always return value between 0 and 1."""
        # Various test cases
        assert 0.0 <= compute_score(0, 10, 10) <= 1.0
        assert 0.0 <= compute_score(5, 10, 10) <= 1.0
        assert 0.0 <= compute_score(10, 10, 10) <= 1.0
        assert 0.0 <= compute_score(3, 5, 10) <= 1.0
