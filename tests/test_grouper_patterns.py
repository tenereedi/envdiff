"""Additional pattern-matching tests for envdiff.grouper."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.grouper import group_env


ENV = (
    "DB_HOST=localhost\n"
    "DB_PORT=5432\n"
    "REDIS_URL=redis://localhost\n"
    "REDIS_TTL=300\n"
    "SECRET_KEY=abc123\n"
    "API_KEY=xyz\n"
    "LOG_LEVEL=info\n"
)


@pytest.fixture
def parsed():
    return parse_env_string(ENV, source="patterns.env")


def test_wildcard_suffix_pattern(parsed):
    patterns = {"*_KEY": "secrets"}
    result = group_env(parsed, patterns=patterns)
    secrets = [e.key for e in result.entries_for("secrets")]
    assert "SECRET_KEY" in secrets
    assert "API_KEY" in secrets


def test_first_matching_pattern_wins(parsed):
    # Both patterns could match DB_HOST, first should win
    patterns = {"DB_*": "first", "DB_HOST": "second"}
    result = group_env(parsed, patterns=patterns)
    db_host_groups = [
        name
        for name, entries in result.groups.items()
        if any(e.key == "DB_HOST" for e in entries)
    ]
    assert db_host_groups == ["first"]


def test_unmatched_keys_fall_back_to_prefix(parsed):
    patterns = {"DB_*": "database"}
    result = group_env(parsed, patterns=patterns)
    # REDIS_* not in patterns, should fall back to prefix grouping
    assert "REDIS" in result.group_names()


def test_all_keys_assigned_exactly_once(parsed):
    patterns = {"DB_*": "database", "REDIS_*": "cache", "*_KEY": "secrets"}
    result = group_env(parsed, patterns=patterns)
    all_keys = [e.key for entries in result.groups.values() for e in entries]
    parsed_keys = [e.key for e in parsed.entries]
    assert sorted(all_keys) == sorted(parsed_keys)


def test_empty_patterns_dict_uses_prefix(parsed):
    result = group_env(parsed, patterns={})
    assert "DB" in result.group_names()
    assert "REDIS" in result.group_names()


def test_group_entry_line_numbers_preserved(parsed):
    result = group_env(parsed)
    for entries in result.groups.values():
        for e in entries:
            assert e.line_number > 0
