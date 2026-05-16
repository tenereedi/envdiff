"""Inspector: analyze a single .env file and surface key metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from envdiff.parser import ParseResult
from envdiff.differ import is_secret


@dataclass
class InspectEntry:
    key: str
    value: str
    line_number: int
    is_secret: bool
    is_empty: bool
    category: str  # 'secret' | 'empty' | 'normal'

    def as_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "line_number": self.line_number,
            "is_secret": self.is_secret,
            "is_empty": self.is_empty,
            "category": self.category,
        }


@dataclass
class InspectStats:
    total: int
    secrets: int
    empty: int
    normal: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "secrets": self.secrets,
            "empty": self.empty,
            "normal": self.normal,
        }


@dataclass
class InspectResult:
    source: str
    entries: List[InspectEntry] = field(default_factory=list)
    stats: InspectStats = field(default_factory=lambda: InspectStats(0, 0, 0, 0))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "stats": self.stats.as_dict(),
            "entries": [e.as_dict() for e in self.entries],
        }


def _categorize(key: str, value: str) -> str:
    if not value:
        return "empty"
    if is_secret(key):
        return "secret"
    return "normal"


def inspect(parsed: ParseResult) -> InspectResult:
    """Inspect a parsed .env file and return an InspectResult."""
    entries: List[InspectEntry] = []

    for env_entry in parsed.entries:
        key = env_entry.key
        val = env_entry.value
        secret = is_secret(key)
        empty = val == ""
        category = _categorize(key, val)
        entries.append(
            InspectEntry(
                key=key,
                value=val,
                line_number=env_entry.line_number,
                is_secret=secret,
                is_empty=empty,
                category=category,
            )
        )

    total = len(entries)
    secrets = sum(1 for e in entries if e.is_secret)
    empty = sum(1 for e in entries if e.is_empty)
    normal = total - secrets - empty

    stats = InspectStats(total=total, secrets=secrets, empty=empty, normal=normal)
    return InspectResult(source=parsed.source, entries=entries, stats=stats)
