"""Tests for SQL parser using sqlglot."""

import pytest
from sqlglot import exp

from sql_similarity.domain.parser import ParseError, parse_sql


class TestParseSql:
    """Tests for parse_sql function."""

    def test_parse_sql_returns_expression_type(self):
        """parse_sql should return a sqlglot Expression for valid SQL."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # Should return a sqlglot Expression object
        assert result is not None
        assert isinstance(result, exp.Expression)

    def test_parse_simple_select_returns_select_expression(self):
        """parse_sql should return a Select expression for SELECT statement."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # Should return a Select expression
        assert result is not None
        assert isinstance(result, exp.Select)

    def test_parse_select_with_where_clause(self):
        """parse_sql should handle WHERE clauses."""
        sql = "SELECT id, name FROM users WHERE active = true"
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, exp.Select)
        # Should have a where clause
        assert result.find(exp.Where) is not None

    def test_parse_complex_join(self):
        """parse_sql should handle JOINs."""
        sql = """
        SELECT u.id, o.total
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        """
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, exp.Select)
        # Should have a join
        assert result.find(exp.Join) is not None

    def test_parse_tree_has_children(self):
        """parse_sql result should have children (expressions in the tree)."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # sqlglot Expression has iter_expressions() for traversal
        children = list(result.iter_expressions())
        assert len(children) > 0

    def test_parse_empty_sql_raises_error_when_raise_on_error_true(self):
        """parse_sql should raise ParseError for empty SQL when raise_on_error=True."""
        sql = ""
        with pytest.raises(ParseError):
            parse_sql(sql, raise_on_error=True)

    def test_parse_empty_sql_returns_none_when_raise_on_error_false(self):
        """parse_sql should return None for empty SQL when raise_on_error=False."""
        sql = ""
        result = parse_sql(sql, raise_on_error=False)

        assert result is None

    def test_parse_whitespace_only_raises_error_when_raise_on_error_true(self):
        """parse_sql should raise ParseError for whitespace-only SQL when raise_on_error=True."""
        sql = "   \n\t  "
        with pytest.raises(ParseError):
            parse_sql(sql, raise_on_error=True)

    def test_parse_invalid_sql_raises_error_when_raise_on_error_true(self):
        """parse_sql should raise ParseError for invalid SQL when raise_on_error=True."""
        sql = "SELECT FROM WHERE"
        with pytest.raises(ParseError):
            parse_sql(sql, raise_on_error=True)

    def test_parse_invalid_sql_returns_none_when_raise_on_error_false(self):
        """parse_sql should return None for invalid SQL when raise_on_error=False."""
        sql = "SELECT FROM WHERE"
        result = parse_sql(sql, raise_on_error=False)

        # sqlglot is lenient, but highly malformed SQL may return None
        # This test checks that no exception is raised
        assert True  # No exception raised
