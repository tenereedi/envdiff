"""Tests for envdiff.merger module."""

import pytest
from envdiff.parser import parse_env_string
from envdiff.merger import merge, MergeStrategy, MergeResult


ENV_A = """
DB_HOST=localhost
DB_PORT=5432
API_KEY=secret_a
ONLY_IN_A=yes
""".strip()

ENV_B = """
DB_HOST=prod.example.com
DB_PORT=5432
API_KEY=secret_b
ONLY_IN_B=yes
""".strip()


@pytest.fixture
def parsed_a():
    return parse_env_string(ENV_A)


@pytest.fixture
def parsed_b():
    return parse_env_string(ENV_B)


def test_merge_returns_merge_result(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b)
    assert isinstance(result, MergeResult)


def test_prefer_b_resolves_conflict_with_b(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b, strategy=MergeStrategy.PREFER_B)
    keys = {e.key: e.value for e in result.entries if e.key}
    assert keys["DB_HOST"] == "prod.example.com"
    assert keys["API_KEY"] == "secret_b"


def test_prefer_a_resolves_conflict_with_a(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b, strategy=MergeStrategy.PREFER_A)
    keys = {e.key: e.value for e in result.entries if e.key}
    assert keys["DB_HOST"] == "localhost"
    assert keys["API_KEY"] == "secret_a"


def test_union_includes_all_keys(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b, strategy=MergeStrategy.UNION)
    keys = {e.key for e in result.entries if e.key}
    assert "ONLY_IN_A" in keys
    assert "ONLY_IN_B" in keys


def test_intersection_only_shared_keys(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b, strategy=MergeStrategy.INTERSECTION)
    keys = {e.key for e in result.entries if e.key}
    assert "ONLY_IN_A" not in keys
    assert "ONLY_IN_B" not in keys
    assert "DB_HOST" in keys


def test_conflicts_recorded(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b)
    conflict_keys = {c.key for c in result.conflicts}
    assert "DB_HOST" in conflict_keys
    assert "API_KEY" in conflict_keys
    # DB_PORT has same value — not a conflict
    assert "DB_PORT" not in conflict_keys


def test_conflict_as_dict(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b)
    conflict = next(c for c in result.conflicts if c.key == "DB_HOST")
    d = conflict.as_dict()
    assert d["key"] == "DB_HOST"
    assert d["value_a"] == "localhost"
    assert d["value_b"] == "prod.example.com"


def test_to_env_string(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b, strategy=MergeStrategy.UNION)
    env_str = result.to_env_string()
    assert "DB_HOST=" in env_str
    assert "ONLY_IN_A=" in env_str
    assert "ONLY_IN_B=" in env_str


def test_as_dict_structure(parsed_a, parsed_b):
    result = merge(parsed_a, parsed_b)
    d = result.as_dict()
    assert "strategy" in d
    assert "entry_count" in d
    assert "conflict_count" in d
    assert isinstance(d["conflicts"], list)
