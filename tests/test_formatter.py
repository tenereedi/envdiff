"""Tests for envdiff.formatter."""

from __future__ import annotations

import json

import pytest

from envdiff.differ import DiffEntry, DiffStatus
from envdiff.formatter import OutputFormat, format_diff, format_json, format_text


@pytest.fixture()
def sample_entries() -> list[DiffEntry]:
    return [
        DiffEntry(
            key="APP_NAME",
            status=DiffStatus.UNCHANGED,
            value_a="myapp",
            value_b="myapp",
        ),
        DiffEntry(
            key="SECRET_KEY",
            status=DiffStatus.CHANGED,
            value_a="old_secret",
            value_b="new_secret",
            masked_value_a="***",
            masked_value_b="***",
        ),
        DiffEntry(
            key="NEW_VAR",
            status=DiffStatus.ADDED,
            value_a=None,
            value_b="hello",
        ),
        DiffEntry(
            key="OLD_VAR",
            status=DiffStatus.REMOVED,
            value_a="bye",
            value_b=None,
        ),
    ]


def test_text_unchanged(sample_entries):
    output = format_text(sample_entries)
    assert "  APP_NAME=myapp" in output


def test_text_added(sample_entries):
    output = format_text(sample_entries)
    assert "+ NEW_VAR=hello" in output


def test_text_removed(sample_entries):
    output = format_text(sample_entries)
    assert "- OLD_VAR=bye" in output


def test_text_changed_masked(sample_entries):
    output = format_text(sample_entries)
    assert "~ SECRET_KEY: *** -> ***" in output
    assert "old_secret" not in output
    assert "new_secret" not in output


def test_json_output_structure(sample_entries):
    raw = format_json(sample_entries)
    data = json.loads(raw)
    assert isinstance(data, list)
    assert len(data) == 4
    keys = {r["key"] for r in data}
    assert keys == {"APP_NAME", "SECRET_KEY", "NEW_VAR", "OLD_VAR"}


def test_json_status_values(sample_entries):
    data = json.loads(format_json(sample_entries))
    statuses = {r["key"]: r["status"] for r in data}
    assert statuses["APP_NAME"] == "unchanged"
    assert statuses["NEW_VAR"] == "added"
    assert statuses["OLD_VAR"] == "removed"
    assert statuses["SECRET_KEY"] == "changed"


def test_json_masked_values_not_exposed(sample_entries):
    """Ensure raw secret values are not present in JSON output for masked entries."""
    data = json.loads(format_json(sample_entries))
    secret_entry = next(r for r in data if r["key"] == "SECRET_KEY")
    raw_output = format_json(sample_entries)
    assert "old_secret" not in raw_output
    assert "new_secret" not in raw_output
    # Masked placeholders should appear instead
    assert secret_entry.get("value_a") == "***"
    assert secret_entry.get("value_b") == "***"


def test_format_diff_dispatches_json(sample_entries):
    result = format_diff(sample_entries, fmt=OutputFormat.JSON)
    assert result.startswith("[")


def test_format_diff_dispatches_text(sample_entries):
    result = format_diff(sample_entries, fmt=OutputFormat.TEXT)
    assert "APP_NAME" in result
    assert not result.startswith("[")


def test_color_output_contains_escape(sample_entries):
    result = format_text(sample_entries, color=True)
    assert "\033[" in result
