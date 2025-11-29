"""Tests for tree comparator and ANTLR4Config."""

import pytest
from antlr4.tree.Tree import TerminalNodeImpl

from sql_similarity.domain.parser import parse_sql
from sql_similarity.domain.comparator import (
    ANTLR4Config,
    compute_distance,
    compute_score,
    interpret_mapping,
    tree_size,
    EditOperation,
    ComparisonResult,
)


class TestANTLR4ConfigChildren:
    """Tests for ANTLR4Config.children() method."""

    def test_children_returns_list_for_rule_context(self):
        """children() should return child list for ParserRuleContext nodes."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Root should have children
        children = config.children(tree)
        assert isinstance(children, list)
        assert len(children) > 0

    def test_children_returns_empty_for_terminal_node(self):
        """children() should return empty list for TerminalNode."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Find a terminal node (leaf)
        def find_terminal(node):
            if isinstance(node, TerminalNodeImpl):
                return node
            for child in config.children(node):
                result = find_terminal(child)
                if result:
                    return result
            return None

        terminal = find_terminal(tree)
        assert terminal is not None
        assert config.children(terminal) == []


class TestANTLR4ConfigDelete:
    """Tests for ANTLR4Config.delete() method."""

    def test_delete_returns_uniform_cost_of_1(self):
        """delete() should return uniform cost of 1."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Should return 1 for any node
        assert config.delete(tree) == 1

    def test_delete_returns_1_for_terminal_node(self):
        """delete() should return 1 for terminal nodes too."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Find a terminal node
        def find_terminal(node):
            if isinstance(node, TerminalNodeImpl):
                return node
            for child in config.children(node):
                result = find_terminal(child)
                if result:
                    return result
            return None

        terminal = find_terminal(tree)
        assert config.delete(terminal) == 1


class TestANTLR4ConfigInsert:
    """Tests for ANTLR4Config.insert() method."""

    def test_insert_returns_uniform_cost_of_1(self):
        """insert() should return uniform cost of 1."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Should return 1 for any node
        assert config.insert(tree) == 1

    def test_insert_returns_1_for_terminal_node(self):
        """insert() should return 1 for terminal nodes too."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Find a terminal node
        def find_terminal(node):
            if isinstance(node, TerminalNodeImpl):
                return node
            for child in config.children(node):
                result = find_terminal(child)
                if result:
                    return result
            return None

        terminal = find_terminal(tree)
        assert config.insert(terminal) == 1


class TestANTLR4ConfigRename:
    """Tests for ANTLR4Config.rename() method."""

    def test_rename_returns_0_for_matching_labels(self):
        """rename() should return 0 when labels match."""
        config = ANTLR4Config()
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        # Both roots are Snowflake_file, should return 0
        assert config.rename(tree1, tree2) == 0

    def test_rename_returns_1_for_different_labels(self):
        """rename() should return 1 when labels differ."""
        config = ANTLR4Config()
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        # Find different node types
        def find_first_child(node):
            children = config.children(node)
            return children[0] if children else None

        # Get different depth nodes which will have different labels
        child1 = find_first_child(tree1)
        # Find a terminal in tree2
        def find_terminal(node):
            if isinstance(node, TerminalNodeImpl):
                return node
            for child in config.children(node):
                result = find_terminal(child)
                if result:
                    return result
            return None

        terminal2 = find_terminal(tree2)

        # Rule context vs terminal should have different labels
        if child1 and terminal2:
            # They should have different labels (one is rule name, other is token text)
            label1 = config._get_label(child1)
            label2 = config._get_label(terminal2)
            if label1 != label2:
                assert config.rename(child1, terminal2) == 1


class TestANTLR4ConfigGetLabel:
    """Tests for ANTLR4Config._get_label() method."""

    def test_get_label_returns_class_name_minus_context_for_rules(self):
        """_get_label() should return class name minus 'Context' for rule nodes."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Root is Snowflake_fileContext, should return "Snowflake_file"
        label = config._get_label(tree)
        assert label == "Snowflake_file"
        assert "Context" not in label

    def test_get_label_returns_token_text_for_terminals(self):
        """_get_label() should return token text for terminal nodes."""
        config = ANTLR4Config()
        tree = parse_sql("SELECT id FROM users")

        # Find the SELECT terminal
        def find_terminal_with_text(node, text):
            if isinstance(node, TerminalNodeImpl):
                if node.getText().upper() == text.upper():
                    return node
            for child in config.children(node):
                result = find_terminal_with_text(child, text)
                if result:
                    return result
            return None

        select_terminal = find_terminal_with_text(tree, "SELECT")
        assert select_terminal is not None
        label = config._get_label(select_terminal)
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
        """tree_size() should count both rule and terminal nodes."""
        tree = parse_sql("SELECT 1")
        size = tree_size(tree)

        # Should have at least: root + some rule nodes + terminal nodes
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
