"""Freeze an env file into an immutable snapshot with integrity verification."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .parser import ParseResult


@dataclass
class FrozenEntry:
    key: str
    value: str
    checksum: str

    def as_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "checksum": self.checksum}


@dataclass
class FreezeResult:
    source: str
    frozen_at: str
    entries: List[FrozenEntry]
    manifest_checksum: str
    tampered_keys: List[str] = field(default_factory=list)

    @property
    def is_intact(self) -> bool:
        return len(self.tampered_keys) == 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "frozen_at": self.frozen_at,
            "manifest_checksum": self.manifest_checksum,
            "is_intact": self.is_intact,
            "tampered_keys": self.tampered_keys,
            "entries": [e.as_dict() for e in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)


def _entry_checksum(key: str, value: str) -> str:
    payload = f"{key}={value}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def _manifest_checksum(entries: List[FrozenEntry]) -> str:
    combined = "|".join(f"{e.key}:{e.checksum}" for e in entries)
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def freeze(parsed: ParseResult) -> FreezeResult:
    """Freeze a parsed env into a FreezeResult with per-entry checksums."""
    entries = [
        FrozenEntry(
            key=entry.key,
            value=entry.value,
            checksum=_entry_checksum(entry.key, entry.value),
        )
        for entry in parsed.entries
        if entry.key is not None
    ]
    manifest = _manifest_checksum(entries)
    return FreezeResult(
        source=parsed.source,
        frozen_at=datetime.now(timezone.utc).isoformat(),
        entries=entries,
        manifest_checksum=manifest,
    )


def verify(parsed: ParseResult, frozen: FreezeResult) -> FreezeResult:
    """Verify a live ParseResult against a previously frozen FreezeResult."""
    live: Dict[str, str] = {
        e.key: e.value for e in parsed.entries if e.key is not None
    }
    tampered: List[str] = []
    for fe in frozen.entries:
        live_val = live.get(fe.key)
        if live_val is None or _entry_checksum(fe.key, live_val) != fe.checksum:
            tampered.append(fe.key)
    return FreezeResult(
        source=frozen.source,
        frozen_at=frozen.frozen_at,
        entries=frozen.entries,
        manifest_checksum=frozen.manifest_checksum,
        tampered_keys=tampered,
    )
