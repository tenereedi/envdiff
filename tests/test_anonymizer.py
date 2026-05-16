"""Tests for envdiff.anonymizer."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.anonymizer import anonymize, AnonymizeResult, AnonymizedEntry

ENV_TEXT = """\
APP_NAME=myapp
SECRET_KEY=supersecret
DB_PASSWORD=hunter2
DEBUG=true
API_TOKEN=abc123
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return anonymize(parsed, salt="testsalt")


def test_returns_anonymize_result(result):
    assert isinstance(result, AnonymizeResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(result, parsed):
    assert len(result.entries) == len(
        [e for e in parsed.entries if e.key is not None]
    )


def test_secret_keys_are_anonymized(result):
    secret_entries = [e for e in result.entries if e.is_secret]
    assert len(secret_entries) > 0
    for entry in secret_entries:
        assert entry.anonymized_value.startswith("REDACTED_")
        assert entry.anonymized_value != entry.original_value


def test_non_secret_keys_unchanged(result):
    plain = [e for e in result.entries if not e.is_secret]
    assert len(plain) > 0
    for entry in plain:
        assert entry.anonymized_value == entry.original_value


def test_token_map_contains_secret_values(result):
    secret_originals = {
        e.original_value for e in result.entries if e.is_secret
    }
    assert secret_originals == set(result.token_map.keys())


def test_token_is_deterministic(parsed):
    r1 = anonymize(parsed, salt="same")
    r2 = anonymize(parsed, salt="same")
    for e1, e2 in zip(r1.entries, r2.entries):
        assert e1.anonymized_value == e2.anonymized_value


def test_different_salts_produce_different_tokens(parsed):
    r1 = anonymize(parsed, salt="salt_a")
    r2 = anonymize(parsed, salt="salt_b")
    secret_keys = [e.key for e in r1.entries if e.is_secret]
    assert len(secret_keys) > 0
    for key in secret_keys:
        v1 = next(e.anonymized_value for e in r1.entries if e.key == key)
        v2 = next(e.anonymized_value for e in r2.entries if e.key == key)
        assert v1 != v2


def test_to_env_string_contains_all_keys(result):
    env_str = result.to_env_string()
    for entry in result.entries:
        assert entry.key in env_str


def test_to_env_string_has_no_original_secrets(result):
    env_str = result.to_env_string()
    for entry in result.entries:
        if entry.is_secret:
            assert entry.original_value not in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "entries" in d
    assert "token_map" in d
    assert isinstance(d["entries"], list)
