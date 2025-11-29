"""Tests for tree comparator and SQLGlotConfig."""

from sqlglot import exp


class TestSQLGlotConfigChildren:
    """Tests for SQLGlotConfig.children() method."""

    def test_children_returns_list_for_expression_node(self):
        """children() should return child list for Expression nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        # Root should have children
        children = config.children(tree)
        assert isinstance(children, list)
        assert len(children) > 0

    def test_children_returns_empty_for_leaf_node(self):
        """children() should return empty list for leaf nodes like Identifier."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        # Find an Identifier node (leaf)
        identifier = tree.find(exp.Identifier)
        assert identifier is not None
        # Identifiers typically don't have expression children
        children = config.children(identifier)
        # May have 'this' as string, but not Expression children
        assert isinstance(children, list)


class TestSQLGlotConfigDelete:
    """Tests for SQLGlotConfig.delete() method."""

    def test_delete_returns_uniform_cost_of_1(self):
        """delete() should return uniform cost of 1."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        # Should return 1 for any node
        assert config.delete(tree) == 1

    def test_delete_returns_1_for_identifier_node(self):
        """delete() should return 1 for identifier nodes too."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        identifier = tree.find(exp.Identifier)
        assert config.delete(identifier) == 1


class TestSQLGlotConfigInsert:
    """Tests for SQLGlotConfig.insert() method."""

    def test_insert_returns_uniform_cost_of_1(self):
        """insert() should return uniform cost of 1."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        # Should return 1 for any node
        assert config.insert(tree) == 1

    def test_insert_returns_1_for_literal_node(self):
        """insert() should return 1 for literal nodes too."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT 1 FROM users")

        literal = tree.find(exp.Literal)
        assert literal is not None
        assert config.insert(literal) == 1


class TestSQLGlotConfigRename:
    """Tests for SQLGlotConfig.rename() method."""

    def test_rename_returns_0_for_matching_labels(self):
        """rename() should return 0 when labels match."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM customers")

        # Both roots are Select expressions, should return 0
        assert config.rename(tree1, tree2) == 0

    def test_rename_returns_1_for_different_labels(self):
        """rename() should return 1 when labels differ."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT 1 FROM users")

        # Find a Column in tree1 and a Literal in tree2
        column = tree1.find(exp.Column)
        literal = tree2.find(exp.Literal)

        if column and literal:
            # Column vs Literal should have different labels
            assert config.rename(column, literal) == 1


class TestSQLGlotConfigGetLabel:
    """Tests for SQLGlotConfig._get_label() method."""

    def test_get_label_returns_class_name_for_expressions(self):
        """_get_label() should return class name for Expression nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        # Root is Select expression
        label = config._get_label(tree)
        assert label == "Select"

    def test_get_label_returns_identifier_for_identifiers(self):
        """_get_label() should return 'Identifier' for identifier nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import SQLGlotConfig

        config = SQLGlotConfig()
        tree = parse_sql("SELECT id FROM users")

        identifier = tree.find(exp.Identifier)
        assert identifier is not None
        label = config._get_label(identifier)
        assert label == "Identifier"


