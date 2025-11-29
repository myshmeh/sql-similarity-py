"""Tests for argument parser factory."""

import pytest

from sql_similarity.presentation.args import create_parser, get_version


class TestCreateParser:
    """Tests for create_parser() factory function."""

    def test_create_parser_returns_argument_parser(self):
        """create_parser() should return an ArgumentParser instance."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "sql-similarity"

    def test_parser_has_path1_argument(self):
        """Parser should have path1 positional argument."""
        parser = create_parser()
        args = parser.parse_args(["file1.sql", "file2.sql"])
        assert args.path1 == "file1.sql"

    def test_parser_has_optional_path2_argument(self):
        """Parser should have optional path2 argument."""
        parser = create_parser()

        # With path2
        args = parser.parse_args(["file1.sql", "file2.sql"])
        assert args.path2 == "file2.sql"

        # Without path2 (batch mode)
        args = parser.parse_args(["./directory/"])
        assert args.path2 is None

    def test_parser_has_json_flag(self):
        """Parser should have -j/--json flag."""
        parser = create_parser()

        # Default is False
        args = parser.parse_args(["f1.sql", "f2.sql"])
        assert args.json is False

        # With --json
        args = parser.parse_args(["f1.sql", "f2.sql", "--json"])
        assert args.json is True

        # With -j
        args = parser.parse_args(["f1.sql", "f2.sql", "-j"])
        assert args.json is True

    def test_parser_has_csv_flag(self):
        """Parser should have -c/--csv flag."""
        parser = create_parser()

        # Default is False
        args = parser.parse_args(["./dir/"])
        assert args.csv is False

        # With --csv
        args = parser.parse_args(["./dir/", "--csv"])
        assert args.csv is True

        # With -c
        args = parser.parse_args(["./dir/", "-c"])
        assert args.csv is True

    def test_json_and_csv_are_mutually_exclusive(self):
        """Parser should not allow both --json and --csv."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["./dir/", "--json", "--csv"])

    def test_parser_has_max_distance_option(self):
        """Parser should have -m/--max-distance option."""
        parser = create_parser()

        # Default is None
        args = parser.parse_args(["./dir/"])
        assert args.max_distance is None

        # With --max-distance
        args = parser.parse_args(["./dir/", "--max-distance", "5"])
        assert args.max_distance == 5

        # With -m
        args = parser.parse_args(["./dir/", "-m", "10"])
        assert args.max_distance == 10

    def test_parser_has_top_option(self):
        """Parser should have -t/--top option."""
        parser = create_parser()

        # Default is None
        args = parser.parse_args(["./dir/"])
        assert args.top is None

        # With --top
        args = parser.parse_args(["./dir/", "--top", "3"])
        assert args.top == 3

        # With -t
        args = parser.parse_args(["./dir/", "-t", "5"])
        assert args.top == 5

    def test_parser_max_distance_requires_integer(self):
        """Parser should reject non-integer max-distance."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["./dir/", "--max-distance", "abc"])

    def test_parser_top_requires_integer(self):
        """Parser should reject non-integer top."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["./dir/", "--top", "abc"])


class TestGetVersion:
    """Tests for get_version() function."""

    def test_get_version_returns_string(self):
        """get_version() should return a version string."""
        version = get_version()
        assert isinstance(version, str)
        assert version == "0.1.0"
