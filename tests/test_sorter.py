"""Tests for envdiff.sorter."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.sorter import SortBy, SortOrder, SortResult, sort


ENV_TEXT = """
# database config
ZEBRA=last
APPLE=first
MANGO=middle
# trailing comment
""".strip()


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return sort(parsed)


def test_returns_sort_result(result):
    assert isinstance(result, SortResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_default_sort_by_key_asc(result):
    keys = [e.key for e in result.entries if e.key is not None]
    assert keys == sorted(keys, key=str.lower)


def test_sort_by_key_desc(parsed):
    r = sort(parsed, sort_by=SortBy.KEY, order=SortOrder.DESC)
    keys = [e.key for e in r.entries if e.key is not None]
    assert keys == sorted(keys, key=str.lower, reverse=True)


def test_sort_by_value_asc(parsed):
    r = sort(parsed, sort_by=SortBy.VALUE, order=SortOrder.ASC)
    values = [e.value for e in r.entries if e.key is not None]
    assert values == sorted(values, key=str.lower)


def test_sort_by_line_preserves_original_order(parsed):
    r = sort(parsed, sort_by=SortBy.LINE, order=SortOrder.ASC)
    lines = [e.line for e in r.entries if e.key is not None]
    assert lines == sorted(lines)


def test_comments_first_places_non_kv_at_top(parsed):
    r = sort(parsed, comments_first=True)
    non_kv_indices = [i for i, e in enumerate(r.entries) if e.key is None]
    kv_indices = [i for i, e in enumerate(r.entries) if e.key is not None]
    if non_kv_indices and kv_indices:
        assert max(non_kv_indices) < min(kv_indices)


def test_to_env_string_contains_all_keys(result):
    env_str = result.to_env_string()
    assert "APPLE" in env_str
    assert "ZEBRA" in env_str
    assert "MANGO" in env_str


def test_as_dict_contains_expected_fields(result):
    d = result.as_dict()
    assert "source" in d
    assert "sort_by" in d
    assert "order" in d
    assert "entry_count" in d
    assert "keys" in d


def test_as_dict_sort_by_matches_enum_value(parsed):
    r = sort(parsed, sort_by=SortBy.VALUE)
    assert r.as_dict()["sort_by"] == "value"


def test_as_dict_order_matches_enum_value(parsed):
    r = sort(parsed, order=SortOrder.DESC)
    assert r.as_dict()["order"] == "desc"


def test_entry_count_matches_kv_plus_non_kv(parsed, result):
    assert result.as_dict()["entry_count"] == len(result.entries)
