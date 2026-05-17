"""Tests for envdiff.promoter."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.promoter import PromoteStatus, promote


@pytest.fixture
def parsed_a():
    return parse_env_string("APP_ENV=production\nDB_HOST=prod-db\nSECRET_KEY=abc123", source="prod.env")


@pytest.fixture
def parsed_b():
    return parse_env_string("APP_ENV=staging\nDB_HOST=staging-db\nDEBUG=true", source="staging.env")


@pytest.fixture
def result(parsed_a, parsed_b):
    return promote(parsed_a, parsed_b)


def test_promote_returns_promote_result(result):
    from envdiff.promoter import PromoteResult
    assert isinstance(result, PromoteResult)


def test_source_preserved(result):
    assert result.source == "prod.env"


def test_target_preserved(result):
    assert result.target == "staging.env"


def test_new_key_is_added(parsed_a, parsed_b):
    res = promote(parsed_a, parsed_b)
    secret_entry = next(e for e in res.entries if e.key == "SECRET_KEY")
    assert secret_entry.status == PromoteStatus.ADDED


def test_existing_differing_key_is_skipped_by_default(result):
    app_env = next(e for e in result.entries if e.key == "APP_ENV")
    assert app_env.status == PromoteStatus.SKIPPED


def test_overwrite_updates_existing_key(parsed_a, parsed_b):
    res = promote(parsed_a, parsed_b, overwrite=True)
    app_env = next(e for e in res.entries if e.key == "APP_ENV")
    assert app_env.status == PromoteStatus.UPDATED


def test_conflict_marker_flags_differing_keys(parsed_a, parsed_b):
    res = promote(parsed_a, parsed_b, conflict_marker=True)
    app_env = next(e for e in res.entries if e.key == "APP_ENV")
    assert app_env.status == PromoteStatus.CONFLICT


def test_specific_keys_only(parsed_a, parsed_b):
    res = promote(parsed_a, parsed_b, keys=["SECRET_KEY"])
    assert len(res.entries) == 1
    assert res.entries[0].key == "SECRET_KEY"


def test_promoted_count(parsed_a, parsed_b):
    res = promote(parsed_a, parsed_b, overwrite=True)
    # APP_ENV updated, DB_HOST updated, SECRET_KEY added
    assert res.promoted_count == 3


def test_conflict_count(parsed_a, parsed_b):
    res = promote(parsed_a, parsed_b, conflict_marker=True)
    assert res.conflict_count == 2  # APP_ENV and DB_HOST differ


def test_skipped_count_default(result):
    # APP_ENV and DB_HOST differ but not overwriting
    assert result.skipped_count == 2


def test_as_dict_has_required_keys(result):
    d = result.as_dict()
    assert "source" in d
    assert "target" in d
    assert "promoted_count" in d
    assert "conflict_count" in d
    assert "skipped_count" in d
    assert "entries" in d


def test_to_env_string_contains_keys(result):
    env_str = result.to_env_string()
    assert "SECRET_KEY" in env_str
