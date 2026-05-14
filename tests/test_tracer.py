"""Tests for envdiff.tracer."""
from __future__ import annotations

import pytest

from envdiff.parser import parse_env_string
from envdiff.tracer import TraceEvent, TraceResult, trace


@pytest.fixture()
def parsed_a():
    return parse_env_string(
        "APP_ENV=production\nDB_HOST=localhost\nSECRET_KEY=abc123\n",
        source="a.env",
    )


@pytest.fixture()
def parsed_b():
    return parse_env_string(
        "APP_ENV=staging\nDB_HOST=localhost\nNEW_KEY=hello\n",
        source="b.env",
    )


@pytest.fixture()
def result(parsed_a, parsed_b):
    return trace(parsed_a, parsed_b)


def test_returns_trace_result(result):
    assert isinstance(result, TraceResult)


def test_sources_preserved(result):
    assert result.source_a == "a.env"
    assert result.source_b == "b.env"


def test_has_changes_when_different(result):
    assert result.has_changes is True


def test_changed_keys_contains_modified(result):
    assert "APP_ENV" in result.changed_keys


def test_removed_key_in_events(result):
    assert "SECRET_KEY" in result.changed_keys


def test_added_key_in_events(result):
    assert "NEW_KEY" in result.changed_keys


def test_unchanged_key_not_in_events(result):
    assert "DB_HOST" not in result.changed_keys


def test_event_count(result):
    assert len(result.events) == 3


def test_removed_key_new_value_is_none(result):
    ev = next(e for e in result.events if e.key == "SECRET_KEY")
    assert ev.new_value is None
    assert ev.old_value == "abc123"


def test_added_key_old_value_is_none(result):
    ev = next(e for e in result.events if e.key == "NEW_KEY")
    assert ev.old_value is None
    assert ev.new_value == "hello"


def test_no_changes_identical_envs(parsed_a):
    r = trace(parsed_a, parsed_a)
    assert r.has_changes is False
    assert r.events == []


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source_a" in d
    assert "source_b" in d
    assert "has_changes" in d
    assert "event_count" in d
    assert isinstance(d["events"], list)


def test_event_as_dict(result):
    ev = result.events[0]
    d = ev.as_dict()
    assert "key" in d
    assert "old_value" in d
    assert "new_value" in d
    assert "timestamp" in d
