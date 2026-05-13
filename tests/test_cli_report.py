"""Tests for envdiff.cli_report — run_report CLI handler."""

from __future__ import annotations

import argparse
import os
import tempfile

import pytest

from envdiff.cli_report import run_report, build_report_parser


CLEAN_CONTENT = "APP_NAME=myapp\nSECRET_KEY=abc123\nDEBUG=false\n"
DIRTY_CONTENT = "1BAD=key\nDUPE=a\nDUPE=b\n"


@pytest.fixture
def clean_env_file(tmp_path):
    f = tmp_path / "clean.env"
    f.write_text(CLEAN_CONTENT)
    return str(f)


@pytest.fixture
def dirty_env_file(tmp_path):
    f = tmp_path / "dirty.env"
    f.write_text(DIRTY_CONTENT)
    return str(f)


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"fmt": "text", "no_score": False, "no_lint": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_clean_returns_zero(clean_env_file):
    ns = _ns(file=clean_env_file)
    assert run_report(ns) == 0


def test_dirty_returns_nonzero(dirty_env_file):
    ns = _ns(file=dirty_env_file)
    result = run_report(ns)
    assert result != 0


def test_missing_file_returns_two():
    ns = _ns(file="nonexistent.env")
    assert run_report(ns) == 2


def test_json_output_is_parseable(clean_env_file, capsys):
    import json
    ns = _ns(file=clean_env_file, fmt="json")
    run_report(ns)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "overall_status" in data


def test_no_score_flag_skips_score(clean_env_file, capsys):
    ns = _ns(file=clean_env_file, fmt="json", no_score=True)
    run_report(ns)
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    section_names = [s["name"] for s in data["sections"]]
    assert "score" not in section_names


def test_no_lint_flag_skips_lint(clean_env_file, capsys):
    ns = _ns(file=clean_env_file, fmt="json", no_lint=True)
    run_report(ns)
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    section_names = [s["name"] for s in data["sections"]]
    assert "lint" not in section_names


def test_text_output_contains_source(clean_env_file, capsys):
    ns = _ns(file=clean_env_file, fmt="text")
    run_report(ns)
    captured = capsys.readouterr()
    assert "clean.env" in captured.out


def test_build_report_parser_returns_parser():
    parser = build_report_parser()
    assert isinstance(parser, argparse.ArgumentParser)
