"""Tests for envdiff.pruner."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.pruner import PruneResult, prune


ENV_TEXT = """\
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=secret
AWS_ACCESS_KEY_ID=AKIA123
AWS_SECRET_ACCESS_KEY=abc123
APP_ENV=production
DEBUG=false
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return prune(parsed, keys=["DEBUG"], patterns=["AWS_*"], prefixes=["DB_P"])


def test_prune_returns_prune_result(result):
    assert isinstance(result, PruneResult)


def test_source_preserved(parsed, result):
    assert result.source == parsed.source


def test_exact_key_removed(result):
    keys = [e.key for e in result.entries if e.key]
    assert "DEBUG" not in keys


def test_pattern_keys_removed(result):
    keys = [e.key for e in result.entries if e.key]
    assert "AWS_ACCESS_KEY_ID" not in keys
    assert "AWS_SECRET_ACCESS_KEY" not in keys


def test_prefix_keys_removed(result):
    keys = [e.key for e in result.entries if e.key]
    assert "DB_PORT" not in keys
    assert "DB_PASSWORD" not in keys


def test_non_matching_keys_kept(result):
    keys = [e.key for e in result.entries if e.key]
    assert "DB_HOST" in keys
    assert "APP_ENV" in keys


def test_pruned_count(result):
    # DEBUG(1) + AWS_*(2) + DB_P*(2) = 5
    assert result.pruned_count == 5


def test_remaining_count(result):
    assert result.remaining_count == 2  # DB_HOST, APP_ENV


def test_pruned_reasons_exact(result):
    ops = {op.key: op.reason for op in result.pruned}
    assert ops["DEBUG"] == "exact"


def test_pruned_reasons_pattern(result):
    ops = {op.key: op.reason for op in result.pruned}
    assert ops["AWS_ACCESS_KEY_ID"] == "pattern"
    assert ops["AWS_SECRET_ACCESS_KEY"] == "pattern"


def test_pruned_reasons_prefix(result):
    ops = {op.key: op.reason for op in result.pruned}
    assert ops["DB_PORT"] == "prefix"
    assert ops["DB_PASSWORD"] == "prefix"


def test_no_criteria_keeps_all(parsed):
    result = prune(parsed)
    kv_entries = [e for e in parsed.entries if e.key]
    assert result.remaining_count == len(kv_entries)
    assert result.pruned_count == 0


def test_to_env_string_excludes_pruned(result):
    output = result.to_env_string()
    assert "DEBUG" not in output
    assert "AWS_" not in output
    assert "DB_HOST" in output


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "pruned_count" in d
    assert "remaining_count" in d
    assert isinstance(d["pruned"], list)
    assert isinstance(d["entries"], list)
