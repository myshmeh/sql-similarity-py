"""Tests for SQL parser."""

import pytest
from sqlparse.sql import Statement

from sql_similarity.domain.parser import ParseError, parse_sql


class TestParseSql:
    """Tests for parse_sql function."""

    def test_parse_sql_returns_statement_type(self):
        """parse_sql should return a sqlparse Statement for valid SQL."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # Should return a Statement object (sqlparse)
        assert result is not None
        assert isinstance(result, Statement)

    def test_parse_simple_select_returns_parse_tree(self):
        """parse_sql should return a Statement for valid SQL."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # Should return a Statement with tokens
        assert result is not None
        assert isinstance(result, Statement)
        assert len(result.tokens) > 0

    def test_parse_select_with_where_clause(self):
        """parse_sql should handle WHERE clauses."""
        sql = "SELECT id, name FROM users WHERE active = true"
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, Statement)
        # Should have multiple tokens including WHERE
        assert len(result.tokens) > 0

    def test_parse_complex_join(self):
        """parse_sql should handle JOINs."""
        sql = """
        SELECT u.id, o.total
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        """
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, Statement)
        assert len(result.tokens) > 0

    def test_parse_tree_has_children(self):
        """parse_sql result should have children (tokens in the tree)."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # sqlparse Statement has tokens attribute
        assert len(result.tokens) > 0

    def test_parse_empty_sql_raises_error_when_raise_on_error_true(self):
        """parse_sql should raise ParseError for empty SQL when raise_on_error=True."""
        sql = ""
        with pytest.raises(ParseError):
            parse_sql(sql, raise_on_error=True)

    def test_parse_empty_sql_returns_empty_statement_when_raise_on_error_false(self):
        """parse_sql should return empty Statement for empty SQL when raise_on_error=False."""
        sql = ""
        result = parse_sql(sql, raise_on_error=False)

        assert result is not None
        assert isinstance(result, Statement)
        # Empty statement should have no meaningful tokens (or just whitespace)

    def test_parse_whitespace_only_raises_error_when_raise_on_error_true(self):
        """parse_sql should raise ParseError for whitespace-only SQL when raise_on_error=True."""
        sql = "   \n\t  "
        with pytest.raises(ParseError):
            parse_sql(sql, raise_on_error=True)
