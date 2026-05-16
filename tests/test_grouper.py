"""Tests for envdiff.grouper."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.grouper import group_env, GroupResult, GroupEntry

ENV_TEXT = """
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=secret
AWS_ACCESS_KEY_ID=AKIA1234
AWS_SECRET_ACCESS_KEY=abc123
APP_ENV=production
APP_DEBUG=false
PORT=8080
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return group_env(parsed)


def test_returns_group_result(result):
    assert isinstance(result, GroupResult)


def test_source_preserved(parsed, result):
    assert result.source == parsed.source


def test_default_grouping_by_prefix(result):
    assert "DB" in result.group_names()
    assert "AWS" in result.group_names()
    assert "APP" in result.group_names()


def test_no_underscore_key_goes_to_default(result):
    assert "DEFAULT" in result.group_names()
    port_entries = result.entries_for("DEFAULT")
    assert any(e.key == "PORT" for e in port_entries)


def test_entries_for_db_group(result):
    db_entries = result.entries_for("DB")
    keys = [e.key for e in db_entries]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "DB_PASSWORD" in keys


def test_custom_patterns(parsed):
    patterns = {"DB_*": "database", "AWS_*": "cloud", "APP_*": "application"}
    result = group_env(parsed, patterns=patterns)
    assert "database" in result.group_names()
    assert "cloud" in result.group_names()
    assert "application" in result.group_names()


def test_custom_pattern_entries(parsed):
    patterns = {"DB_*": "database", "AWS_*": "cloud"}
    result = group_env(parsed, patterns=patterns)
    db = result.entries_for("database")
    assert all(e.key.startswith("DB_") for e in db)


def test_group_entry_as_dict(result):
    db_entries = result.entries_for("DB")
    d = db_entries[0].as_dict()
    assert "key" in d
    assert "value" in d
    assert "group" in d
    assert "line_number" in d


def test_result_as_dict(result):
    d = result.as_dict()
    assert d["source"] == "test.env"
    assert isinstance(d["groups"], dict)


def test_group_names_sorted(result):
    names = result.group_names()
    assert names == sorted(names)


def test_empty_env():
    parsed = parse_env_string("", source="empty.env")
    result = group_env(parsed)
    assert result.groups == {}
    assert result.group_names() == []
