"""Audit trail for env diff operations — records what changed, when, and why."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from envdiff.differ import DiffEntry, DiffStatus


@dataclass
class AuditEvent:
    timestamp: str
    operation: str
    source_a: str
    source_b: str
    total_keys: int
    added: int
    removed: int
    changed: int
    unchanged: int
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "source_a": self.source_a,
            "source_b": self.source_b,
            "summary": {
                "total_keys": self.total_keys,
                "added": self.added,
                "removed": self.removed,
                "changed": self.changed,
                "unchanged": self.unchanged,
            },
            "note": self.note,
        }


@dataclass
class AuditLog:
    events: List[AuditEvent] = field(default_factory=list)

    def add(self, event: AuditEvent) -> None:
        self.events.append(event)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps([e.as_dict() for e in self.events], indent=indent)

    def __len__(self) -> int:
        return len(self.events)


def build_audit_event(
    diffs: List[DiffEntry],
    source_a: str,
    source_b: str,
    operation: str = "diff",
    note: Optional[str] = None,
) -> AuditEvent:
    """Create an AuditEvent from a list of DiffEntry objects."""
    counts = {s: 0 for s in DiffStatus}
    for entry in diffs:
        counts[entry.status] += 1

    return AuditEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        operation=operation,
        source_a=source_a,
        source_b=source_b,
        total_keys=len(diffs),
        added=counts[DiffStatus.ADDED],
        removed=counts[DiffStatus.REMOVED],
        changed=counts[DiffStatus.CHANGED],
        unchanged=counts[DiffStatus.UNCHANGED],
        note=note,
    )
