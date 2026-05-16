"""Tests for envdiff.scoper."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.scoper import scope, ScopeResult, ScopedEntry

ENV_TEXT = """
PROD_DB_HOST=prod.db.example.com
PROD_DB_PASSWORD=s3cr3t
PROD_API_KEY=apikey123
STAGING_DB_HOST=staging.db.example.com
COMMON_TIMEOUT=30
""".strip()


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="prod.env")


@pytest.fixture
def result(parsed):
    return scope(parsed, "PROD")


def test_returns_scope_result(result):
    assert isinstance(result, ScopeResult)


def test_source_preserved(result):
    assert result.source == "prod.env"


def test_scope_stored(result):
    assert result.scope == "PROD"


def test_matched_count(result):
    assert len(result.entries) == 3


def test_excluded_count(result, parsed):
    total_kv = sum(1 for e in parsed.entries if e.key is not None)
    assert result.excluded_count == total_kv - len(result.entries)


def test_entries_are_scoped_entry_instances(result):
    for e in result.entries:
        assert isinstance(e, ScopedEntry)


def test_original_keys_retain_prefix(result):
    for e in result.entries:
        assert e.original_key.startswith("PROD_")


def test_strip_prefix_false_keeps_original_key(result):
    assert result.strip_prefix is False
    assert all(e.scoped_key == e.original_key for e in result.entries)


def test_strip_prefix_true_removes_prefix(parsed):
    r = scope(parsed, "PROD", strip_prefix=True)
    keys = [e.scoped_key for e in r.entries]
    assert "DB_HOST" in keys
    assert "DB_PASSWORD" in keys
    assert "API_KEY" in keys


def test_secret_keys_flagged(result):
    password_entry = next(e for e in result.entries if "PASSWORD" in e.original_key)
    assert password_entry.is_secret is True


def test_non_secret_keys_not_flagged(result):
    host_entry = next(e for e in result.entries if "HOST" in e.original_key)
    assert host_entry.is_secret is False


def test_to_env_string_no_strip(result):
    output = result.to_env_string()
    assert "PROD_DB_HOST=prod.db.example.com" in output
    assert "STAGING" not in output


def test_to_env_string_with_strip(parsed):
    r = scope(parsed, "PROD", strip_prefix=True)
    output = r.to_env_string()
    assert "DB_HOST=prod.db.example.com" in output
    assert "PROD_" not in output


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "scope" in d
    assert "matched_count" in d
    assert "excluded_count" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_empty_scope_matches_nothing(parsed):
    r = scope(parsed, "NONEXISTENT")
    assert len(r.entries) == 0
    assert r.excluded_count > 0
