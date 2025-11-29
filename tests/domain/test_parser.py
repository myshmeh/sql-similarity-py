"""Tests for SQL parser."""

import pytest
from sqlglot import exp


class TestParseSql:
    """Tests for parse_sql function."""

    def test_parse_simple_select_returns_sqlglot_expression(self):
        """parse_sql should return a sqlglot Expression for valid SQL."""
        from sql_similarity.domain.parser import parse_sql

        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # Should return a sqlglot Expression (specifically Select)
        assert result is not None
        assert isinstance(result, exp.Expression)
        assert isinstance(result, exp.Select)

    def test_parse_select_with_where_clause(self):
        """parse_sql should handle WHERE clauses."""
        from sql_similarity.domain.parser import parse_sql

        sql = "SELECT id, name FROM users WHERE active = true"
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, exp.Select)
        # Check that WHERE clause is present
        assert result.find(exp.Where) is not None

    def test_parse_complex_join(self):
        """parse_sql should handle JOINs."""
        from sql_similarity.domain.parser import parse_sql

        sql = """
        SELECT u.id, o.total
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        """
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, exp.Select)
        # Check that JOIN is present
        assert result.find(exp.Join) is not None

    def test_parse_tree_has_children(self):
        """parse_sql result should have children (not an empty tree)."""
        from sql_similarity.domain.parser import parse_sql

        sql = "SELECT id FROM users"
        result = parse_sql(sql)

        # sqlglot trees have args dict with children
        assert len(result.args) > 0

    def test_parse_error_raises_on_invalid_sql(self):
        """parse_sql should raise ParseError for invalid SQL when raise_on_error=True."""
        from sql_similarity.domain.parser import parse_sql, ParseError

        sql = "SELECT FROM"  # Invalid SQL

        with pytest.raises(ParseError):
            parse_sql(sql, raise_on_error=True)

    def test_parse_error_contains_line_info(self):
        """ParseError should contain line information when available."""
        from sql_similarity.domain.parser import ParseError

        error = ParseError("test error", line=1, column=5)

        assert error.line == 1
        assert error.column == 5
        assert "line 1:5" in str(error)

    def test_parse_snowflake_specific_syntax(self):
        """parse_sql should handle Snowflake-specific syntax like QUALIFY."""
        from sql_similarity.domain.parser import parse_sql

        sql = """
        SELECT id, name, ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) as rn
        FROM employees
        QUALIFY rn = 1
        """
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, exp.Select)

    def test_parse_sql_accepts_dialect_parameter(self):
        """parse_sql should accept an optional dialect parameter."""
        from sql_similarity.domain.parser import parse_sql

        sql = "SELECT id FROM users"
        # Should work with explicit dialect
        result = parse_sql(sql, dialect="snowflake")

        assert result is not None
        assert isinstance(result, exp.Select)

    def test_parse_sql_default_dialect_is_snowflake(self):
        """parse_sql should default to snowflake dialect."""
        from sql_similarity.domain.parser import parse_sql

        # Snowflake-specific syntax should work without specifying dialect
        sql = "SELECT * FROM table1 SAMPLE (10)"  # Snowflake SAMPLE syntax
        result = parse_sql(sql)

        assert result is not None
        assert isinstance(result, exp.Select)
