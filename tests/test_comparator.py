"""Tests for envdiff.comparator."""

import pytest
from envdiff.parser import parse_env_string
from envdiff.comparator import compare_envs, CompareResult, CompareStats
from envdiff.differ import DiffStatus


ENV_A = """
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=abc123
DEBUG=true
"""

ENV_B = """
DB_HOST=prodserver
DB_PORT=5432
SECRET_KEY=xyz999
NEW_FEATURE=enabled
"""


@pytest.fixture
def parsed_a():
    return parse_env_string(ENV_A, source=".env.dev")


@pytest.fixture
def parsed_b():
    return parse_env_string(ENV_B, source=".env.prod")


@pytest.fixture
def result(parsed_a, parsed_b):
    return compare_envs(parsed_a, parsed_b)


def test_returns_compare_result(result):
    assert isinstance(result, CompareResult)


def test_sources_preserved(result):
    assert result.source_a == ".env.dev"
    assert result.source_b == ".env.prod"


def test_has_differences(result):
    assert result.has_differences() is True


def test_stats_type(result):
    assert isinstance(result.stats, CompareStats)


def test_stats_totals(result):
    assert result.stats.total_a == 4
    assert result.stats.total_b == 4


def test_stats_only_in_a(result):
    assert result.stats.only_in_a == 1  # DEBUG


def test_stats_only_in_b(result):
    assert result.stats.only_in_b == 1  # NEW_FEATURE


def test_stats_changed(result):
    assert result.stats.changed == 2  # DB_HOST, SECRET_KEY


def test_stats_unchanged(result):
    assert result.stats.unchanged == 1  # DB_PORT


def test_as_dict_keys(result):
    d = result.as_dict()
    assert "source_a" in d
    assert "source_b" in d
    assert "has_differences" in d
    assert "stats" in d
    assert "entries" in d


def test_identical_envs_no_differences():
    env = "KEY=value\nFOO=bar\n"
    pa = parse_env_string(env, source="a")
    pb = parse_env_string(env, source="b")
    r = compare_envs(pa, pb)
    assert r.has_differences() is False
    assert r.stats.changed == 0
    assert r.stats.only_in_a == 0
    assert r.stats.only_in_b == 0
