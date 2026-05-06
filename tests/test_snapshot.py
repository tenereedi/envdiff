"""Tests for envdiff.snapshot."""

import json
import pytest

from envdiff.parser import parse_env_string
from envdiff.snapshot import (
    Snapshot,
    take_snapshot,
    snapshots_equal,
    snapshot_from_dict,
    _compute_checksum,
)

ENV_A = "APP_ENV=production\nDB_HOST=db.example.com\nSECRET_KEY=abc123\n"
ENV_B = "APP_ENV=staging\nDB_HOST=db.example.com\nSECRET_KEY=abc123\n"


@pytest.fixture
def snapshot_a():
    return take_snapshot(parse_env_string(ENV_A), source=".env.production")


@pytest.fixture
def snapshot_b():
    return take_snapshot(parse_env_string(ENV_B), source=".env.staging")


def test_snapshot_has_correct_source(snapshot_a):
    assert snapshot_a.source == ".env.production"


def test_snapshot_entries_match_parsed_keys(snapshot_a):
    assert snapshot_a.entries["APP_ENV"] == "production"
    assert snapshot_a.entries["DB_HOST"] == "db.example.com"


def test_snapshot_has_checksum(snapshot_a):
    assert isinstance(snapshot_a.checksum, str)
    assert len(snapshot_a.checksum) == 64  # SHA-256 hex digest


def test_snapshot_has_captured_at(snapshot_a):
    assert "T" in snapshot_a.captured_at  # ISO 8601 datetime


def test_equal_snapshots(snapshot_a):
    duplicate = take_snapshot(parse_env_string(ENV_A), source="other")
    assert snapshots_equal(snapshot_a, duplicate)


def test_unequal_snapshots(snapshot_a, snapshot_b):
    assert not snapshots_equal(snapshot_a, snapshot_b)


def test_checksum_is_deterministic():
    entries = {"FOO": "bar", "BAZ": "qux"}
    assert _compute_checksum(entries) == _compute_checksum(entries)


def test_checksum_order_independent():
    a = {"FOO": "1", "BAR": "2"}
    b = {"BAR": "2", "FOO": "1"}
    assert _compute_checksum(a) == _compute_checksum(b)


def test_as_dict_keys(snapshot_a):
    d = snapshot_a.as_dict()
    assert set(d.keys()) == {"source", "captured_at", "entries", "checksum"}


def test_to_json_is_valid(snapshot_a):
    raw = snapshot_a.to_json()
    parsed = json.loads(raw)
    assert parsed["source"] == ".env.production"


def test_snapshot_from_dict_roundtrip(snapshot_a):
    restored = snapshot_from_dict(snapshot_a.as_dict())
    assert restored.source == snapshot_a.source
    assert restored.checksum == snapshot_a.checksum
    assert restored.entries == snapshot_a.entries
