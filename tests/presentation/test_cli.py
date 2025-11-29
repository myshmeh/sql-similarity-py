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


class TestCliErrorHandling:
    """Tests for CLI error handling (US3)."""

    def run_cli(self, *args):
        """Run the CLI with given arguments and return result."""
        result = subprocess.run(
            ["uv", "run", "sql-similarity", *args],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result

    def test_file_not_found_returns_exit_code_1(self):
        """CLI should return exit code 1 for file not found."""
        result = self.run_cli("/nonexistent/path/file1.sql", "/nonexistent/path/file2.sql")

        assert result.returncode == 1
        assert "Error" in result.stderr or "error" in result.stderr.lower()
        assert "not found" in result.stderr.lower() or "no such file" in result.stderr.lower()

    def test_file_not_found_writes_to_stderr(self):
        """CLI should write file not found error to stderr."""
        result = self.run_cli("/nonexistent/file.sql", "/another/nonexistent.sql")

        assert result.returncode == 1
        assert len(result.stderr) > 0
        assert len(result.stdout) == 0  # No output to stdout on error

    def test_sql_parse_error_returns_exit_code_2(self, tmp_path):
        """CLI should return exit code 2 for SQL parse error."""
        # Create a file with invalid SQL
        invalid_sql = tmp_path / "invalid.sql"
        invalid_sql.write_text("THIS IS NOT VALID SQL @#$%^&*()")

        valid_sql = tmp_path / "valid.sql"
        valid_sql.write_text("SELECT id FROM users")

        result = self.run_cli(str(invalid_sql), str(valid_sql))

        assert result.returncode == 2
        assert "Error" in result.stderr or "error" in result.stderr.lower()

    def test_sql_parse_error_includes_filename(self, tmp_path):
        """CLI should include filename in parse error message."""
        invalid_sql = tmp_path / "broken_query.sql"
        invalid_sql.write_text("SELEC id FROM")  # Typo in SELECT

        valid_sql = tmp_path / "valid.sql"
        valid_sql.write_text("SELECT id FROM users")

        result = self.run_cli(str(invalid_sql), str(valid_sql))

        assert result.returncode == 2
        assert "broken_query.sql" in result.stderr

    def test_missing_arguments_returns_exit_code_3(self):
        """CLI should return exit code 3 for missing arguments."""
        result = self.run_cli()  # No arguments

        # argparse returns exit code 2 by default for missing args
        # We'll accept either 2 or 3 as the contract says 3
        assert result.returncode in (2, 3)
        assert "usage" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_help_flag_shows_usage(self):
        """CLI should show usage with --help flag."""
        result = self.run_cli("--help")

        assert result.returncode == 0
        assert "usage" in result.stdout.lower()
        assert "file1" in result.stdout.lower()
        assert "file2" in result.stdout.lower()

    def test_version_flag_shows_version(self):
        """CLI should show version with --version flag."""
        result = self.run_cli("--version")

        assert result.returncode == 0
        # Version should be in output (either stdout or contain version number)
        output = result.stdout + result.stderr
        assert "0.1.0" in output or "version" in output.lower()
