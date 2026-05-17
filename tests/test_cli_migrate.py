"""Tests for envdiff.cli_migrate."""
import argparse
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

from envdiff.cli_migrate import build_migrate_parser, run_migrate, _parse_kv_args


ENV_CONTENT = "APP_HOST=localhost\nAPP_PORT=8080\nSECRET_KEY=abc123\n"


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT)
    return str(p)


def _ns(**kwargs):
    defaults = {
        "rename": [],
        "value_transforms": [],
        "output_format": "text",
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_missing_file_returns_two():
    ns = _ns(file="/nonexistent/.env")
    assert run_migrate(ns) == 2


def test_no_rename_rules_returns_zero(env_file):
    ns = _ns(file=env_file)
    assert run_migrate(ns) == 0


def test_successful_rename_returns_zero(env_file, capsys):
    ns = _ns(file=env_file, rename=["APP_HOST=HOST"])
    code = run_migrate(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "HOST=localhost" in out


def test_collision_returns_one(env_file, capsys):
    # APP_HOST -> SECRET_KEY collides with existing key
    ns = _ns(file=env_file, rename=["APP_HOST=SECRET_KEY"])
    code = run_migrate(ns)
    assert code == 1


def test_json_output_format(env_file, capsys):
    ns = _ns(file=env_file, rename=["APP_HOST=HOST"], output_format="json")
    run_migrate(ns)
    out = capsys.readouterr().out
    import json
    data = json.loads(out)
    assert "migrated_count" in data
    assert data["migrated_count"] == 1


def test_output_written_to_file(env_file, tmp_path):
    out_path = tmp_path / "migrated.env"
    ns = _ns(file=env_file, rename=["APP_HOST=HOST"], output=str(out_path))
    run_migrate(ns)
    assert out_path.exists()
    content = out_path.read_text()
    assert "HOST=localhost" in content


def test_parse_kv_args_basic():
    result = _parse_kv_args(["FOO=BAR", "BAZ=QUX"])
    assert result == {"FOO": "BAR", "BAZ": "QUX"}


def test_parse_kv_args_ignores_malformed():
    result = _parse_kv_args(["NOEQUALSSIGN", "OK=yes"])
    assert "NOEQUALSSIGN" not in result
    assert result["OK"] == "yes"


def test_build_migrate_parser_returns_parser():
    parser = build_migrate_parser()
    assert isinstance(parser, argparse.ArgumentParser)
