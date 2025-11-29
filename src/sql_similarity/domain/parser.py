"""SQL parsing using Snowflake ANTLR4 grammar."""

import sys
from pathlib import Path

from antlr4 import CommonTokenStream, InputStream

# Add grammars directory to path for imports
_grammars_path = Path(__file__).parent.parent.parent.parent / "grammars" / "snowflake"
if str(_grammars_path) not in sys.path:
    sys.path.insert(0, str(_grammars_path))

from SnowflakeLexer import SnowflakeLexer
from SnowflakeParser import SnowflakeParser


def parse_sql(sql_text: str) -> SnowflakeParser.Snowflake_fileContext:
    """Parse SQL text into an ANTLR4 parse tree.

    Args:
        sql_text: SQL query string to parse.

    Returns:
        ANTLR4 parse tree with Snowflake_fileContext as root.
    """
    input_stream = InputStream(sql_text)
    lexer = SnowflakeLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = SnowflakeParser(token_stream)
    tree = parser.snowflake_file()
    return tree
