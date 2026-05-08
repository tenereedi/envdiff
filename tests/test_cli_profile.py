"""Tests for envdiff.cli_profile."""
from __future__ import annotations

import json
from pathlib import Path
from argparse import Namespace

import pytest

from envdiff.cli_profile import run_profile


FULL_WEB = "APP_ENV=prod\nLOG_LEVEL=info\nPORT=8080\nDATABASE_URL=x\nSECRET_KEY=s\n"
PARTIAL = "APP_ENV=dev\nLOG_LEVEL=debug\n"


@pytest.fixture
def full_env_file(tmp_path):
    p = tmp_path / "full.env"
    p.write_text(FULL_WEB)
    return p


@pytest.fixture
def partial_env_file(tmp_path):
    p = tmp_path / "partial.env"
    p.write_text(PARTIAL)
    return p


def _ns(env_file, profile="web", fmt="text"):
    return Namespace(env_file=str(env_file), profile=profile, format=fmt)


def test_compliant_returns_zero(full_env_file):
    assert run_profile(_ns(full_env_file)) == 0


def test_non_compliant_returns_one(partial_env_file):
    assert run_profile(_ns(partial_env_file, profile="web")) == 1


def test_missing_file_returns_two(tmp_path):
    ns = _ns(tmp_path / "no_such.env")
    assert run_profile(ns) == 2


def test_unknown_profile_returns_two(full_env_file):
    ns = _ns(full_env_file, profile="ghost")
    assert run_profile(ns) == 2


def test_json_output_compliant(full_env_file, capsys):
    code = run_profile(_ns(full_env_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["compliant"] is True
    assert data["profile"] == "web"
    assert code == 0


def test_json_output_non_compliant(partial_env_file, capsys):
    code = run_profile(_ns(partial_env_file, profile="web", fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["compliant"] is False
    assert len(data["missing_keys"]) > 0
    assert code == 1


def test_text_output_contains_status(full_env_file, capsys):
    run_profile(_ns(full_env_file, fmt="text"))
    out = capsys.readouterr().out
    assert "COMPLIANT" in out
    assert "web" in out
