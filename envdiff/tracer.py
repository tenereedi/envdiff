"""Tracer module: track which keys changed between two parsed envs over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envdiff.parser import ParseResult


@dataclass
class TraceEvent:
    key: str
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: str
    source_a: str
    source_b: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp,
            "source_a": self.source_a,
            "source_b": self.source_b,
        }


@dataclass
class TraceResult:
    source_a: str
    source_b: str
    timestamp: str
    events: List[TraceEvent] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.events) > 0

    @property
    def changed_keys(self) -> List[str]:
        return [e.key for e in self.events]

    def as_dict(self) -> dict:
        return {
            "source_a": self.source_a,
            "source_b": self.source_b,
            "timestamp": self.timestamp,
            "has_changes": self.has_changes,
            "event_count": len(self.events),
            "events": [e.as_dict() for e in self.events],
        }


def trace(parsed_a: ParseResult, parsed_b: ParseResult) -> TraceResult:
    """Produce a TraceResult capturing every key-level change between two envs."""
    now = datetime.now(timezone.utc).isoformat()
    result = TraceResult(
        source_a=parsed_a.source,
        source_b=parsed_b.source,
        timestamp=now,
    )

    dict_a: Dict[str, str] = parsed_a.as_dict()
    dict_b: Dict[str, str] = parsed_b.as_dict()
    all_keys = sorted(set(dict_a) | set(dict_b))

    for key in all_keys:
        val_a = dict_a.get(key)
        val_b = dict_b.get(key)
        if val_a != val_b:
            result.events.append(
                TraceEvent(
                    key=key,
                    old_value=val_a,
                    new_value=val_b,
                    timestamp=now,
                    source_a=parsed_a.source,
                    source_b=parsed_b.source,
                )
            )

    return result
