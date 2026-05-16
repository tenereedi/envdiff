"""Tests for envdiff.deduplicator."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.deduplicator import deduplicate, DeduplicateResult, DuplicateGroup


ENV_NO_DUPES = """APP_ENV=production
DATABASE_URL=postgres://localhost/db
SECRET_KEY=abc123
"""

ENV_WITH_DUPES = """APP_ENV=production
DATABASE_URL=postgres://localhost/db
APP_ENV=staging
SECRET_KEY=abc123
DATABASE_URL=postgres://remotehost/db
"""


@pytest.fixture
def parsed_clean():
    return parse_env_string(ENV_NO_DUPES, source="clean.env")


@pytest.fixture
def parsed_dupes():
    return parse_env_string(ENV_WITH_DUPES, source="dupes.env")


def test_deduplicate_returns_deduplicate_result(parsed_clean):
    result = deduplicate(parsed_clean)
    assert isinstance(result, DeduplicateResult)


def test_source_preserved(parsed_clean):
    result = deduplicate(parsed_clean)
    assert result.source == "clean.env"


def test_no_duplicates_has_duplicates_false(parsed_clean):
    result = deduplicate(parsed_clean)
    assert result.has_duplicates is False


def test_no_duplicates_entry_count_unchanged(parsed_clean):
    result = deduplicate(parsed_clean)
    assert len(result.entries) == 3


def test_duplicates_detected(parsed_dupes):
    result = deduplicate(parsed_dupes)
    assert result.has_duplicates is True


def test_duplicate_keys_list(parsed_dupes):
    result = deduplicate(parsed_dupes)
    assert set(result.duplicate_keys) == {"APP_ENV", "DATABASE_URL"}


def test_keep_last_selects_last_value(parsed_dupes):
    result = deduplicate(parsed_dupes, keep="last")
    values = {e.key: e.value for e in result.entries}
    assert values["APP_ENV"] == "staging"
    assert values["DATABASE_URL"] == "postgres://remotehost/db"


def test_keep_first_selects_first_value(parsed_dupes):
    result = deduplicate(parsed_dupes, keep="first")
    values = {e.key: e.value for e in result.entries}
    assert values["APP_ENV"] == "production"
    assert values["DATABASE_URL"] == "postgres://localhost/db"


def test_deduped_entry_count(parsed_dupes):
    result = deduplicate(parsed_dupes)
    assert len(result.entries) == 3


def test_invalid_keep_raises(parsed_clean):
    with pytest.raises(ValueError, match="keep must be"):
        deduplicate(parsed_clean, keep="middle")


def test_as_dict_structure(parsed_dupes):
    result = deduplicate(parsed_dupes)
    d = result.as_dict()
    assert "source" in d
    assert "entry_count" in d
    assert "has_duplicates" in d
    assert "duplicate_count" in d
    assert "duplicates" in d


def test_duplicate_group_as_dict(parsed_dupes):
    result = deduplicate(parsed_dupes)
    group = result.duplicates[0]
    gd = group.as_dict()
    assert "key" in gd
    assert "occurrences" in gd
    assert "line_numbers" in gd
    assert gd["occurrences"] == 2


def test_to_env_string_contains_keys(parsed_dupes):
    result = deduplicate(parsed_dupes, keep="last")
    env_str = result.to_env_string()
    assert "APP_ENV=staging" in env_str
    assert "DATABASE_URL=postgres://remotehost/db" in env_str


def test_order_preserved_keep_first(parsed_dupes):
    result = deduplicate(parsed_dupes, keep="first")
    keys = [e.key for e in result.entries]
    assert keys.index("APP_ENV") < keys.index("DATABASE_URL")
