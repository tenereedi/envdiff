"""Tests for envdiff.truncator."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.truncator import (
    TruncateResult,
    TruncatedEntry,
    truncate,
    DEFAULT_MAX_LENGTH,
    TRUNCATION_SUFFIX,
)

ENV_CONTENT = """
SHORT=hi
MEDIUM=hello_world
LONG=this_is_a_very_long_value_that_exceeds_the_default_maximum_length_setting
EMPTY=
""".strip()


@pytest.fixture
def parsed():
    return parse_env_string(ENV_CONTENT, source="test.env")


@pytest.fixture
def result(parsed):
    return truncate(parsed)


def test_returns_truncate_result(result):
    assert isinstance(result, TruncateResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(result, parsed):
    from envdiff.parser import EnvEntry
    kv_count = sum(1 for e in parsed.entries if isinstance(e, EnvEntry))
    assert result.total_count == kv_count


def test_short_value_not_truncated(result):
    entry = next(e for e in result.entries if e.key == "SHORT")
    assert not entry.was_truncated
    assert entry.display_value == "hi"
    assert entry.original_value == "hi"


def test_long_value_is_truncated(result):
    entry = next(e for e in result.entries if e.key == "LONG")
    assert entry.was_truncated
    assert len(entry.display_value) == DEFAULT_MAX_LENGTH
    assert entry.display_value.endswith(TRUNCATION_SUFFIX)


def test_truncated_count(result):
    assert result.truncated_count == 1


def test_custom_max_length(parsed):
    r = truncate(parsed, max_length=10)
    long_entry = next(e for e in r.entries if e.key == "LONG")
    assert len(long_entry.display_value) == 10
    assert long_entry.display_value.endswith(TRUNCATION_SUFFIX)


def test_empty_value_not_truncated(result):
    entry = next(e for e in result.entries if e.key == "EMPTY")
    assert not entry.was_truncated
    assert entry.display_value == ""


def test_to_env_string(result):
    env_str = result.to_env_string()
    assert "SHORT=hi" in env_str
    assert "LONG=" in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "max_length" in d
    assert "truncated_count" in d
    assert "total_count" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_entry_as_dict_keys(result):
    entry_dict = result.entries[0].as_dict()
    assert set(entry_dict.keys()) == {"key", "original_value", "display_value", "was_truncated", "line"}


def test_invalid_max_length_raises(parsed):
    with pytest.raises(ValueError):
        truncate(parsed, max_length=2)
