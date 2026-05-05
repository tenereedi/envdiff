"""Tests for envdiff.differ module."""

import pytest

from envdiff.differ import DiffStatus, diff_envs, _mask
from envdiff.parser import parse_env_string


ENV_A = """
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=supersecret
APP_NAME=myapp
"""

ENV_B = """
DB_HOST=prod.example.com
DB_PORT=5432
DB_PASSWORD=anothersecret
NEW_FEATURE=true
"""


@pytest.fixture
def diff():
    return diff_envs(parse_env_string(ENV_A), parse_env_string(ENV_B))


def test_has_differences(diff):
    assert diff.has_differences is True


def test_removed_keys(diff):
    keys = [e.key for e in diff.removed]
    assert "APP_NAME" in keys


def test_added_keys(diff):
    keys = [e.key for e in diff.added]
    assert "NEW_FEATURE" in keys


def test_changed_keys(diff):
    keys = [e.key for e in diff.changed]
    assert "DB_HOST" in keys
    assert "DB_PASSWORD" in keys


def test_unchanged_keys(diff):
    keys = [e.key for e in diff.unchanged]
    assert "DB_PORT" in keys


def test_secret_detection(diff):
    changed = {e.key: e for e in diff.changed}
    assert changed["DB_PASSWORD"].is_secret is True
    assert changed["DB_HOST"].is_secret is False


def test_secret_masking(diff):
    changed = {e.key: e for e in diff.changed}
    entry = changed["DB_PASSWORD"]
    assert entry.masked_value_a() != entry.value_a
    assert entry.masked_value_b() != entry.value_b
    assert "*" in entry.masked_value_a()


def test_non_secret_not_masked(diff):
    changed = {e.key: e for e in diff.changed}
    entry = changed["DB_HOST"]
    assert entry.masked_value_a() == entry.value_a
    assert entry.masked_value_b() == entry.value_b


def test_mask_short_value():
    assert _mask("ab") == "***"
    assert _mask(None) is None


def test_mask_long_value():
    result = _mask("supersecret")
    assert result.startswith("su")
    assert result.endswith("et")
    assert "*" in result


def test_identical_envs():
    env = "FOO=bar\nBAZ=qux\n"
    result = diff_envs(parse_env_string(env), parse_env_string(env))
    assert result.has_differences is False
    assert len(result.unchanged) == 2
