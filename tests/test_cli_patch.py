"""Tests for envdiff.cli_patch."""
import argparse
import pytest
from unittest.mock import patch as mock_patch, mock_open

from envdiff.cli_patch import run_patch, build_patch_parser


SAMPLE_ENV = "APP=myapp\nDEBUG=false\nSECRET=abc\n"


def _ns(**kwargs):
    """Build an argparse.Namespace with sensible defaults for patch tests."""
    defaults = {
        "env_file": ".env",
        "overrides": ["DEBUG=true"],
        "format": "env",
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def env_file(tmp_path):
    """Create a temporary .env file populated with SAMPLE_ENV content."""
    p = tmp_path / ".env"
    p.write_text(SAMPLE_ENV)
    return str(p)


def test_change_returns_zero(env_file):
    args = _ns(env_file=env_file, overrides=["DEBUG=true"])
    assert run_patch(args) == 0


def test_missing_file_returns_two():
    args = _ns(env_file="/no/such/file.env")
    assert run_patch(args) == 2


def test_output_contains_updated_value(env_file, capsys):
    args = _ns(env_file=env_file, overrides=["APP=newapp"])
    run_patch(args)
    out = capsys.readouterr().out
    assert "APP=newapp" in out


def test_removed_key_absent_from_output(env_file, capsys):
    args = _ns(env_file=env_file, overrides=["SECRET="])
    run_patch(args)
    out = capsys.readouterr().out
    assert "SECRET" not in out


def test_json_format_output(env_file, capsys):
    args = _ns(env_file=env_file, overrides=["DEBUG=true"], format="json")
    run_patch(args)
    out = capsys.readouterr().out
    import json
    data = json.loads(out)
    assert "operations" in data
    assert "source" in data


def test_dry_run_returns_zero(env_file, capsys):
    args = _ns(env_file=env_file, overrides=["DEBUG=true"], dry_run=True)
    assert run_patch(args) == 0


def test_dry_run_prints_operations(env_file, capsys):
    args = _ns(env_file=env_file, overrides=["DEBUG=true"], dry_run=True)
    run_patch(args)
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "DEBUG" in out


def test_invalid_override_exits(env_file):
    args = _ns(env_file=env_file, overrides=["NODEQUALS"])
    with pytest.raises(SystemExit) as exc:
        run_patch(args)
    assert exc.value.code == 2


def test_no_overrides_returns_zero(env_file):
    """Patching with an empty override list should succeed without error."""
    args = _ns(env_file=env_file, overrides=[])
    assert run_patch(args) == 0


def test_build_patch_parser_returns_parser():
    p = build_patch_parser()
    assert isinstance(p, argparse.ArgumentParser)
