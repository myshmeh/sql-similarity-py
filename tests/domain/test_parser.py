"""Tests for SQL parser."""

import pytest
from sql_similarity.domain.parser import parse_sql


class TestParseSql:
    """Tests for parse_sql function."""

    def test_parse_simple_select_returns_parse_tree(self):
        """parse_sql should return an ANTLR4 parse tree for valid SQL."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # Should return a parse tree context (Snowflake_fileContext)
        assert result is not None
        assert "Snowflake_file" in type(result).__name__

    def test_parse_select_with_where_clause(self):
        """parse_sql should handle WHERE clauses."""
        sql = "SELECT id, name FROM users WHERE active = true"
        result = parse_sql(sql)

        assert result is not None
        assert "Snowflake_file" in type(result).__name__

    def test_parse_complex_join(self):
        """parse_sql should handle JOINs."""
        sql = """
        SELECT u.id, o.total
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        """
        result = parse_sql(sql)

        assert result is not None
        assert "Snowflake_file" in type(result).__name__

    def test_parse_tree_has_children(self):
        """parse_sql result should have children (not an empty tree)."""
        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # ANTLR4 trees have getChildCount() method
        assert result.getChildCount() > 0
