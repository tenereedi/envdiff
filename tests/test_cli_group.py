"""Tests for envdiff.cli_group."""
import argparse
import json
from pathlib import Path

import pytest

from envdiff.cli_group import run_group, build_group_parser


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nAWS_KEY=abc\nPORT=8080\n"


@pytest.fixture
def env_file(tmp_path):
    f = tmp_path / "test.env"
    f.write_text(ENV_CONTENT)
    return str(f)


def _ns(file, fmt="text", pattern=None):
    return argparse.Namespace(file=file, format=fmt, pattern=pattern or [])


def test_returns_zero_on_valid_file(env_file):
    assert run_group(_ns(env_file)) == 0


def test_missing_file_returns_two(tmp_path):
    assert run_group(_ns(str(tmp_path / "missing.env"))) == 2


def test_json_output_has_groups(env_file, capsys):
    run_group(_ns(env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "groups" in data
    assert "source" in data


def test_json_output_db_group(env_file, capsys):
    run_group(_ns(env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "DB" in data["groups"]


def test_text_output_contains_group_header(env_file, capsys):
    run_group(_ns(env_file, fmt="text"))
    out = capsys.readouterr().out
    assert "[DB]" in out


def test_custom_pattern_applied(env_file, capsys):
    run_group(_ns(env_file, fmt="json", pattern=["DB_*=database"]))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "database" in data["groups"]


def test_invalid_pattern_exits(env_file):
    with pytest.raises(SystemExit) as exc:
        run_group(_ns(env_file, pattern=["NOEQUALSSIGN"]))
    assert exc.value.code == 2


def test_build_group_parser_returns_parser():
    p = build_group_parser()
    assert isinstance(p, argparse.ArgumentParser)
