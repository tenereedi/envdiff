"""Tests for envdiff.patcher."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.patcher import patch, PatchResult, PatchOperation


RAW = """\
APP_NAME=myapp
DEBUG=false
SECRET_KEY=abc123
DB_HOST=localhost
"""


@pytest.fixture
def parsed():
    return parse_env_string(RAW, source=".env")


def test_patch_returns_patch_result(parsed):
    result = patch(parsed, {})
    assert isinstance(result, PatchResult)


def test_source_preserved(parsed):
    result = patch(parsed, {})
    assert result.source == ".env"


def test_no_ops_when_no_overrides(parsed):
    result = patch(parsed, {})
    assert result.operations == []


def test_changed_key_recorded(parsed):
    result = patch(parsed, {"DEBUG": "true"})
    ops = {op.key: op for op in result.operations}
    assert "DEBUG" in ops
    assert ops["DEBUG"].old_value == "false"
    assert ops["DEBUG"].new_value == "true"


def test_changed_value_reflected_in_entries(parsed):
    result = patch(parsed, {"DEBUG": "true"})
    keys = {e.key: e for e in result.entries if e.key}
    assert keys["DEBUG"].value == "true"


def test_removed_key_absent_from_entries(parsed):
    result = patch(parsed, {"DB_HOST": None})
    keys = [e.key for e in result.entries if e.key]
    assert "DB_HOST" not in keys


def test_removed_key_has_none_new_value(parsed):
    result = patch(parsed, {"DB_HOST": None})
    ops = {op.key: op for op in result.operations}
    assert ops["DB_HOST"].new_value is None


def test_new_key_appended(parsed):
    result = patch(parsed, {"NEW_VAR": "hello"})
    keys = [e.key for e in result.entries if e.key]
    assert "NEW_VAR" in keys


def test_new_key_operation_old_value_is_none(parsed):
    result = patch(parsed, {"NEW_VAR": "hello"})
    ops = {op.key: op for op in result.operations}
    assert ops["NEW_VAR"].old_value is None


def test_to_env_string_contains_updated_value(parsed):
    result = patch(parsed, {"APP_NAME": "newapp"})
    env_str = result.to_env_string()
    assert "APP_NAME=newapp" in env_str


def test_to_env_string_excludes_removed_key(parsed):
    result = patch(parsed, {"SECRET_KEY": None})
    env_str = result.to_env_string()
    assert "SECRET_KEY" not in env_str


def test_as_dict_structure(parsed):
    result = patch(parsed, {"DEBUG": "true"})
    d = result.as_dict()
    assert "source" in d
    assert "operations" in d
    assert "entry_count" in d
    assert isinstance(d["operations"], list)


def test_operation_as_dict(parsed):
    result = patch(parsed, {"DEBUG": "true"})
    op = result.operations[0]
    d = op.as_dict()
    assert set(d.keys()) == {"key", "old_value", "new_value"}
