"""Tests for envdiff.tagger."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.tagger import TagResult, TaggedEntry, tag_env

RAW_ENV = """
DB_HOST=localhost
DB_PASSWORD=supersecret
API_KEY=abc123
APP_PORT=8080
DEBUG=true
FEATURE_DARK_MODE=on
SERVICE_URL=https://example.com
APP_NAME=myapp
"""


@pytest.fixture
def parsed():
    return parse_env_string(RAW_ENV.strip(), source="test.env")


@pytest.fixture
def result(parsed):
    return tag_env(parsed)


def test_returns_tag_result(result):
    assert isinstance(result, TagResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(result, parsed):
    assert len(result.entries) == len(parsed.entries)


def test_entries_are_tagged_entry(result):
    for entry in result.entries:
        assert isinstance(entry, TaggedEntry)


def test_db_password_tagged_secret(result):
    tags = result.tags_for_key("DB_PASSWORD")
    assert "secret" in tags


def test_api_key_tagged_secret(result):
    tags = result.tags_for_key("API_KEY")
    assert "secret" in tags


def test_db_host_tagged_database(result):
    tags = result.tags_for_key("DB_HOST")
    assert "database" in tags


def test_port_tagged(result):
    tags = result.tags_for_key("APP_PORT")
    assert "port" in tags


def test_debug_tagged(result):
    tags = result.tags_for_key("DEBUG")
    assert "debug" in tags


def test_feature_flag_tagged(result):
    tags = result.tags_for_key("FEATURE_DARK_MODE")
    assert "feature_flag" in tags


def test_url_tagged(result):
    tags = result.tags_for_key("SERVICE_URL")
    assert "url" in tags


def test_app_name_has_no_tags(result):
    tags = result.tags_for_key("APP_NAME")
    assert tags == []


def test_tag_index_contains_secret(result):
    secret_keys = result.keys_for_tag("secret")
    assert "DB_PASSWORD" in secret_keys
    assert "API_KEY" in secret_keys


def test_all_tags_sorted(result):
    all_tags = result.all_tags()
    assert all_tags == sorted(all_tags)


def test_extra_tags_applied(parsed):
    result = tag_env(parsed, extra_tags={"APP_NAME": ["infra", "core"]})
    tags = result.tags_for_key("APP_NAME")
    assert "infra" in tags
    assert "core" in tags


def test_extra_tags_no_duplicates(parsed):
    result = tag_env(parsed, extra_tags={"DB_PASSWORD": ["secret"]})
    tags = result.tags_for_key("DB_PASSWORD")
    assert tags.count("secret") == 1


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "entries" in d
    assert "tag_index" in d
    assert isinstance(d["entries"], list)
    assert isinstance(d["tag_index"], dict)


def test_entry_as_dict_has_tags(result):
    entry_dict = result.entries[0].as_dict()
    assert "tags" in entry_dict
    assert isinstance(entry_dict["tags"], list)
