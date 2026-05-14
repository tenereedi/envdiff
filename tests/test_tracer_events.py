"""Additional edge-case tests for TraceEvent details."""
from __future__ import annotations

import pytest

from envdiff.parser import parse_env_string
from envdiff.tracer import trace


def _parse(text: str, source: str = "test.env"):
    return parse_env_string(text, source=source)


def test_timestamp_is_iso_format():
    a = _parse("K=1\n")
    b = _parse("K=2\n")
    r = trace(a, b)
    assert "T" in r.timestamp  # ISO 8601 contains 'T'


def test_event_sources_match_parsed_sources():
    a = _parse("K=1\n", source="env_a")
    b = _parse("K=2\n", source="env_b")
    r = trace(a, b)
    ev = r.events[0]
    assert ev.source_a == "env_a"
    assert ev.source_b == "env_b"


def test_empty_a_all_keys_added():
    a = _parse("")
    b = _parse("X=1\nY=2\n")
    r = trace(a, b)
    assert set(r.changed_keys) == {"X", "Y"}
    for ev in r.events:
        assert ev.old_value is None


def test_empty_b_all_keys_removed():
    a = _parse("X=1\nY=2\n")
    b = _parse("")
    r = trace(a, b)
    assert set(r.changed_keys) == {"X", "Y"}
    for ev in r.events:
        assert ev.new_value is None


def test_event_count_matches_as_dict():
    a = _parse("A=1\nB=2\n")
    b = _parse("A=9\nB=2\nC=3\n")
    r = trace(a, b)
    assert r.as_dict()["event_count"] == len(r.events)


def test_changed_keys_sorted_alphabetically():
    a = _parse("Z=1\nA=1\nM=1\n")
    b = _parse("Z=2\nA=2\nM=2\n")
    r = trace(a, b)
    assert r.changed_keys == sorted(r.changed_keys)
