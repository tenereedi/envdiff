"""Formatter module for rendering diff results as text or JSON output."""

from __future__ import annotations

import json
from enum import Enum
from typing import List

from envdiff.differ import DiffEntry, DiffStatus


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


_STATUS_SYMBOL = {
    DiffStatus.ADDED: "+",
    DiffStatus.REMOVED: "-",
    DiffStatus.CHANGED: "~",
    DiffStatus.UNCHANGED: " ",
}

_STATUS_COLOR = {
    DiffStatus.ADDED: "\033[32m",
    DiffStatus.REMOVED: "\033[31m",
    DiffStatus.CHANGED: "\033[33m",
    DiffStatus.UNCHANGED: "",
}

_RESET = "\033[0m"


def format_text(entries: List[DiffEntry], color: bool = False) -> str:
    """Render diff entries as a human-readable text block."""
    lines: List[str] = []
    for entry in entries:
        symbol = _STATUS_SYMBOL[entry.status]
        key = entry.key
        if entry.status == DiffStatus.UNCHANGED:
            line = f"  {key}={entry.masked_value_a or entry.value_a or ''}"
        elif entry.status == DiffStatus.ADDED:
            line = f"+ {key}={entry.masked_value_b or entry.value_b or ''}"
        elif entry.status == DiffStatus.REMOVED:
            line = f"- {key}={entry.masked_value_a or entry.value_a or ''}"
        else:  # CHANGED
            val_a = entry.masked_value_a or entry.value_a or ""
            val_b = entry.masked_value_b or entry.value_b or ""
            line = f"~ {key}: {val_a} -> {val_b}"

        if color and _STATUS_COLOR[entry.status]:
            line = f"{_STATUS_COLOR[entry.status]}{line}{_RESET}"
        lines.append(line)
    return "\n".join(lines)


def format_json(entries: List[DiffEntry]) -> str:
    """Render diff entries as a JSON string."""
    records = []
    for entry in entries:
        records.append(
            {
                "key": entry.key,
                "status": entry.status.value,
                "value_a": entry.masked_value_a or entry.value_a,
                "value_b": entry.masked_value_b or entry.value_b,
            }
        )
    return json.dumps(records, indent=2)


def format_diff(
    entries: List[DiffEntry],
    fmt: OutputFormat = OutputFormat.TEXT,
    color: bool = False,
) -> str:
    """Dispatch to the appropriate formatter."""
    if fmt == OutputFormat.JSON:
        return format_json(entries)
    return format_text(entries, color=color)
