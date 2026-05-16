"""Tests for envdiff.cli_freeze."""
import json
import argparse
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from envdiff.cli_freeze import run_freeze
from envdiff.parser import parse_env_string
from envdiff.freezer import freeze


ENV_CONTENT = "DB_HOST=localhost\nSECRET_KEY=abc123\nDEBUG=true\n"


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / "test.env"
    p.write_text(ENV_CONTENT)
    return p


@pytest.fixture
def freeze_file(tmp_path, env_file):
    parsed = parse_env_string(ENV_CONTENT, source=str(env_file))
    result = freeze(parsed)
    p = tmp_path / "freeze.json"
    p.write_text(result.to_json())
    return p


def _ns(**kwargs):
    defaults = {"file": None, "verify": None, "output": "text"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_freeze_returns_zero(env_file):
    args = _ns(file=str(env_file))
    assert run_freeze(args) == 0


def test_missing_file_returns_two(tmp_path):
    args = _ns(file=str(tmp_path / "missing.env"))
    assert run_freeze(args) == 2


def test_json_output_is_valid(env_file, capsys):
    args = _ns(file=str(env_file), output="json")
    code = run_freeze(args)
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "manifest_checksum" in data
    assert "entries" in data


def test_text_output_contains_frozen(env_file, capsys):
    args = _ns(file=str(env_file), output="text")
    run_freeze(args)
    captured = capsys.readouterr()
    assert "Frozen" in captured.out
    assert "Manifest" in captured.out


def test_verify_intact_returns_zero(env_file, freeze_file):
    args = _ns(file=str(env_file), verify=str(freeze_file))
    assert run_freeze(args) == 0


def test_verify_missing_freeze_file_returns_two(env_file, tmp_path):
    args = _ns(file=str(env_file), verify=str(tmp_path / "missing.json"))
    assert run_freeze(args) == 2


def test_verify_tampered_returns_one(env_file, freeze_file, tmp_path):
    tampered = tmp_path / "tampered.env"
    tampered.write_text("DB_HOST=localhost\nSECRET_KEY=CHANGED\nDEBUG=true\n")
    args = _ns(file=str(tampered), verify=str(freeze_file))
    assert run_freeze(args) == 1


def test_verify_text_shows_intact(env_file, freeze_file, capsys):
    args = _ns(file=str(env_file), verify=str(freeze_file), output="text")
    run_freeze(args)
    captured = capsys.readouterr()
    assert "INTACT" in captured.out


def test_verify_text_shows_tampered_keys(env_file, freeze_file, tmp_path, capsys):
    tampered = tmp_path / "tampered.env"
    tampered.write_text("DB_HOST=localhost\nSECRET_KEY=CHANGED\nDEBUG=true\n")
    args = _ns(file=str(tampered), verify=str(freeze_file), output="text")
    run_freeze(args)
    captured = capsys.readouterr()
    assert "TAMPERED" in captured.out
    assert "SECRET_KEY" in captured.out
