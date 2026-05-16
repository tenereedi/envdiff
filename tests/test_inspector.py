"""Tests for envdiff.inspector."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.inspector import inspect, InspectResult, InspectStats, InspectEntry


ENV_TEXT = """
DB_HOST=localhost
DB_PASSWORD=supersecret
API_KEY=abc123
DEBUG=true
EMPTY_VAR=
""".strip()


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return inspect(parsed)


def test_returns_inspect_result(result):
    assert isinstance(result, InspectResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(result):
    assert len(result.entries) == 5


def test_stats_is_inspect_stats(result):
    assert isinstance(result.stats, InspectStats)


def test_stats_total(result):
    assert result.stats.total == 5


def test_stats_empty_count(result):
    assert result.stats.empty == 1


def test_secret_keys_flagged(result):
    secret_keys = {e.key for e in result.entries if e.is_secret}
    assert "DB_PASSWORD" in secret_keys
    assert "API_KEY" in secret_keys


def test_non_secret_keys_not_flagged(result):
    non_secret = {e.key for e in result.entries if not e.is_secret}
    assert "DB_HOST" in non_secret
    assert "DEBUG" in non_secret


def test_empty_var_flagged(result):
    empty_entries = [e for e in result.entries if e.is_empty]
    assert len(empty_entries) == 1
    assert empty_entries[0].key == "EMPTY_VAR"


def test_category_secret(result):
    pw_entry = next(e for e in result.entries if e.key == "DB_PASSWORD")
    assert pw_entry.category == "secret"


def test_category_empty(result):
    empty_entry = next(e for e in result.entries if e.key == "EMPTY_VAR")
    assert empty_entry.category == "empty"


def test_category_normal(result):
    debug_entry = next(e for e in result.entries if e.key == "DEBUG")
    assert debug_entry.category == "normal"


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "stats" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_stats_normal_count(result):
    # DB_HOST, DEBUG are normal (not secret, not empty)
    assert result.stats.normal == 2


def test_entry_as_dict_keys(result):
    entry_dict = result.entries[0].as_dict()
    for key in ("key", "value", "line_number", "is_secret", "is_empty", "category"):
        assert key in entry_dict
