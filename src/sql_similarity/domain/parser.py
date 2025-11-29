"""SQL parsing using sqlglot."""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError as SQLGlotParseError


class ParseError(Exception):
    """Exception raised when SQL parsing fails.

    Attributes:
        message: Description of the parse error.
        line: Line number where error occurred.
        column: Column number where error occurred.
    """

    def __init__(self, message: str, line: int = None, column: int = None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.line is not None and self.column is not None:
            return f"line {self.line}:{self.column} {self.message}"
        return self.message


def parse_sql(
    sql_text: str, raise_on_error: bool = False, dialect: str = "snowflake"
) -> exp.Expression:
    """Parse SQL text into a sqlglot expression tree.

    Args:
        sql_text: SQL query string to parse.
        raise_on_error: If True, raise ParseError on syntax errors.
        dialect: SQL dialect to use for parsing. Defaults to "snowflake".
                 Supported dialects include: snowflake, postgres, mysql, bigquery,
                 redshift, spark, trino, duckdb, and many more.
                 See sqlglot documentation for full list of supported dialects.

    Returns:
        sqlglot Expression tree.

    Raises:
        ParseError: If raise_on_error is True and parsing fails.
    """
    try:
        tree = sqlglot.parse_one(sql_text, dialect=dialect)
        return tree
    except SQLGlotParseError as e:
        if raise_on_error:
            if e.errors:
                error = e.errors[0]
                raise ParseError(
                    error.get("description", str(e)),
                    error.get("line"),
                    error.get("col"),
                )
            raise ParseError(str(e))
        # Return empty expression on error if not raising
        return exp.Expression()
