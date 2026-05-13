"""Tests for envdiff.summarizer."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.summarizer import summarize, SummaryResult, SummaryStats


ENV_TEXT = """\
# Database config
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=supersecret

API_KEY=abc123
DEBUG=true
EMPTY_VAL=
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return summarize(parsed)


def test_returns_summary_result(result):
    assert isinstance(result, SummaryResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_stats_is_summary_stats(result):
    assert isinstance(result.stats, SummaryStats)


def test_total_keys(result):
    assert result.stats.total_keys == 6


def test_secret_keys_detected(result):
    # DB_PASSWORD and API_KEY should be flagged as secrets
    assert result.stats.secret_keys >= 1
    assert "DB_PASSWORD" in result.secret_key_names or "API_KEY" in result.secret_key_names


def test_plain_keys_count(result):
    assert result.stats.plain_keys == result.stats.total_keys - result.stats.secret_keys


def test_empty_values_detected(result):
    assert result.stats.empty_values == 1
    assert "EMPTY_VAL" in result.empty_key_names


def test_as_dict_has_expected_keys(result):
    d = result.as_dict()
    assert "source" in d
    assert "stats" in d
    assert "secret_key_names" in d
    assert "empty_key_names" in d


def test_stats_as_dict_structure(result):
    sd = result.stats.as_dict()
    for key in ("total_keys", "secret_keys", "plain_keys", "empty_values", "comment_lines", "blank_lines"):
        assert key in sd


def test_to_text_contains_source(result):
    text = result.to_text()
    assert "test.env" in text


def test_to_text_contains_key_counts(result):
    text = result.to_text()
    assert "6" in text


def test_empty_env_summary():
    parsed = parse_env_string("", source="empty.env")
    result = summarize(parsed)
    assert result.stats.total_keys == 0
    assert result.stats.secret_keys == 0
    assert result.stats.empty_values == 0
