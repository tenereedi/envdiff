"""Tests for envdiff.cli_rename."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from envdiff.cli_rename import build_rename_parser, run_rename


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n"


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT)
    return str(p)


def _ns(file, renames, fmt="text", output=None):
    return argparse.Namespace(file=file, renames=renames, format=fmt, output=output)


def test_rename_returns_zero_on_success(env_file):
    ns = _ns(env_file, ["DB_HOST=DATABASE_HOST"])
    assert run_rename(ns) == 0


def test_rename_returns_one_when_skipped(env_file):
    ns = _ns(env_file, ["MISSING_KEY=NEW_KEY"])
    assert run_rename(ns) == 1


def test_missing_file_returns_two(tmp_path):
    ns = _ns(str(tmp_path / "no.env"), ["A=B"])
    assert run_rename(ns) == 2


def test_invalid_rename_spec_returns_two(env_file):
    ns = _ns(env_file, ["BADSPEC"])
    assert run_rename(ns) == 2


def test_text_output_contains_new_key(env_file, capsys):
    ns = _ns(env_file, ["DB_HOST=DATABASE_HOST"])
    run_rename(ns)
    captured = capsys.readouterr()
    assert "DATABASE_HOST=localhost" in captured.out
    assert "DB_HOST" not in captured.out.split("#")[-1]


def test_json_output_is_valid(env_file, capsys):
    ns = _ns(env_file, ["DB_HOST=DATABASE_HOST"], fmt="json")
    run_rename(ns)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "renamed_count" in data
    assert data["renamed_count"] == 1


def test_json_output_skipped_list(env_file, capsys):
    ns = _ns(env_file, ["GHOST=NEW"], fmt="json")
    run_rename(ns)
    data = json.loads(capsys.readouterr().out)
    assert "GHOST" in data["skipped"]


def test_output_written_to_file(env_file, tmp_path):
    out_path = tmp_path / "out.env"
    ns = _ns(env_file, ["DB_HOST=DATABASE_HOST"], output=str(out_path))
    run_rename(ns)
    assert out_path.exists()
    assert "DATABASE_HOST=localhost" in out_path.read_text()


def test_build_rename_parser_returns_parser():
    parser = build_rename_parser()
    assert isinstance(parser, argparse.ArgumentParser)
