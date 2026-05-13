"""Tests for envdiff.cli_compare."""

import argparse
import pytest
from unittest.mock import patch, mock_open
from envdiff.cli_compare import build_compare_parser, run_compare


ENV_A_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\n"
ENV_B_CONTENT = "DB_HOST=prodserver\nDB_PORT=5432\nSECRET_KEY=xyz\n"
ENV_SAME = "DB_HOST=localhost\nDB_PORT=5432\n"


def _ns(**kwargs):
    defaults = {
        "file_a": ".env.dev",
        "file_b": ".env.prod",
        "output_format": "text",
        "no_mask": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _mock_files(content_a, content_b):
    contents = {"a": content_a, "b": content_b}
    call_count = {"n": 0}

    def _open(path, *a, **kw):
        call_count["n"] += 1
        data = content_a if call_count["n"] == 1 else content_b
        return mock_open(read_data=data)()

    return _open


def test_differences_returns_one(tmp_path):
    fa = tmp_path / ".env.dev"
    fb = tmp_path / ".env.prod"
    fa.write_text(ENV_A_CONTENT)
    fb.write_text(ENV_B_CONTENT)
    ns = _ns(file_a=str(fa), file_b=str(fb))
    assert run_compare(ns) == 1


def test_identical_returns_zero(tmp_path):
    fa = tmp_path / ".env.a"
    fb = tmp_path / ".env.b"
    fa.write_text(ENV_SAME)
    fb.write_text(ENV_SAME)
    ns = _ns(file_a=str(fa), file_b=str(fb))
    assert run_compare(ns) == 0


def test_missing_file_returns_two(tmp_path):
    fa = tmp_path / ".env.dev"
    fa.write_text(ENV_A_CONTENT)
    ns = _ns(file_a=str(fa), file_b="nonexistent.env")
    assert run_compare(ns) == 2


def test_json_format_output(tmp_path, capsys):
    fa = tmp_path / ".env.dev"
    fb = tmp_path / ".env.prod"
    fa.write_text(ENV_A_CONTENT)
    fb.write_text(ENV_B_CONTENT)
    ns = _ns(file_a=str(fa), file_b=str(fb), output_format="json")
    run_compare(ns)
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert "stats" in data
    assert "entries" in data


def test_text_format_shows_stats(tmp_path, capsys):
    fa = tmp_path / ".env.dev"
    fb = tmp_path / ".env.prod"
    fa.write_text(ENV_A_CONTENT)
    fb.write_text(ENV_B_CONTENT)
    ns = _ns(file_a=str(fa), file_b=str(fb))
    run_compare(ns)
    captured = capsys.readouterr()
    assert "Stats:" in captured.out


def test_build_compare_parser():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_compare_parser(sub)
    args = root.parse_args(["compare", "a.env", "b.env", "--format", "json"])
    assert args.file_a == "a.env"
    assert args.output_format == "json"
