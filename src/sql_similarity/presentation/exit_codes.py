"""Centralized exit code definitions for CLI commands."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Exit codes for CLI commands.

    Pair mode codes:
        SUCCESS: Successful comparison
        FILE_NOT_FOUND: Input file does not exist
        PARSE_ERROR: SQL parsing failed
        INVALID_ARGS: Invalid arguments provided

    Batch mode codes:
        BATCH_SUCCESS: All files processed successfully
        BATCH_PARTIAL: Some files had errors
        BATCH_NO_FILES: No SQL files found in directory
        BATCH_DIR_NOT_FOUND: Directory does not exist
        BATCH_INVALID_ARGS: Invalid batch arguments
    """

    # Pair mode
    SUCCESS = 0
    FILE_NOT_FOUND = 1
    PARSE_ERROR = 2
    INVALID_ARGS = 3

    # Batch mode
    BATCH_SUCCESS = 0
    BATCH_PARTIAL = 1
    BATCH_NO_FILES = 2
    BATCH_DIR_NOT_FOUND = 3
    BATCH_INVALID_ARGS = 4
