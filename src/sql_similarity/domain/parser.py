"""SQL parsing using Snowflake ANTLR4 grammar."""

import sys
from pathlib import Path

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

# Add grammars directory to path for imports
_grammars_path = Path(__file__).parent.parent.parent.parent / "grammars" / "snowflake"
if str(_grammars_path) not in sys.path:
    sys.path.insert(0, str(_grammars_path))

from SnowflakeLexer import SnowflakeLexer
from SnowflakeParser import SnowflakeParser


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


class _ErrorCollector(ErrorListener):
    """Collects syntax errors from ANTLR4 parser."""

    def __init__(self):
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(ParseError(msg, line, column))


def parse_sql(sql_text: str, raise_on_error: bool = False) -> SnowflakeParser.Snowflake_fileContext:
    """Parse SQL text into an ANTLR4 parse tree.

    Args:
        sql_text: SQL query string to parse.
        raise_on_error: If True, raise ParseError on syntax errors.

    Returns:
        ANTLR4 parse tree with Snowflake_fileContext as root.

    Raises:
        ParseError: If raise_on_error is True and parsing fails.
    """
    input_stream = InputStream(sql_text)
    lexer = SnowflakeLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = SnowflakeParser(token_stream)

    if raise_on_error:
        # Remove default error listeners and add our collector
        error_collector = _ErrorCollector()
        lexer.removeErrorListeners()
        lexer.addErrorListener(error_collector)
        parser.removeErrorListeners()
        parser.addErrorListener(error_collector)

    tree = parser.snowflake_file()

    if raise_on_error and error_collector.errors:
        # Raise the first error encountered
        raise error_collector.errors[0]

    return tree
