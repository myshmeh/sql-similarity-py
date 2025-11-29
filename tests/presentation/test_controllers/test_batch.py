"""Tests for BatchController."""

import argparse
import json
from pathlib import Path

import pytest

from sql_similarity.presentation.controllers.batch import BatchController
from sql_similarity.presentation.exit_codes import ExitCode


class TestBatchController:
    """Tests for BatchController.execute()."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent.parent / "fixtures"

    @pytest.fixture
    def controller(self):
        """Return a BatchController instance."""
        return BatchController()

    def test_execute_returns_success_for_valid_directory(
        self, controller, fixtures_dir, capsys
    ):
        """execute() should return BATCH_SUCCESS for valid directory."""
        args = argparse.Namespace(
            path1=str(fixtures_dir),
            max_distance=None,
            top=None,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_SUCCESS
        captured = capsys.readouterr()
        assert "Batch Comparison:" in captured.out

    def test_execute_returns_dir_not_found_for_missing_directory(
        self, controller, capsys
    ):
        """execute() should return BATCH_DIR_NOT_FOUND for nonexistent dir."""
        args = argparse.Namespace(
            path1="/nonexistent/directory",
            max_distance=None,
            top=None,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_DIR_NOT_FOUND
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Directory not found" in captured.err

    def test_execute_returns_no_files_for_empty_directory(
        self, controller, tmp_path, capsys
    ):
        """execute() should return BATCH_NO_FILES for dir with no SQL files."""
        (tmp_path / "readme.txt").write_text("Not an SQL file")

        args = argparse.Namespace(
            path1=str(tmp_path),
            max_distance=None,
            top=None,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_NO_FILES
        captured = capsys.readouterr()
        assert "No .sql files found" in captured.err

    def test_execute_returns_partial_for_parse_errors(
        self, controller, tmp_path, capsys
    ):
        """execute() should return BATCH_PARTIAL when some files have errors.

        Note: sqlparse is a non-validating parser. Only empty files trigger errors.
        """
        (tmp_path / "valid.sql").write_text("SELECT id FROM users")
        (tmp_path / "empty.sql").write_text("")  # Empty file triggers ParseError

        args = argparse.Namespace(
            path1=str(tmp_path),
            max_distance=None,
            top=None,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_PARTIAL
        captured = capsys.readouterr()
        assert "Errors:" in captured.out

    def test_execute_returns_invalid_args_for_negative_max_distance(
        self, controller, tmp_path, capsys
    ):
        """execute() should return BATCH_INVALID_ARGS for negative max_distance."""
        (tmp_path / "a.sql").write_text("SELECT 1")

        args = argparse.Namespace(
            path1=str(tmp_path),
            max_distance=-1,
            top=None,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_INVALID_ARGS
        captured = capsys.readouterr()
        assert "must be" in captured.err.lower()

    def test_execute_returns_invalid_args_for_zero_top(
        self, controller, tmp_path, capsys
    ):
        """execute() should return BATCH_INVALID_ARGS for zero top."""
        (tmp_path / "a.sql").write_text("SELECT 1")

        args = argparse.Namespace(
            path1=str(tmp_path),
            max_distance=None,
            top=0,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_INVALID_ARGS
        captured = capsys.readouterr()
        assert "must be" in captured.err.lower()

    def test_execute_json_format(self, controller, fixtures_dir, capsys):
        """execute() should output JSON when json=True."""
        args = argparse.Namespace(
            path1=str(fixtures_dir),
            max_distance=None,
            top=None,
            json=True,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_SUCCESS
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "directory" in data
        assert "comparisons" in data

    def test_execute_csv_format(self, controller, fixtures_dir, capsys):
        """execute() should output CSV when csv=True."""
        args = argparse.Namespace(
            path1=str(fixtures_dir),
            max_distance=None,
            top=None,
            json=False,
            csv=True,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_SUCCESS
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert lines[0] == "file1,file2,score,distance"

    def test_execute_applies_max_distance_filter(self, controller, tmp_path, capsys):
        """execute() should filter results by max_distance."""
        (tmp_path / "a.sql").write_text("SELECT id FROM users")
        (tmp_path / "b.sql").write_text("SELECT id FROM users")
        (tmp_path / "c.sql").write_text(
            "SELECT u.id, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )

        args = argparse.Namespace(
            path1=str(tmp_path),
            max_distance=0,
            top=None,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_SUCCESS
        captured = capsys.readouterr()
        assert "max distance: 0" in captured.out

    def test_execute_applies_top_filter(self, controller, tmp_path, capsys):
        """execute() should filter results by top."""
        (tmp_path / "a.sql").write_text("SELECT 1")
        (tmp_path / "b.sql").write_text("SELECT 2")
        (tmp_path / "c.sql").write_text("SELECT 3")

        args = argparse.Namespace(
            path1=str(tmp_path),
            max_distance=None,
            top=1,
            json=False,
            csv=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.BATCH_SUCCESS
        captured = capsys.readouterr()
        assert "top 1" in captured.out
