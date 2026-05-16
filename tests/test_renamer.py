"""Tests for envdiff.renamer."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.renamer import rename, RenameResult, RenameOperation


ENV_TEXT = """\
DB_HOST=localhost
DB_PORT=5432
APP_SECRET=hunter2
DEBUG=true
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return rename(parsed, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})


def test_rename_returns_rename_result(result):
    assert isinstance(result, RenameResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_renamed_count(result):
    assert result.renamed_count == 2


def test_old_keys_absent(result):
    keys = [e.key for e in result.entries]
    assert "DB_HOST" not in keys
    assert "DB_PORT" not in keys


def test_new_keys_present(result):
    keys = [e.key for e in result.entries]
    assert "DATABASE_HOST" in keys
    assert "DATABASE_PORT" in keys


def test_untouched_keys_preserved(result):
    keys = [e.key for e in result.entries]
    assert "APP_SECRET" in keys
    assert "DEBUG" in keys


def test_entry_count_unchanged(parsed, result):
    assert len(result.entries) == len(parsed.entries)


def test_values_preserved(result):
    entry_map = {e.key: e.value for e in result.entries}
    assert entry_map["DATABASE_HOST"] == "localhost"
    assert entry_map["DATABASE_PORT"] == "5432"


def test_operations_are_rename_operation_instances(result):
    for op in result.operations:
        assert isinstance(op, RenameOperation)


def test_skipped_nonexistent_key(parsed):
    result = rename(parsed, {"NONEXISTENT": "NEW_KEY"})
    assert "NONEXISTENT" in result.skipped
    assert result.renamed_count == 0


def test_skipped_when_new_key_already_exists(parsed):
    # DB_PORT already exists, renaming DB_HOST -> DB_PORT should be skipped
    result = rename(parsed, {"DB_HOST": "DB_PORT"})
    assert "DB_HOST" in result.skipped
    assert result.renamed_count == 0


def test_to_env_string_contains_new_key(result):
    env_str = result.to_env_string()
    assert "DATABASE_HOST=localhost" in env_str
    assert "DB_HOST" not in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "renamed_count" in d
    assert "operations" in d
    assert "skipped" in d
    assert "entries" in d


def test_operation_as_dict(result):
    op_dicts = [op.as_dict() for op in result.operations]
    keys = {d["old_key"] for d in op_dicts}
    assert "DB_HOST" in keys
