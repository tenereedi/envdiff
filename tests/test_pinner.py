"""Tests for envdiff.pinner — pin and drift detection."""
import json
import pytest

from envdiff.parser import parse_env_string
from envdiff.pinner import pin, check_drift, PinResult, PinnedEntry


ENV_A = """DB_HOST=localhost
DB_PASSWORD=s3cr3t
APP_ENV=production
DEBUG=false
"""

ENV_B = """DB_HOST=remotehost
DB_PASSWORD=s3cr3t
APP_ENV=production
DEBUG=true
NEW_KEY=hello
"""


@pytest.fixture
def parsed_a():
    return parse_env_string(ENV_A, source="a.env")


@pytest.fixture
def parsed_b():
    return parse_env_string(ENV_B, source="b.env")


@pytest.fixture
def pinned_a(parsed_a):
    return pin(parsed_a)


def test_pin_returns_pin_result(pinned_a):
    assert isinstance(pinned_a, PinResult)


def test_pin_source_preserved(pinned_a):
    assert pinned_a.source == "a.env"


def test_pin_entry_count(pinned_a):
    assert len(pinned_a.entries) == 4


def test_pin_entries_are_pinned_entry(pinned_a):
    for e in pinned_a.entries:
        assert isinstance(e, PinnedEntry)


def test_secret_key_flagged(pinned_a):
    secret_entries = [e for e in pinned_a.entries if e.key == "DB_PASSWORD"]
    assert len(secret_entries) == 1
    assert secret_entries[0].is_secret is True


def test_non_secret_key_not_flagged(pinned_a):
    entries = [e for e in pinned_a.entries if e.key == "APP_ENV"]
    assert entries[0].is_secret is False


def test_as_dict_masks_secret(pinned_a):
    secret = next(e for e in pinned_a.entries if e.key == "DB_PASSWORD")
    d = secret.as_dict()
    assert d["value"] == "***"


def test_as_dict_shows_non_secret(pinned_a):
    entry = next(e for e in pinned_a.entries if e.key == "APP_ENV")
    d = entry.as_dict()
    assert d["value"] == "production"


def test_no_drift_when_identical(parsed_a, pinned_a):
    result = check_drift(parsed_a, pinned_a)
    assert result.has_drift is False
    assert result.drift_keys == []


def test_drift_detected_on_changed_value(parsed_b, pinned_a):
    result = check_drift(parsed_b, pinned_a)
    assert result.has_drift is True
    assert "DB_HOST" in result.drift_keys


def test_drift_includes_new_keys(parsed_b, pinned_a):
    result = check_drift(parsed_b, pinned_a)
    assert "NEW_KEY" in result.drift_keys


def test_to_json_is_valid(pinned_a):
    output = pinned_a.to_json()
    data = json.loads(output)
    assert "entries" in data
    assert data["source"] == "a.env"
    assert data["has_drift"] is False
