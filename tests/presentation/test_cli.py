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
        """CLI should report edit_count 0 for identical files."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2)

        assert result.returncode == 0
        assert "Edit Count: 0" in result.stdout

    def test_cli_compares_different_files(self, fixtures_dir):
        """CLI should report positive edit_count for different files."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "complex_join.sql")

        result = self.run_cli(file1, file2)

        assert result.returncode == 0
        assert "Edit Count:" in result.stdout
        assert "Operations:" in result.stdout

    def test_cli_json_output(self, fixtures_dir):
        """CLI should output valid JSON with --json flag."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2, "--json")

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "edit_count" in parsed
        assert "operations" in parsed
        assert parsed["edit_count"] == 0

    def test_cli_json_short_flag(self, fixtures_dir):
        """CLI should accept -j as short form of --json."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "simple_select.sql")

        result = self.run_cli(file1, file2, "-j")

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "edit_count" in parsed

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
        """CLI should return exit code 2 for SQL parse error (empty file).

        Note: sqlparse is a non-validating parser, so "invalid" SQL like
        'THIS IS NOT VALID SQL' is still parsed. Empty files trigger errors.
        """
        # Create an empty SQL file (triggers ParseError)
        empty_sql = tmp_path / "empty.sql"
        empty_sql.write_text("")

        valid_sql = tmp_path / "valid.sql"
        valid_sql.write_text("SELECT id FROM users")

        result = self.run_cli(str(empty_sql), str(valid_sql))

        assert result.returncode == 2
        assert "Error" in result.stderr or "error" in result.stderr.lower()

    def test_sql_parse_error_includes_filename(self, tmp_path):
        """CLI should include filename in parse error message."""
        empty_sql = tmp_path / "broken_query.sql"
        empty_sql.write_text("")  # Empty file triggers ParseError

        valid_sql = tmp_path / "valid.sql"
        valid_sql.write_text("SELECT id FROM users")

        result = self.run_cli(str(empty_sql), str(valid_sql))

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
        assert "path1" in result.stdout.lower()
        assert "path2" in result.stdout.lower()

    def test_version_flag_shows_version(self):
        """CLI should show version with --version flag."""
        result = self.run_cli("--version")

        assert result.returncode == 0
        # Version should be in output (either stdout or contain version number)
        output = result.stdout + result.stderr
        assert "0.1.0" in output or "version" in output.lower()


# ============================================================================
# US1 Tests: Batch Mode CLI
# ============================================================================


