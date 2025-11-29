"""Base controller interface for CLI commands."""

import argparse
from abc import ABC, abstractmethod


class BaseController(ABC):
    """Base class for CLI command controllers.

    Each controller handles one command type and is responsible for:
    1. Validating command-specific arguments
    2. Invoking the appropriate service
    3. Formatting the response
    4. Returning the appropriate exit code
    """

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command and return exit code.

        Args:
            args: Parsed command-line arguments.

        Returns:
            Exit code (use ExitCode enum values).
        """
        pass
