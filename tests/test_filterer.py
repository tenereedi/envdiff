"""Tests for envdiff.filterer."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.filterer import FilterResult, filter_env


ENV_TEXT = """\
DB_HOST=localhost
DB_PASSWORD=s3cr3t
APP_NAME=myapp
API_SECRET_KEY=abc123
DEBUG=true
AWS_ACCESS_KEY_ID=AKIA1234
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


def test_filter_returns_filter_result(parsed):
    result = filter_env(parsed)
    assert isinstance(result, FilterResult)


def test_source_preserved(parsed):
    result = filter_env(parsed)
    assert result.source == "test.env"


def test_no_criteria_returns_all(parsed):
    result = filter_env(parsed)
    assert result.total_after == result.total_before
    assert result.removed_count == 0


def test_pattern_filters_by_glob(parsed):
    result = filter_env(parsed, pattern="DB_*")
    keys = [e.key for e in result.entries]
    assert "DB_HOST" in keys
    assert "DB_PASSWORD" in keys
    assert "APP_NAME" not in keys


def test_pattern_no_match_returns_empty(parsed):
    result = filter_env(parsed, pattern="NONEXISTENT_*")
    assert result.total_after == 0
    assert result.removed_count == result.total_before


def test_secrets_only_keeps_secret_keys(parsed):
    result = filter_env(parsed, secrets_only=True)
    keys = [e.key for e in result.entries]
    assert "DB_PASSWORD" in keys
    assert "API_SECRET_KEY" in keys
    assert "AWS_ACCESS_KEY_ID" in keys
    assert "DEBUG" not in keys
    assert "APP_NAME" not in keys


def test_non_secrets_only_excludes_secret_keys(parsed):
    result = filter_env(parsed, non_secrets_only=True)
    keys = [e.key for e in result.entries]
    assert "DEBUG" in keys
    assert "APP_NAME" in keys
    assert "DB_PASSWORD" not in keys


def test_secrets_only_takes_precedence_over_non_secrets(parsed):
    result = filter_env(parsed, secrets_only=True, non_secrets_only=True)
    keys = [e.key for e in result.entries]
    assert "DB_PASSWORD" in keys
    assert "DEBUG" not in keys


def test_as_dict_structure(parsed):
    result = filter_env(parsed, pattern="DB_*")
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert d["pattern"] == "DB_*"
    assert isinstance(d["entries"], list)
    assert d["total_after"] == len(d["entries"])


def test_to_env_string_format(parsed):
    result = filter_env(parsed, pattern="APP_*")
    env_str = result.to_env_string()
    assert "APP_NAME=myapp" in env_str


def test_removed_count_correct(parsed):
    result = filter_env(parsed, pattern="DB_*")
    assert result.removed_count == result.total_before - result.total_after
