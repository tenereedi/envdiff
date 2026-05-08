"""Tests for envdiff.redactor."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.redactor import redact, DEFAULT_MASK, RedactResult


ENV_TEXT = """\
APP_NAME=myapp
SECRET_KEY=supersecret
DB_PASSWORD=hunter2
DEBUG=true
API_TOKEN=tok_abc123
PORT=8080
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source=".env")


def test_redact_returns_redact_result(parsed):
    result = redact(parsed)
    assert isinstance(result, RedactResult)


def test_redact_source_preserved(parsed):
    result = redact(parsed)
    assert result.source == ".env"


def test_secret_keys_are_masked(parsed):
    result = redact(parsed)
    masked = {e.key: e.redacted_value for e in result.entries if e.was_redacted}
    assert "SECRET_KEY" in masked
    assert "DB_PASSWORD" in masked
    assert "API_TOKEN" in masked
    for val in masked.values():
        assert val == DEFAULT_MASK


def test_non_secret_keys_are_not_masked(parsed):
    result = redact(parsed)
    plain = {e.key: e.redacted_value for e in result.entries if not e.was_redacted}
    assert "APP_NAME" in plain
    assert "DEBUG" in plain
    assert "PORT" in plain
    assert plain["APP_NAME"] == "myapp"


def test_redacted_count(parsed):
    result = redact(parsed)
    assert result.redacted_count == 3


def test_custom_mask(parsed):
    result = redact(parsed, mask="<hidden>")
    for entry in result.entries:
        if entry.was_redacted:
            assert entry.redacted_value == "<hidden>"


def test_extra_keys_are_redacted(parsed):
    result = redact(parsed, extra_keys=["APP_NAME"])
    entry = next(e for e in result.entries if e.key == "APP_NAME")
    assert entry.was_redacted
    assert entry.redacted_value == DEFAULT_MASK


def test_keep_keys_are_not_redacted(parsed):
    result = redact(parsed, keep_keys=["SECRET_KEY"])
    entry = next(e for e in result.entries if e.key == "SECRET_KEY")
    assert not entry.was_redacted
    assert entry.redacted_value == "supersecret"


def test_to_env_string_contains_all_keys(parsed):
    result = redact(parsed)
    env_str = result.to_env_string()
    for entry in result.entries:
        assert entry.key in env_str


def test_to_env_string_secrets_masked(parsed):
    result = redact(parsed)
    env_str = result.to_env_string()
    assert "supersecret" not in env_str
    assert DEFAULT_MASK in env_str


def test_as_dict_structure(parsed):
    result = redact(parsed)
    d = result.as_dict()
    assert "source" in d
    assert "redacted_count" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)
    first = d["entries"][0]
    assert "key" in first
    assert "was_redacted" in first
    assert "original_value" not in first
