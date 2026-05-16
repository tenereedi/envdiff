"""Tests for envdiff.masker."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.masker import mask, MaskResult, MaskedEntry, DEFAULT_MASK


ENV_TEXT = """
DB_HOST=localhost
DB_PASSWORD=supersecret
API_KEY=abc123
APP_NAME=myapp
SECRET_TOKEN=tok_xyz
""".strip()


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return mask(parsed)


def test_mask_returns_mask_result(result):
    assert isinstance(result, MaskResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_entry_count(result, parsed):
    kv_count = sum(1 for e in parsed.entries if e.key is not None)
    assert result.total_count == kv_count


def test_secret_keys_are_masked(result):
    masked_keys = {e.key for e in result.entries if e.was_masked}
    assert "DB_PASSWORD" in masked_keys
    assert "API_KEY" in masked_keys
    assert "SECRET_TOKEN" in masked_keys


def test_non_secret_keys_are_not_masked(result):
    plain_keys = {e.key for e in result.entries if not e.was_masked}
    assert "DB_HOST" in plain_keys
    assert "APP_NAME" in plain_keys


def test_masked_value_uses_default_token(result):
    for entry in result.entries:
        if entry.was_masked:
            assert entry.masked_value == DEFAULT_MASK


def test_custom_mask_token(parsed):
    r = mask(parsed, mask_token="[REDACTED]")
    assert r.mask_token == "[REDACTED]"
    for entry in r.entries:
        if entry.was_masked:
            assert entry.masked_value == "[REDACTED]"


def test_explicit_keys_always_masked(parsed):
    r = mask(parsed, keys=["APP_NAME"], auto_detect=False)
    masked_keys = {e.key for e in r.entries if e.was_masked}
    assert "APP_NAME" in masked_keys
    # auto_detect off — secret-looking keys should NOT be masked
    assert "DB_PASSWORD" not in masked_keys


def test_auto_detect_false_masks_nothing_without_keys(parsed):
    r = mask(parsed, auto_detect=False)
    assert r.masked_count == 0


def test_masked_count_matches_secret_keys(result):
    expected = sum(1 for e in result.entries if e.was_masked)
    assert result.masked_count == expected


def test_to_env_string_contains_mask_token(result):
    env_str = result.to_env_string()
    assert DEFAULT_MASK in env_str


def test_to_env_string_plain_values_intact(result):
    env_str = result.to_env_string()
    assert "APP_NAME=myapp" in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "masked_count" in d
    assert "total_count" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_entry_as_dict_masked_hides_original(result):
    for entry in result.entries:
        d = entry.as_dict()
        if d["was_masked"]:
            assert d["original_value"] is None
        else:
            assert d["original_value"] is not None