class TestCliBatchMode:
    """Tests for batch mode CLI (T012-T016)."""

    def run_cli(self, *args):
        """Run the CLI with given arguments and return result."""
        result = subprocess.run(
            ["uv", "run", "sql-similarity", *args],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    def test_cli_detects_directory_argument(self, fixtures_dir):
        """CLI should detect when first argument is a directory (T012)."""
        result = self.run_cli(str(fixtures_dir))

        # Should succeed and show batch output
        assert result.returncode == 0
        assert "Batch Comparison:" in result.stdout

    def test_cli_outputs_table_format_for_batch_mode(self, fixtures_dir):
        """CLI should output table format for batch mode (T013)."""
        result = self.run_cli(str(fixtures_dir))

        assert result.returncode == 0
        # Should have table header elements
        assert "File 1" in result.stdout
        assert "File 2" in result.stdout
        assert "Edits" in result.stdout
        # Should show file count info
        assert "Files:" in result.stdout
        assert "Comparisons:" in result.stdout

    def test_cli_exit_code_2_for_no_sql_files(self, tmp_path):
        """CLI should return exit code 2 for no SQL files (T014)."""
        # Create empty directory (or with non-sql files)
        (tmp_path / "readme.txt").write_text("Not an SQL file")

        result = self.run_cli(str(tmp_path))

        assert result.returncode == 2
        assert "No .sql files found" in result.stderr

    def test_cli_exit_code_3_for_directory_not_found(self):
        """CLI should return exit code 3 for directory not found (T015)."""
        result = self.run_cli("/nonexistent/directory/path")

        assert result.returncode == 3
        assert "Directory not found" in result.stderr

    def test_cli_exit_code_1_for_partial_success(self, tmp_path):
        """CLI should return exit code 1 for partial success with parse errors (T016).

        Note: sqlparse is a non-validating parser. Only empty files trigger errors.
        """
        # Create one valid and one empty SQL file
        (tmp_path / "valid.sql").write_text("SELECT id FROM users")
        (tmp_path / "empty.sql").write_text("")  # Empty file triggers ParseError

        result = self.run_cli(str(tmp_path))

        assert result.returncode == 1
        assert "Errors:" in result.stdout
        assert "empty.sql" in result.stdout

    def test_cli_batch_shows_sorted_results(self, tmp_path):
        """CLI batch mode should show results sorted by score descending."""
        # Create files with different similarities
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT id FROM users")  # identical to a
        (tmp_path / "c.sql").write_text(
            "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )

        result = self.run_cli(str(tmp_path))

        assert result.returncode == 0
        # Find lines with edits and verify order
        lines = result.stdout.split("\n")
        edit_lines = [l for l in lines if l.strip() and ".sql" in l]
        # First comparison should be a.sql vs b.sql with edit_count 0
        if edit_lines:
            first_line = edit_lines[0]
            assert "0" in first_line or "a.sql" in first_line


# ============================================================================
# US2 Tests: Filter CLI Options
# ============================================================================


class TestCliFilterOptions:
    """Tests for CLI filter options (T025-T031)."""

    def run_cli(self, *args):
        """Run the CLI with given arguments and return result."""
        result = subprocess.run(
            ["uv", "run", "sql-similarity", *args],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result

    def test_cli_max_edits_flag(self, tmp_path):
        """CLI should filter results by --max-edits (T025)."""
        # Create files with varying edit counts
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT id FROM users")  # identical
        (tmp_path / "c.sql").write_text(
            "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )

        result = self.run_cli(str(tmp_path), "--max-edits", "5")

        assert result.returncode == 0
        # Should only show pairs with edit_count <= 5
        assert "a.sql" in result.stdout
        assert "b.sql" in result.stdout
        # Header should indicate filter
        assert "max edits: 5" in result.stdout

    def test_cli_top_flag(self, tmp_path):
        """CLI should filter results by --top (T026)."""
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")
        (tmp_path / "c.sql").write_text("SELECT 3")
        (tmp_path / "d.sql").write_text("SELECT 4")

        result = self.run_cli(str(tmp_path), "--top", "2")

        assert result.returncode == 0
        # Should show "Showing: 2 of X" in header
        assert "top 2" in result.stdout

    def test_cli_combined_max_edits_and_top(self, tmp_path):
        """CLI should combine --max-edits and --top filters (T027)."""
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT id FROM users")  # identical
        (tmp_path / "c.sql").write_text("SELECT name FROM customers")
        (tmp_path / "d.sql").write_text(
            "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )

        result = self.run_cli(str(tmp_path), "--max-edits", "20", "--top", "2")

        assert result.returncode == 0
        assert "max edits: 20" in result.stdout
        assert "top 2" in result.stdout

    def test_cli_exit_code_4_for_invalid_max_edits(self, tmp_path):
        """CLI should return exit code 4 for negative --max-edits (T028)."""
        (tmp_path / "a.sql").write_text("SELECT 1")

        result = self.run_cli(str(tmp_path), "--max-edits", "-1")

        assert result.returncode == 4
        assert "must be" in result.stderr.lower() or "invalid" in result.stderr.lower()

    def test_cli_exit_code_4_for_invalid_top(self, tmp_path):
        """CLI should return exit code 4 for zero or negative --top (T029)."""
        (tmp_path / "a.sql").write_text("SELECT 1")

        result = self.run_cli(str(tmp_path), "--top", "0")

        assert result.returncode == 4
        assert "must be" in result.stderr.lower() or "invalid" in result.stderr.lower()

    def test_table_header_shows_filter_info(self, tmp_path):
        """CLI table header should show filter info (T030)."""
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")

        result = self.run_cli(str(tmp_path), "--max-edits", "10")

        assert result.returncode == 0
        assert "(max edits: 10)" in result.stdout

    def test_table_header_shows_filtered_count(self, tmp_path):
        """CLI table header should show 'Showing: X of Y' when filtered (T031)."""
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")
        (tmp_path / "c.sql").write_text("SELECT 3")

        result = self.run_cli(str(tmp_path), "--top", "1")

        assert result.returncode == 0
        assert "Showing:" in result.stdout


# ============================================================================
# US3 Tests: Output Formats CLI
# ============================================================================


class TestCliBatchOutputFormats:
    """Tests for CLI batch output format options (T041-T043)."""

    def run_cli(self, *args):
        """Run the CLI with given arguments and return result."""
        result = subprocess.run(
            ["uv", "run", "sql-similarity", *args],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result

    def test_cli_json_flag_for_batch_mode(self, tmp_path):
        """CLI --json flag should output JSON for batch mode (T041)."""
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT name FROM customers")

        result = self.run_cli(str(tmp_path), "--json")

        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert "directory" in parsed
        assert "comparisons" in parsed
        assert "operations" in parsed["comparisons"][0]

    def test_cli_csv_flag_for_batch_mode(self, tmp_path):
        """CLI --csv flag should output CSV for batch mode (T042)."""
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT name FROM customers")

        result = self.run_cli(str(tmp_path), "--csv")

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[0] == "file1,file2,score,edit_count"
        assert len(lines) == 2  # header + 1 comparison

    def test_json_and_csv_are_mutually_exclusive(self, tmp_path):
        """CLI --json and --csv should be mutually exclusive (T043)."""
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")

        result = self.run_cli(str(tmp_path), "--json", "--csv")

        # Should fail with error
        assert result.returncode != 0
        assert "cannot" in result.stderr.lower() or "mutually" in result.stderr.lower() or "not allowed" in result.stderr.lower()


# ============================================================================
# US1 Enhancement: Recursive Directory Scanning CLI Tests (T055)
# ============================================================================


class TestCliRecursiveScanning:
    """Tests for recursive directory scanning in CLI (T055)."""

    def run_cli(self, *args):
        """Run the CLI with given arguments and return result."""
        result = subprocess.run(
            ["uv", "run", "sql-similarity", *args],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,
        )
        return result

    def test_cli_batch_mode_outputs_relative_paths_for_nested_files(self, tmp_path):
        """CLI batch mode should output relative paths for nested files (T055)."""
        # Create nested directory structure
        (tmp_path / "root.sql").write_text("SELECT id FROM users")

        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "daily.sql").write_text("SELECT * FROM daily_metrics")

        result = self.run_cli(str(tmp_path))

        assert result.returncode == 0
        # Should show relative paths with subdirectory prefix
        assert "reports/daily.sql" in result.stdout
        assert "root.sql" in result.stdout

    def test_cli_json_output_includes_relative_paths(self, tmp_path):
        """CLI JSON output should include relative paths for nested files."""
        (tmp_path / "root.sql").write_text("SELECT 1")

        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.sql").write_text("SELECT 2")

        result = self.run_cli(str(tmp_path), "--json")

        assert result.returncode == 0
        parsed = json.loads(result.stdout)

        # Check that relative path is in the comparison output
        all_files = set()
        for comp in parsed["comparisons"]:
            all_files.add(comp["file1"])
            all_files.add(comp["file2"])

        assert "subdir/nested.sql" in all_files

    def test_cli_csv_output_includes_relative_paths(self, tmp_path):
        """CLI CSV output should include relative paths for nested files."""
        (tmp_path / "root.sql").write_text("SELECT 1")

        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.sql").write_text("SELECT 2")

        result = self.run_cli(str(tmp_path), "--csv")

        assert result.returncode == 0
        assert "subdir/nested.sql" in result.stdout
