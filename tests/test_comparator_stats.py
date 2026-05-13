"""Edge-case and stats-focused tests for envdiff.comparator."""

import pytest
from envdiff.parser import parse_env_string
from envdiff.comparator import compare_envs


def test_empty_vs_populated():
    pa = parse_env_string("", source="empty")
    pb = parse_env_string("KEY=val\nFOO=bar\n", source="populated")
    r = compare_envs(pa, pb)
    assert r.stats.total_a == 0
    assert r.stats.total_b == 2
    assert r.stats.only_in_b == 2
    assert r.stats.only_in_a == 0
    assert r.stats.changed == 0
    assert r.stats.unchanged == 0
    assert r.has_differences() is True


def test_populated_vs_empty():
    pa = parse_env_string("KEY=val\n", source="a")
    pb = parse_env_string("", source="b")
    r = compare_envs(pa, pb)
    assert r.stats.only_in_a == 1
    assert r.stats.only_in_b == 0


def test_shared_count_correct():
    pa = parse_env_string("A=1\nB=2\nC=3\n", source="a")
    pb = parse_env_string("B=2\nC=99\nD=4\n", source="b")
    r = compare_envs(pa, pb)
    assert r.stats.shared == 2  # B and C
    assert r.stats.unchanged == 1  # B
    assert r.stats.changed == 1  # C


def test_as_dict_stats_structure():
    pa = parse_env_string("X=1\n", source="a")
    pb = parse_env_string("X=1\n", source="b")
    r = compare_envs(pa, pb)
    d = r.as_dict()
    stats = d["stats"]
    for key in ("total_a", "total_b", "shared", "only_in_a", "only_in_b", "changed", "unchanged"):
        assert key in stats


def test_entries_count_matches_all_keys():
    pa = parse_env_string("A=1\nB=2\n", source="a")
    pb = parse_env_string("B=2\nC=3\n", source="b")
    r = compare_envs(pa, pb)
    # A (removed) + B (unchanged) + C (added) = 3
    assert len(r.entries) == 3
