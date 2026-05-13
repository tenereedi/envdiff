"""Tests for envdiff.classifier."""

import pytest
from envdiff.parser import parse_env_string
from envdiff.classifier import classify, ClassifyResult, ClassifiedEntry


ENV_TEXT = """\
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET=supersecret
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
FEATURE_DARK_MODE=true
LOG_LEVEL=info
APP_NAME=myapp
EMAIL_HOST=smtp.example.com
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return classify(parsed)


def test_classify_returns_classify_result(result):
    assert isinstance(result, ClassifyResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(result, parsed):
    assert len(result.entries) == len(parsed.entries)


def test_entries_are_classified_entries(result):
    for entry in result.entries:
        assert isinstance(entry, ClassifiedEntry)


def test_database_keys_classified(result):
    db_keys = result.categories.get("database", [])
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys


def test_auth_keys_classified(result):
    auth_keys = result.categories.get("auth", [])
    assert "JWT_SECRET" in auth_keys


def test_cloud_keys_classified(result):
    cloud_keys = result.categories.get("cloud", [])
    assert "AWS_ACCESS_KEY_ID" in cloud_keys


def test_feature_flag_keys_classified(result):
    flag_keys = result.categories.get("feature_flags", [])
    assert "FEATURE_DARK_MODE" in flag_keys


def test_logging_keys_classified(result):
    log_keys = result.categories.get("logging", [])
    assert "LOG_LEVEL" in log_keys


def test_email_keys_classified(result):
    email_keys = result.categories.get("email", [])
    assert "EMAIL_HOST" in email_keys


def test_general_fallback(result):
    general_keys = result.categories.get("general", [])
    assert "APP_NAME" in general_keys


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "categories" in d
    assert "entries" in d
    assert isinstance(d["categories"], dict)
    assert isinstance(d["entries"], list)


def test_entry_as_dict_keys(result):
    entry_dict = result.entries[0].as_dict()
    assert set(entry_dict.keys()) == {"key", "value", "category", "line_number"}
