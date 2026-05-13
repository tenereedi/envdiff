"""Tests for envdiff.normalizer."""

import pytest
from envdiff.parser import parse_env_string
from envdiff.normalizer import normalize, NormalizeResult


CLEAN_ENV = """ALPHA=one
BETA=two
GAMMA=three
"""

DUPLICATE_ENV = """ALPHA=first
BETA=second
ALPHA=overridden
"""

UNSORTED_ENV = """ZEBRA=last
APPLE=first
MIDDLE=mid
"""

WHITESPACE_ENV = """KEY=  value with spaces  
OTHER=clean
"""


@pytest.fixture
def clean_parsed():
    return parse_env_string(CLEAN_ENV, source="clean.env")


@pytest.fixture
def duplicate_parsed():
    return parse_env_string(DUPLICATE_ENV, source="dup.env")


@pytest.fixture
def unsorted_parsed():
    return parse_env_string(UNSORTED_ENV, source="unsorted.env")


@pytest.fixture
def whitespace_parsed():
    return parse_env_string(WHITESPACE_ENV, source="ws.env")


def test_normalize_returns_normalize_result(clean_parsed):
    result = normalize(clean_parsed)
    assert isinstance(result, NormalizeResult)


def test_source_preserved(clean_parsed):
    result = normalize(clean_parsed)
    assert result.source == "clean.env"


def test_no_duplicates_in_clean_env(clean_parsed):
    result = normalize(clean_parsed)
    assert result.removed_duplicates == []


def test_duplicate_key_removed(duplicate_parsed):
    result = normalize(duplicate_parsed)
    assert "ALPHA" in result.removed_duplicates


def test_duplicate_keeps_last_value(duplicate_parsed):
    result = normalize(duplicate_parsed)
    keys = {e.key: e.value for e in result.entries}
    assert keys["ALPHA"] == "overridden"


def test_entry_count_reduced_on_duplicate(duplicate_parsed):
    result = normalize(duplicate_parsed)
    assert len(result.entries) == 2


def test_sort_keys_true_orders_alphabetically(unsorted_parsed):
    result = normalize(unsorted_parsed, sort_keys=True)
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_sort_keys_false_preserves_order(unsorted_parsed):
    result = normalize(unsorted_parsed, sort_keys=False)
    keys = [e.key for e in result.entries]
    assert keys == ["ZEBRA", "APPLE", "MIDDLE"]


def test_value_whitespace_trimmed(whitespace_parsed):
    result = normalize(whitespace_parsed)
    keys = {e.key: e.value for e in result.entries}
    assert keys["KEY"] == "value with spaces"


def test_to_env_string_contains_keys(clean_parsed):
    result = normalize(clean_parsed)
    env_str = result.to_env_string()
    assert "ALPHA=one" in env_str
    assert "BETA=two" in env_str


def test_as_dict_structure(clean_parsed):
    result = normalize(clean_parsed)
    d = result.as_dict()
    assert "source" in d
    assert "entry_count" in d
    assert "removed_duplicates" in d
    assert "trimmed_keys" in d
    assert "entries" in d
