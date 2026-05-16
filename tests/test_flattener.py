"""Tests for envdiff.flattener."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.flattener import flatten, FlattenResult, FlattenedEntry


ENV_TEXT = """APP_HOST=localhost
APP_PORT=5432
APP_DEBUG=true
SECRET_KEY=abc123
PLAIN=value
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return flatten(parsed, strip_prefix="APP_")


def test_flatten_returns_flatten_result(result):
    assert isinstance(result, FlattenResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(parsed, result):
    kv_count = sum(1 for e in parsed.entries if e.key is not None)
    assert len(result.entries) == kv_count


def test_strip_prefix_stored(result):
    assert result.strip_prefix == "APP_"


def test_prefixed_keys_renamed(result):
    flat_keys = {e.flat_key for e in result.entries}
    assert "HOST" in flat_keys
    assert "PORT" in flat_keys
    assert "DEBUG" in flat_keys


def test_non_prefixed_keys_unchanged(result):
    plain = next(e for e in result.entries if e.original_key == "PLAIN")
    assert plain.flat_key == "PLAIN"
    assert plain.was_renamed is False


def test_was_renamed_true_for_prefixed(result):
    host = next(e for e in result.entries if e.original_key == "APP_HOST")
    assert host.was_renamed is True


def test_renamed_count(result):
    assert result.renamed_count == 3  # APP_HOST, APP_PORT, APP_DEBUG


def test_no_prefix_leaves_all_unchanged(parsed):
    r = flatten(parsed)
    assert r.renamed_count == 0
    for e in r.entries:
        assert e.flat_key == e.original_key
        assert e.was_renamed is False


def test_to_env_string_uses_flat_keys(result):
    env_str = result.to_env_string()
    assert "HOST=localhost" in env_str
    assert "APP_HOST" not in env_str


def test_to_env_string_includes_non_prefixed(result):
    env_str = result.to_env_string()
    assert "PLAIN=value" in env_str
    assert "SECRET_KEY=abc123" in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "strip_prefix" in d
    assert "renamed_count" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_entry_as_dict_fields(result):
    entry_dict = result.entries[0].as_dict()
    assert "original_key" in entry_dict
    assert "flat_key" in entry_dict
    assert "value" in entry_dict
    assert "was_renamed" in entry_dict
