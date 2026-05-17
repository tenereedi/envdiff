"""Tests for envdiff.migrator."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.migrator import migrate, MigrateResult, MigrateOperation


ENV_TEXT = """APP_HOST=localhost
APP_PORT=8080
DB_URL=postgres://localhost/mydb
SECRET_KEY=abc123
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return migrate(parsed, mapping={"APP_HOST": "HOST", "APP_PORT": "PORT"})


def test_migrate_returns_migrate_result(result):
    assert isinstance(result, MigrateResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_migrated_count(result):
    assert result.migrated_count == 2


def test_skipped_count_zero(result):
    assert result.skipped_count == 0


def test_old_keys_replaced(result):
    keys = [e.key for e in result.entries if e.key is not None]
    assert "APP_HOST" not in keys
    assert "APP_PORT" not in keys


def test_new_keys_present(result):
    keys = [e.key for e in result.entries if e.key is not None]
    assert "HOST" in keys
    assert "PORT" in keys


def test_unmapped_keys_unchanged(result):
    keys = [e.key for e in result.entries if e.key is not None]
    assert "DB_URL" in keys
    assert "SECRET_KEY" in keys


def test_value_transform_applied(parsed):
    result = migrate(
        parsed,
        mapping={"APP_PORT": "PORT"},
        value_transforms={"PORT": "9090"},
    )
    port_entry = next(e for e in result.entries if e.key == "PORT")
    assert port_entry.value == "9090"
    assert result.operations[0].transformed is True


def test_no_transform_flag_when_no_transform(result):
    for op in result.operations:
        assert op.transformed is False


def test_collision_causes_skip(parsed):
    # APP_HOST -> DB_URL would collide with existing DB_URL
    result = migrate(parsed, mapping={"APP_HOST": "DB_URL"})
    assert "APP_HOST" in result.skipped_keys
    assert result.migrated_count == 0


def test_to_env_string_contains_new_keys(result):
    env_str = result.to_env_string()
    assert "HOST=localhost" in env_str
    assert "PORT=8080" in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "migrated_count" in d
    assert "skipped_count" in d
    assert "operations" in d
    assert isinstance(d["operations"], list)


def test_operation_as_dict(result):
    op = result.operations[0]
    d = op.as_dict()
    assert "old_key" in d
    assert "new_key" in d
    assert "old_value" in d
    assert "new_value" in d
    assert "transformed" in d
