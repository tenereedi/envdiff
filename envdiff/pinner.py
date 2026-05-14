"""Pin current env values to a lockfile for drift detection."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envdiff.parser import ParseResult
from envdiff.differ import is_secret


@dataclass
class PinnedEntry:
    key: str
    value: str
    is_secret: bool
    pinned_at: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": "***" if self.is_secret else self.value,
            "is_secret": self.is_secret,
            "pinned_at": self.pinned_at,
        }


@dataclass
class PinResult:
    source: str
    pinned_at: str
    entries: List[PinnedEntry] = field(default_factory=list)
    _drift: List[str] = field(default_factory=list, repr=False)

    @property
    def has_drift(self) -> bool:
        return bool(self._drift)

    @property
    def drift_keys(self) -> List[str]:
        return list(self._drift)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "pinned_at": self.pinned_at,
            "has_drift": self.has_drift,
            "drift_keys": self.drift_keys,
            "entries": [e.as_dict() for e in self.entries],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent)


def pin(parsed: ParseResult) -> PinResult:
    """Pin all entries from a parsed env to a PinResult lockfile snapshot."""
    now = datetime.now(timezone.utc).isoformat()
    entries = [
        PinnedEntry(
            key=e.key,
            value=e.value,
            is_secret=is_secret(e.key),
            pinned_at=now,
        )
        for e in parsed.entries
        if e.key
    ]
    return PinResult(source=parsed.source, pinned_at=now, entries=entries)


def check_drift(current: ParseResult, pin_result: PinResult) -> PinResult:
    """Compare current parsed env against a pinned result and record drift."""
    pinned_map: Dict[str, str] = {e.key: e.value for e in pin_result.entries}
    current_map: Dict[str, str] = {
        e.key: e.value for e in current.entries if e.key
    }
    drift: List[str] = []
    for key, pinned_val in pinned_map.items():
        current_val = current_map.get(key)
        if current_val is None or current_val != pinned_val:
            drift.append(key)
    for key in current_map:
        if key not in pinned_map:
            drift.append(key)
    pin_result._drift = sorted(set(drift))
    return pin_result
