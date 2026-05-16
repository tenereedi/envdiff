"""Tests for envdiff.stripper."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.stripper import StripResult, strip


RAW_ENV = """
# This is a top-level comment
DB_HOST=localhost
DB_PORT=5432

# Another comment
SECRET_KEY=abc123
DEBUG=true
""".strip()


@pytest.fixture()
def parsed():
    return parse_env_string(RAW_ENV, source="test.env")


@pytest.fixture()
def result(parsed):
    return strip(parsed)


def test_strip_returns_strip_result(result):
    assert isinstance(result, StripResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_only_kv_entries_remain(result):
    keys = [e.key for e in result.entries]
    assert keys == ["DB_HOST", "DB_PORT", "SECRET_KEY", "DEBUG"]


def test_removed_comments_count(result):
    assert result.removed_comments == 2


def test_removed_blanks_count(result):
    # RAW_ENV has one blank line between the two comment blocks
    assert result.removed_blanks >= 1


def test_no_comment_keys_in_entries(result):
    for entry in result.entries:
        assert not entry.key.startswith("#")


def test_to_env_string_contains_all_keys(result):
    output = result.to_env_string()
    assert "DB_HOST=localhost" in output
    assert "SECRET_KEY=abc123" in output
    assert "#" not in output


def test_keep_blanks_preserves_blank_entries(parsed):
    result = strip(parsed, keep_blanks=True)
    blank_entries = [e for e in result.entries if e.key == ""]
    assert len(blank_entries) >= 1


def test_as_dict_structure(result):
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert "removed_comments" in d
    assert "removed_blanks" in d
    assert "entry_count" in d
    assert isinstance(d["entries"], list)


def test_as_dict_entry_count_matches_entries(result):
    d = result.as_dict()
    assert d["entry_count"] == len(result.entries)


def test_empty_env_produces_zero_counts():
    parsed = parse_env_string("", source="empty.env")
    result = strip(parsed)
    assert result.removed_comments == 0
    assert result.removed_blanks == 0
    assert result.entries == []