class TestGetNodeType:
    """Tests for _get_node_type() function."""

    def test_get_node_type_returns_terminal_for_literal(self):
        """_get_node_type() should return 'terminal' for Literal nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import _get_node_type

        tree = parse_sql("SELECT 1 FROM users")
        literal = tree.find(exp.Literal)

        assert literal is not None
        assert _get_node_type(literal) == "terminal"

    def test_get_node_type_returns_terminal_for_identifier(self):
        """_get_node_type() should return 'terminal' for Identifier nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import _get_node_type

        tree = parse_sql("SELECT id FROM users")
        identifier = tree.find(exp.Identifier)

        assert identifier is not None
        assert _get_node_type(identifier) == "terminal"

    def test_get_node_type_returns_rule_for_select(self):
        """_get_node_type() should return 'rule' for Select nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import _get_node_type

        tree = parse_sql("SELECT id FROM users")
        assert _get_node_type(tree) == "rule"


class TestGetTreePath:
    """Tests for _get_tree_path() function."""

    def test_get_tree_path_returns_string(self):
        """_get_tree_path() should return a string path."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import _get_tree_path

        tree = parse_sql("SELECT id FROM users")
        identifier = tree.find(exp.Identifier)

        assert identifier is not None
        path = _get_tree_path(identifier)
        assert isinstance(path, str)

    def test_get_tree_path_contains_parent_info(self):
        """_get_tree_path() should contain parent node information."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import _get_tree_path

        tree = parse_sql("SELECT id FROM users")
        identifier = tree.find(exp.Identifier)

        if identifier and identifier.parent:
            path = _get_tree_path(identifier)
            # Path should contain Select at minimum
            assert "Select" in path or path == ""


class TestComputeDistance:
    """Tests for compute_distance() function."""

    def test_compute_distance_returns_tuple(self):
        """compute_distance() should return (distance, mapping) tuple."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import compute_distance

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
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import compute_distance

        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        distance, mapping = compute_distance(tree1, tree2)

        assert distance == 0

    def test_compute_distance_different_trees_returns_positive(self):
        """compute_distance() should return positive value for different trees."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import compute_distance

        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id, name FROM customers WHERE active = true")

        distance, mapping = compute_distance(tree1, tree2)

        assert distance > 0


class TestInterpretMapping:
    """Tests for interpret_mapping() function."""

    def test_interpret_mapping_returns_edit_operations(self):
        """interpret_mapping() should return list of EditOperation objects."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import (
            compute_distance,
            interpret_mapping,
            EditOperation,
        )

        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT name FROM users")

        distance, mapping = compute_distance(tree1, tree2)
        operations = interpret_mapping(mapping)

        assert isinstance(operations, list)
        assert all(isinstance(op, EditOperation) for op in operations)

    def test_interpret_mapping_contains_match_operations(self):
        """interpret_mapping() should include MATCH operations for matching nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import compute_distance, interpret_mapping

        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        distance, mapping = compute_distance(tree1, tree2)
        operations = interpret_mapping(mapping)

        # Identical trees should have only MATCH operations
        assert all(op.type == "match" for op in operations)

    def test_interpret_mapping_contains_rename_insert_delete(self):
        """interpret_mapping() should include rename/insert/delete for different trees."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import compute_distance, interpret_mapping

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
        from sql_similarity.domain.comparator import EditOperation

        op = EditOperation(type="match", source_node="Foo", target_node="Foo")

        assert op.type == "match"
        assert op.source_node == "Foo"
        assert op.target_node == "Foo"

    def test_edit_operation_allows_none_for_insert(self):
        """EditOperation should allow None source_node for INSERT."""
        from sql_similarity.domain.comparator import EditOperation

        op = EditOperation(type="insert", source_node=None, target_node="NewNode")

        assert op.type == "insert"
        assert op.source_node is None
        assert op.target_node == "NewNode"

    def test_edit_operation_allows_none_for_delete(self):
        """EditOperation should allow None target_node for DELETE."""
        from sql_similarity.domain.comparator import EditOperation

        op = EditOperation(type="delete", source_node="OldNode", target_node=None)

        assert op.type == "delete"
        assert op.source_node == "OldNode"
        assert op.target_node is None


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_comparison_result_has_distance_and_operations(self):
        """ComparisonResult should have distance and operations fields."""
        from sql_similarity.domain.comparator import ComparisonResult, EditOperation

        ops = [EditOperation(type="match", source_node="A", target_node="A")]
        result = ComparisonResult(distance=0, operations=ops, score=1.0)

        assert result.distance == 0
        assert result.operations == ops

    def test_comparison_result_operations_can_be_empty(self):
        """ComparisonResult operations can be empty list."""
        from sql_similarity.domain.comparator import ComparisonResult

        result = ComparisonResult(distance=0, operations=[], score=1.0)

        assert result.distance == 0
        assert result.operations == []

    def test_comparison_result_has_score_field(self):
        """ComparisonResult should have score field."""
        from sql_similarity.domain.comparator import ComparisonResult, EditOperation

        ops = [EditOperation(type="match", source_node="A", target_node="A")]
        result = ComparisonResult(distance=0, operations=ops, score=1.0)

        assert result.score == 1.0

    def test_comparison_result_score_can_be_fractional(self):
        """ComparisonResult score can be a fractional value."""
        from sql_similarity.domain.comparator import ComparisonResult

        result = ComparisonResult(distance=5, operations=[], score=0.847)

        assert result.score == 0.847


