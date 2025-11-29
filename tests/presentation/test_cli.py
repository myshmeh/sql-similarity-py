"""Tests for CLI integration."""

import json
import subprocess
from pathlib import Path

import pytest


class TestCliIntegration:
    """Integration tests for the sql-similarity CLI."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def run_cli(self, *args):
        """Run the CLI with given arguments and return result."""
        result = subprocess.run(
            ["uv", "run", "sql-similarity", *args],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result

    def test_cli_compares_identical_files(self, fixtures_dir):
        """CLI should report distance 0 for identical files."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2)

        assert result.returncode == 0
        assert "Tree Edit Distance: 0" in result.stdout

    def test_cli_compares_different_files(self, fixtures_dir):
        """CLI should report positive distance for different files."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "complex_join.sql")

        result = self.run_cli(file1, file2)

        assert result.returncode == 0
        assert "Tree Edit Distance:" in result.stdout
        assert "Operations:" in result.stdout

    def test_cli_json_output(self, fixtures_dir):
        """CLI should output valid JSON with --json flag."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2, "--json")

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "distance" in parsed
        assert "operations" in parsed
        assert parsed["distance"] == 0

    def test_cli_json_short_flag(self, fixtures_dir):
        """CLI should accept -j as short form of --json."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2, "-j")

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "distance" in parsed

    def test_cli_shows_operations_in_output(self, fixtures_dir):
        """CLI should show operations in human-readable output."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2)

        assert result.returncode == 0
        assert "MATCH:" in result.stdout
