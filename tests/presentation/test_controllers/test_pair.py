"""Tests for PairController."""

import argparse
from pathlib import Path

import pytest

from sql_similarity.presentation.controllers.pair import PairController
from sql_similarity.presentation.exit_codes import ExitCode


class TestPairController:
    """Tests for PairController.execute()."""

    @pytest.fixture
    def fixtures_dir(self):
        """Return path to test fixtures directory."""
        return Path(__file__).parent.parent.parent / "fixtures"

    @pytest.fixture
    def controller(self):
        """Return a PairController instance."""
        return PairController()

    def test_execute_returns_success_for_identical_files(
        self, controller, fixtures_dir, capsys
    ):
        """execute() should return SUCCESS for identical files."""
        file1 = str(fixtures_dir / "simple_select.sql")
        args = argparse.Namespace(path1=file1, path2=file1, json=False)

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert "Tree Edit Distance: 0" in captured.out

    def test_execute_returns_success_for_different_files(
        self, controller, fixtures_dir, capsys
    ):
        """execute() should return SUCCESS for different valid files."""
        file1 = str(fixtures_dir / "simple_select.sql")
        file2 = str(fixtures_dir / "complex_join.sql")
        args = argparse.Namespace(path1=file1, path2=file2, json=False)

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert "Tree Edit Distance:" in captured.out

    def test_execute_json_format(self, controller, fixtures_dir, capsys):
        """execute() should output JSON when json=True."""
        file1 = str(fixtures_dir / "simple_select.sql")
        args = argparse.Namespace(path1=file1, path2=file1, json=True)

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert '"distance":' in captured.out
        assert '"operations":' in captured.out

    def test_execute_returns_invalid_args_for_missing_path2(
        self, controller, capsys
    ):
        """execute() should return INVALID_ARGS when path2 is None."""
        args = argparse.Namespace(path1="/some/file.sql", path2=None, json=False)

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.INVALID_ARGS
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "Two files required" in captured.err

    def test_execute_returns_file_not_found_for_missing_file(
        self, controller, capsys
    ):
        """execute() should return FILE_NOT_FOUND for nonexistent file."""
        args = argparse.Namespace(
            path1="/nonexistent/file1.sql",
            path2="/nonexistent/file2.sql",
            json=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.FILE_NOT_FOUND
        captured = capsys.readouterr()
        assert "Error:" in captured.err

    def test_execute_returns_parse_error_for_invalid_sql(
        self, controller, fixtures_dir, tmp_path, capsys
    ):
        """execute() should return PARSE_ERROR for invalid SQL."""
        invalid_sql = tmp_path / "invalid.sql"
        invalid_sql.write_text("THIS IS NOT VALID SQL @#$%^&*()")
        valid_sql = str(fixtures_dir / "simple_select.sql")

        args = argparse.Namespace(
            path1=str(invalid_sql),
            path2=valid_sql,
            json=False,
        )

        exit_code = controller.execute(args)

        assert exit_code == ExitCode.PARSE_ERROR
        captured = capsys.readouterr()
        assert "Error:" in captured.err
