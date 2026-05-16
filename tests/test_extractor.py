"""Tests for envdiff.extractor."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.extractor import ExtractResult, ExtractedEntry, extract

ENV_TEXT = """
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=supersecret
DEBUG=true
APP_NAME=myapp
""".strip()


@pytest.fixture()
def parsed():
    return parse_env_string(ENV_TEXT, source=".env")


@pytest.fixture()
def result(parsed):
    return extract(parsed, ["DB_HOST", "SECRET_KEY", "APP_NAME"])


def test_returns_extract_result(result):
    assert isinstance(result, ExtractResult)


def test_source_preserved(parsed, result):
    assert result.source == parsed.source


def test_found_count_matches_requested_present_keys(result):
    assert result.found_count == 3


def test_missing_count_zero_when_all_present(result):
    assert result.missing_count == 0


def test_entries_are_extracted_entries(result):
    for e in result.entries:
        assert isinstance(e, ExtractedEntry)


def test_extracted_keys_match_requested(result):
    assert [e.key for e in result.entries] == ["DB_HOST", "SECRET_KEY", "APP_NAME"]


def test_extracted_values_correct(result):
    values = {e.key: e.value for e in result.entries}
    assert values["DB_HOST"] == "localhost"
    assert values["SECRET_KEY"] == "supersecret"
    assert values["APP_NAME"] == "myapp"


def test_missing_key_recorded(parsed):
    result = extract(parsed, ["DB_HOST", "NONEXISTENT"])
    assert "NONEXISTENT" in result.missing_keys
    assert result.missing_count == 1


def test_missing_key_not_in_entries(parsed):
    result = extract(parsed, ["DB_HOST", "NONEXISTENT"])
    keys = [e.key for e in result.entries]
    assert "NONEXISTENT" not in keys


def test_duplicate_keys_deduplicated(parsed):
    result = extract(parsed, ["DB_HOST", "DB_HOST", "DEBUG"])
    keys = [e.key for e in result.entries]
    assert keys.count("DB_HOST") == 1


def test_order_of_entries_matches_requested_order(parsed):
    result = extract(parsed, ["APP_NAME", "DB_HOST"])
    assert result.entries[0].key == "APP_NAME"
    assert result.entries[1].key == "DB_HOST"


def test_to_env_string_contains_extracted_keys(result):
    env_str = result.to_env_string()
    assert "DB_HOST=localhost" in env_str
    assert "APP_NAME=myapp" in env_str
    assert "DB_PORT" not in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "found_count" in d
    assert "missing_count" in d
    assert "missing_keys" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_as_dict_entry_structure(result):
    entry_dict = result.as_dict()["entries"][0]
    assert "key" in entry_dict
    assert "value" in entry_dict
    assert "original_line" in entry_dict
    assert "was_requested" in entry_dict
    assert entry_dict["was_requested"] is True


def test_empty_keys_list_returns_empty_result(parsed):
    result = extract(parsed, [])
    assert result.found_count == 0
    assert result.missing_count == 0
