"""SQL parsing using sqlparse library."""

import sqlparse
from sqlparse.sql import Statement


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


def parse_sql(sql_text: str, raise_on_error: bool = False) -> Statement:
    """Parse SQL text into a sqlparse Statement.

    Args:
        sql_text: SQL query string to parse.
        raise_on_error: If True, raise ParseError on empty/whitespace-only SQL.

    Returns:
        sqlparse Statement object representing the parsed SQL.

    Raises:
        ParseError: If raise_on_error is True and SQL is empty or whitespace-only.
    """
    statements = sqlparse.parse(sql_text)

    if not statements or not statements[0].tokens:
        if raise_on_error:
            raise ParseError("No SQL statements found")
        # Return an empty Statement for compatibility
        return Statement([])

    first_statement = statements[0]

    # Check if statement contains only whitespace tokens
    has_meaningful_content = any(
        not token.is_whitespace for token in first_statement.tokens
    )

    if not has_meaningful_content:
        if raise_on_error:
            raise ParseError("No SQL statements found")
        return Statement([])

    return first_statement
