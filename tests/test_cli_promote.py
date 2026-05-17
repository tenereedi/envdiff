"""Tests for envdiff.cli_promote."""
import argparse
from unittest.mock import mock_open, patch

import pytest

from envdiff.cli_promote import run_promote


@pytest.fixture
def src_env_file(tmp_path):
    f = tmp_path / "prod.env"
    f.write_text("APP_ENV=production\nSECRET_KEY=abc123\nDB_HOST=prod-db\n")
    return f


@pytest.fixture
def tgt_env_file(tmp_path):
    f = tmp_path / "staging.env"
    f.write_text("APP_ENV=staging\nDB_HOST=staging-db\n")
    return f


def _ns(**kwargs):
    defaults = {
        "keys": None,
        "overwrite": False,
        "conflict": False,
        "output_format": "text",
        "output": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_new_key_promoted_returns_zero(src_env_file, tgt_env_file):
    ns = _ns(source=str(src_env_file), target=str(tgt_env_file))
    assert run_promote(ns) == 0


def test_conflict_returns_one(src_env_file, tgt_env_file):
    ns = _ns(source=str(src_env_file), target=str(tgt_env_file), conflict=True)
    assert run_promote(ns) == 1


def test_missing_source_returns_two(tmp_path, tgt_env_file):
    ns = _ns(source=str(tmp_path / "missing.env"), target=str(tgt_env_file))
    assert run_promote(ns) == 2


def test_missing_target_returns_two(src_env_file, tmp_path):
    ns = _ns(source=str(src_env_file), target=str(tmp_path / "missing.env"))
    assert run_promote(ns) == 2


def test_json_output_is_valid(src_env_file, tgt_env_file, capsys):
    import json
    ns = _ns(source=str(src_env_file), target=str(tgt_env_file), output_format="json")
    run_promote(ns)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "entries" in data
    assert "promoted_count" in data


def test_output_file_written(src_env_file, tgt_env_file, tmp_path):
    out_file = tmp_path / "result.env"
    ns = _ns(
        source=str(src_env_file),
        target=str(tgt_env_file),
        overwrite=True,
        output=str(out_file),
    )
    run_promote(ns)
    assert out_file.exists()
    content = out_file.read_text()
    assert "SECRET_KEY" in content


def test_specific_keys_only_promotes_subset(src_env_file, tgt_env_file, capsys):
    ns = _ns(
        source=str(src_env_file),
        target=str(tgt_env_file),
        keys=["SECRET_KEY"],
        output_format="json",
    )
    run_promote(ns)
    import json
    data = json.loads(capsys.readouterr().out)
    assert len(data["entries"]) == 1
    assert data["entries"][0]["key"] == "SECRET_KEY"
