"""Tests for envdiff.cli_score."""
import json
import argparse
import pytest
from pathlib import Path

from envdiff.cli_score import build_score_parser, run_score


CLEAN_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=s3cr3t\n"
DIRTY_CONTENT = "1BAD=val\nDB_HOST=a\nDB_HOST=dup\n"


@pytest.fixture
def clean_env_file(tmp_path):
    f = tmp_path / "clean.env"
    f.write_text(CLEAN_CONTENT)
    return f


@pytest.fixture
def dirty_env_file(tmp_path):
    f = tmp_path / "dirty.env"
    f.write_text(DIRTY_CONTENT)
    return f


def _ns(file, fmt="text", profile=None, min_score=0.0):
    return argparse.Namespace(file=str(file), format=fmt, profile=profile, min_score=min_score)


def test_clean_returns_zero(clean_env_file):
    assert run_score(_ns(clean_env_file)) == 0


def test_missing_file_returns_two(tmp_path):
    assert run_score(_ns(tmp_path / "missing.env")) == 2


def test_min_score_triggers_exit_one(dirty_env_file):
    result = run_score(_ns(dirty_env_file, min_score=99.0))
    assert result == 1


def test_min_score_zero_always_passes(clean_env_file):
    assert run_score(_ns(clean_env_file, min_score=0.0)) == 0


def test_json_output(clean_env_file, capsys):
    run_score(_ns(clean_env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "score" in data
    assert "grade" in data
    assert "breakdown" in data


def test_text_output_contains_score(clean_env_file, capsys):
    run_score(_ns(clean_env_file, fmt="text"))
    out = capsys.readouterr().out
    assert "Score" in out


def test_build_score_parser_returns_parser():
    parser = build_score_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_profile_flag_accepted(clean_env_file):
    code = run_score(_ns(clean_env_file, profile="minimal"))
    assert code in (0, 1)
