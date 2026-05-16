"""Tests for envdiff.cli_encode."""
import argparse
import json
import pytest
from unittest.mock import mock_open, patch, MagicMock

from envdiff.cli_encode import build_encode_parser, run_encode


RAW_ENV = "APP_ENV=production\nDB_HOST=localhost\nSECRET_KEY=abc123\n"


def _ns(**kwargs):
    defaults = {"file": "test.env", "fmt": "json", "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(RAW_ENV)
    return str(p)


def test_returns_zero_on_valid_file(env_file):
    ns = _ns(file=env_file)
    assert run_encode(ns) == 0


def test_missing_file_returns_two():
    ns = _ns(file="/nonexistent/.env")
    assert run_encode(ns) == 2


def test_json_output_is_valid(env_file, capsys):
    ns = _ns(file=env_file, fmt="json")
    run_encode(ns)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["APP_ENV"] == "production"


def test_base64_output_printed(env_file, capsys):
    ns = _ns(file=env_file, fmt="base64")
    run_encode(ns)
    captured = capsys.readouterr()
    # base64 strings only contain alphanumeric + /+=
    import base64 as b64
    decoded = b64.b64decode(captured.out.strip()).decode()
    assert "APP_ENV=production" in decoded


def test_csv_output_has_header(env_file, capsys):
    ns = _ns(file=env_file, fmt="csv")
    run_encode(ns)
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0] == "key,value"


def test_output_to_file(env_file, tmp_path):
    out = str(tmp_path / "out.json")
    ns = _ns(file=env_file, fmt="json", output=out)
    code = run_encode(ns)
    assert code == 0
    with open(out) as fh:
        data = json.load(fh)
    assert "APP_ENV" in data


def test_build_encode_parser_returns_parser():
    p = build_encode_parser()
    assert isinstance(p, argparse.ArgumentParser)
