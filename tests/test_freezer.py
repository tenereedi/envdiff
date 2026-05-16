"""Tests for envdiff.freezer."""
import json
import pytest

from envdiff.parser import parse_env_string
from envdiff.freezer import freeze, verify, FreezeResult, FrozenEntry


ENV_TEXT = """DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=supersecret
DEBUG=false
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="prod.env")


@pytest.fixture
def result(parsed):
    return freeze(parsed)


def test_freeze_returns_freeze_result(result):
    assert isinstance(result, FreezeResult)


def test_source_preserved(result):
    assert result.source == "prod.env"


def test_entry_count(result, parsed):
    kv_count = sum(1 for e in parsed.entries if e.key is not None)
    assert len(result.entries) == kv_count


def test_entries_are_frozen_entry(result):
    for entry in result.entries:
        assert isinstance(entry, FrozenEntry)


def test_each_entry_has_checksum(result):
    for entry in result.entries:
        assert isinstance(entry.checksum, str)
        assert len(entry.checksum) == 16


def test_manifest_checksum_is_set(result):
    assert isinstance(result.manifest_checksum, str)
    assert len(result.manifest_checksum) == 32


def test_frozen_at_is_iso(result):
    assert "T" in result.frozen_at


def test_is_intact_true_when_no_tampering(result):
    assert result.is_intact is True


def test_tampered_keys_empty_initially(result):
    assert result.tampered_keys == []


def test_verify_intact_env(parsed, result):
    verified = verify(parsed, result)
    assert verified.is_intact is True
    assert verified.tampered_keys == []


def test_verify_detects_changed_value(result):
    tampered_text = ENV_TEXT.replace("supersecret", "CHANGED_VALUE")
    tampered_parsed = parse_env_string(tampered_text, source="prod.env")
    verified = verify(tampered_parsed, result)
    assert not verified.is_intact
    assert "SECRET_KEY" in verified.tampered_keys


def test_verify_detects_missing_key(result):
    reduced_text = "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=false\n"
    reduced_parsed = parse_env_string(reduced_text, source="prod.env")
    verified = verify(reduced_parsed, result)
    assert "SECRET_KEY" in verified.tampered_keys


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "frozen_at" in d
    assert "manifest_checksum" in d
    assert "is_intact" in d
    assert "tampered_keys" in d
    assert "entries" in d


def test_to_json_is_valid(result):
    raw = result.to_json()
    parsed_json = json.loads(raw)
    assert parsed_json["source"] == "prod.env"
    assert isinstance(parsed_json["entries"], list)
