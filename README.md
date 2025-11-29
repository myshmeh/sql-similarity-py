# sql-similarity

![Experimental](https://img.shields.io/badge/status-experimental-red)

A CLI tool to compare SQL files using tree edit distance. It parses SQL statements into abstract syntax trees and computes structural similarity using the APTED algorithm.

## Overview

sql-similarity analyzes SQL queries by:

1. Parsing SQL files using ANTLR4
2. Computing tree edit distance between parse trees using APTED
3. Returning a normalized similarity score (0.0 to 1.0) and detailed edit operations

The tool supports two modes:
- **Pair mode**: Compare two SQL files directly
- **Batch mode**: Compare all SQL files in a directory against each other

## Supported SQL Dialects

- **Snowflake SQL**

## Usage

No installation required - run directly with `uvx`:

### Pair Mode

Compare two SQL files:

```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity file1.sql file2.sql
```

Output includes:
- Edit distance (number of tree operations)
- Similarity score (0.0-1.0)
- List of edit operations (insert, delete, rename, match)

### Batch Mode

Compare all `.sql` files in a directory:

```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity /path/to/sql/directory
```

This compares all pairs of SQL files and outputs results sorted by similarity.

### Output Formats

**JSON output:**
```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity file1.sql file2.sql --json
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity /path/to/directory --json
```

**CSV output (batch mode only):**
```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity /path/to/directory --csv
```

### Filtering Options (Batch Mode)

Limit results by maximum distance:
```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity /path/to/directory --max-distance 10
```

Show only the top N most similar pairs:
```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity /path/to/directory --top 5
```

### Version

```bash
uvx --from https://github.com/myshmeh/sql-similarity-py.git sql-similarity --version
```

## Development

```bash
git clone https://github.com/myshmeh/sql-similarity-py.git
cd sql-similarity
uv sync --dev
```

Run tests:

```bash
uv run pytest
```

## Requirements

- Python 3.11+

## License

MIT
