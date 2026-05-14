"""Tests for envdiff.cli_trace."""
from __future__ import annotations

import argparse
from io import StringIO
from unittest.mock import mock_open, patch

import pytest

from envdiff.cli_trace import build_trace_parser, run_trace


ENV_A = "APP_ENV=production\nDB_HOST=localhost\n"
ENV_B = "APP_ENV=staging\nDB_HOST=localhost\nNEW_KEY=hello\n"
ENV_SAME = "APP_ENV=production\nDB_HOST=localhost\n"


def _ns(file_a="a.env", file_b="b.env", fmt="text"):
    return argparse.Namespace(file_a=file_a, file_b=file_b, fmt=fmt)


def _open(a_content, b_content):
    files = {"a.env": a_content, "b.env": b_content}

    def _side_effect(path, *args, **kwargs):
        return mock_open(read_data=files[path])()

    return patch("builtins.open", side_effect=_side_effect)


def test_changes_returns_one():
    with _open(ENV_A, ENV_B):
        code = run_trace(_ns())
    assert code == 1


def test_identical_returns_zero():
    with _open(ENV_SAME, ENV_SAME):
        code = run_trace(_ns())
    assert code == 0


def test_missing_file_returns_two():
    with patch("builtins.open", side_effect=FileNotFoundError("no file")):
        code = run_trace(_ns())
    assert code == 2


def test_text_output_shows_arrow(capsys):
    with _open(ENV_A, ENV_B):
        run_trace(_ns(fmt="text"))
    out = capsys.readouterr().out
    assert "->" in out


def test_json_output_is_parseable(capsys):
    import json

    with _open(ENV_A, ENV_B):
        run_trace(_ns(fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "events" in data


def test_no_changes_text_message(capsys):
    with _open(ENV_SAME, ENV_SAME):
        run_trace(_ns(fmt="text"))
    out = capsys.readouterr().out
    assert "No changes" in out


def test_build_parser_returns_parser():
    p = build_trace_parser()
    assert isinstance(p, argparse.ArgumentParser)
