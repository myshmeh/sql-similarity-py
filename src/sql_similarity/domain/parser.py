"""SQL parsing using sqlglot library."""

from sqlglot import parse_one, exp
from sqlglot.errors import ParseError as SqlglotParseError


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


def parse_sql(sql_text: str, raise_on_error: bool = False) -> exp.Expression | None:
    """Parse SQL text into a sqlglot Expression.

    Args:
        sql_text: SQL query string to parse.
        raise_on_error: If True, raise ParseError on empty/whitespace-only/invalid SQL.

    Returns:
        sqlglot Expression object representing the parsed SQL, or None if parsing fails
        and raise_on_error is False.

    Raises:
        ParseError: If raise_on_error is True and SQL is empty, whitespace-only, or invalid.
    """
    # Check for empty or whitespace-only input
    if not sql_text or not sql_text.strip():
        if raise_on_error:
            raise ParseError("No SQL statements found")
        return None

    try:
        result = parse_one(sql_text)
        return result
    except SqlglotParseError as e:
        if raise_on_error:
            raise ParseError(str(e))
        return None
