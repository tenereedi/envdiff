"""Pruner: remove keys from a parsed env that match given criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from envdiff.parser import EnvEntry, ParseResult


@dataclass
class PruneOperation:
    key: str
    reason: str  # 'pattern', 'prefix', 'exact'

    def as_dict(self) -> dict:
        return {"key": self.key, "reason": self.reason}


@dataclass
class PruneResult:
    source: str
    entries: List[EnvEntry]
    pruned: List[PruneOperation] = field(default_factory=list)

    @property
    def pruned_count(self) -> int:
        return len(self.pruned)

    @property
    def remaining_count(self) -> int:
        return len(self.entries)

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.key is not None:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "pruned_count": self.pruned_count,
            "remaining_count": self.remaining_count,
            "pruned": [op.as_dict() for op in self.pruned],
            "entries": [
                {"key": e.key, "value": e.value}
                for e in self.entries
                if e.key is not None
            ],
        }


def prune(
    parsed: ParseResult,
    keys: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    prefixes: Optional[List[str]] = None,
) -> PruneResult:
    """Remove entries whose keys match any of the given exact keys, glob patterns,
    or prefixes. Entries without a key (comments/blanks) are always kept."""
    keys = keys or []
    patterns = patterns or []
    prefixes = prefixes or []

    kept: List[EnvEntry] = []
    pruned: List[PruneOperation] = []

    for entry in parsed.entries:
        if entry.key is None:
            kept.append(entry)
            continue

        reason: Optional[str] = None

        if entry.key in keys:
            reason = "exact"
        elif any(fnmatch(entry.key, pat) for pat in patterns):
            reason = "pattern"
        elif any(entry.key.startswith(pfx) for pfx in prefixes):
            reason = "prefix"

        if reason:
            pruned.append(PruneOperation(key=entry.key, reason=reason))
        else:
            kept.append(entry)

    return PruneResult(source=parsed.source, entries=kept, pruned=pruned)