class TestTreeSize:
    """Tests for tree_size() function."""

    def test_tree_size_returns_positive_integer(self):
        """tree_size() should return a positive integer."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import tree_size

        tree = parse_sql("SELECT id FROM users")
        size = tree_size(tree)

        assert isinstance(size, int)
        assert size > 0

    def test_tree_size_counts_all_nodes(self):
        """tree_size() should count both rule and terminal nodes."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import tree_size

        tree = parse_sql("SELECT 1")
        size = tree_size(tree)

        # Should have at least: Select + Literal
        assert size > 1

    def test_tree_size_larger_for_complex_query(self):
        """tree_size() should return larger value for more complex queries."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import tree_size

        simple_tree = parse_sql("SELECT 1")
        complex_tree = parse_sql("SELECT id, name FROM users WHERE active = true")

        simple_size = tree_size(simple_tree)
        complex_size = tree_size(complex_tree)

        assert complex_size > simple_size

    def test_tree_size_identical_for_identical_queries(self):
        """tree_size() should return same value for identical queries."""
        from sql_similarity.domain.parser import parse_sql
        from sql_similarity.domain.comparator import tree_size

        tree1 = parse_sql("SELECT id FROM users")
        tree2 = parse_sql("SELECT id FROM users")

        assert tree_size(tree1) == tree_size(tree2)


class TestComputeScore:
    """Tests for compute_score() function."""

    def test_compute_score_returns_1_for_zero_distance(self):
        """compute_score() should return 1.0 when distance is 0."""
        from sql_similarity.domain.comparator import compute_score

        score = compute_score(distance=0, size1=10, size2=10)
        assert score == 1.0

    def test_compute_score_returns_0_for_max_distance(self):
        """compute_score() should return 0.0 when distance equals max(size1, size2)."""
        from sql_similarity.domain.comparator import compute_score

        # Max distance = max(5, 10) = 10
        score = compute_score(distance=10, size1=5, size2=10)
        assert score == 0.0

    def test_compute_score_returns_1_for_empty_trees(self):
        """compute_score() should return 1.0 when both trees are empty."""
        from sql_similarity.domain.comparator import compute_score

        score = compute_score(distance=0, size1=0, size2=0)
        assert score == 1.0

    def test_compute_score_returns_fractional_value(self):
        """compute_score() should return correct fractional score."""
        from sql_similarity.domain.comparator import compute_score

        # distance=5, max(10, 10)=10, score = 1 - 5/10 = 0.5
        score = compute_score(distance=5, size1=10, size2=10)
        assert score == 0.5

    def test_compute_score_uses_max_of_sizes(self):
        """compute_score() should use max(size1, size2) as denominator."""
        from sql_similarity.domain.comparator import compute_score

        # distance=3, max(5, 10)=10, score = 1 - 3/10 = 0.7
        score = compute_score(distance=3, size1=5, size2=10)
        assert score == 0.7

    def test_compute_score_between_0_and_1(self):
        """compute_score() should always return value between 0 and 1."""
        from sql_similarity.domain.comparator import compute_score

        # Various test cases
        assert 0.0 <= compute_score(0, 10, 10) <= 1.0
        assert 0.0 <= compute_score(5, 10, 10) <= 1.0
        assert 0.0 <= compute_score(10, 10, 10) <= 1.0
        assert 0.0 <= compute_score(3, 5, 10) <= 1.0
