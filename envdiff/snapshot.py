"""Snapshot module for capturing and comparing .env state at a point in time."""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envdiff.parser import ParseResult


@dataclass
class Snapshot:
    """Represents a captured state of a parsed .env file."""

    source: str
    captured_at: str
    entries: Dict[str, str]
    checksum: str

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "entries": self.entries,
            "checksum": self.checksum,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent)


def _compute_checksum(entries: Dict[str, str]) -> str:
    """Compute a deterministic SHA-256 checksum over sorted key=value pairs."""
    content = "\n".join(f"{k}={v}" for k, v in sorted(entries.items()))
    return hashlib.sha256(content.encode()).hexdigest()


def take_snapshot(parsed: ParseResult, source: str = "<unknown>") -> Snapshot:
    """Create a Snapshot from a ParseResult."""
    entries = {e.key: e.value for e in parsed.entries}
    checksum = _compute_checksum(entries)
    captured_at = datetime.now(timezone.utc).isoformat()
    return Snapshot(
        source=source,
        captured_at=captured_at,
        entries=entries,
        checksum=checksum,
    )


def snapshots_equal(a: Snapshot, b: Snapshot) -> bool:
    """Return True if two snapshots have identical content (by checksum)."""
    return a.checksum == b.checksum


def snapshot_from_dict(data: dict) -> Snapshot:
    """Deserialise a Snapshot from a plain dictionary (e.g. loaded from JSON)."""
    return Snapshot(
        source=data["source"],
        captured_at=data["captured_at"],
        entries=data["entries"],
        checksum=data["checksum"],
    )
