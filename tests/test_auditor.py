"""Tests for envdiff.auditor."""

import json
from unittest.mock import patch

import pytest

from envdiff.auditor import AuditEvent, AuditLog, build_audit_event
from envdiff.differ import DiffEntry, DiffStatus


SAMPLE_DIFFS = [
    DiffEntry(key="A", status=DiffStatus.UNCHANGED, value_a="1", value_b="1"),
    DiffEntry(key="B", status=DiffStatus.CHANGED, value_a="old", value_b="new"),
    DiffEntry(key="C", status=DiffStatus.ADDED, value_a=None, value_b="x"),
    DiffEntry(key="D", status=DiffStatus.REMOVED, value_a="y", value_b=None),
]


@pytest.fixture
def event() -> AuditEvent:
    return build_audit_event(SAMPLE_DIFFS, source_a=".env.dev", source_b=".env.prod")


def test_event_counts(event):
    assert event.added == 1
    assert event.removed == 1
    assert event.changed == 1
    assert event.unchanged == 1
    assert event.total_keys == 4


def test_event_sources(event):
    assert event.source_a == ".env.dev"
    assert event.source_b == ".env.prod"


def test_event_operation_default(event):
    assert event.operation == "diff"


def test_event_custom_operation():
    ev = build_audit_event(SAMPLE_DIFFS, "a", "b", operation="reconcile", note="auto")
    assert ev.operation == "reconcile"
    assert ev.note == "auto"


def test_event_as_dict_keys(event):
    d = event.as_dict()
    assert set(d.keys()) == {"timestamp", "operation", "source_a", "source_b", "summary", "note"}
    assert set(d["summary"].keys()) == {"total_keys", "added", "removed", "changed", "unchanged"}


def test_event_timestamp_is_iso(event):
    # Should not raise
    from datetime import datetime
    datetime.fromisoformat(event.timestamp)


def test_audit_log_add_and_len(event):
    log = AuditLog()
    assert len(log) == 0
    log.add(event)
    assert len(log) == 1


def test_audit_log_to_json(event):
    log = AuditLog()
    log.add(event)
    data = json.loads(log.to_json())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["operation"] == "diff"


def test_audit_log_multiple_events():
    log = AuditLog()
    for _ in range(3):
        log.add(build_audit_event(SAMPLE_DIFFS, "a", "b"))
    assert len(log) == 3
    data = json.loads(log.to_json())
    assert len(data) == 3
