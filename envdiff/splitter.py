"""Split a parsed env file into multiple files by group or pattern."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import EnvEntry, ParseResult
from envdiff.grouper import group_entries


@dataclass
class SplitBucket:
    name: str
    entries: List[EnvEntry] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "entry_count": len(self.entries),
            "keys": [e.key for e in self.entries if e.key],
        }

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.key is not None:
                if entry.raw is not None:
                    lines.append(entry.raw)
                else:
                    lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines) + ("\n" if lines else "")


@dataclass
class SplitResult:
    source: str
    buckets: List[SplitBucket]
    patterns: List[str]

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "bucket_count": len(self.buckets),
            "patterns": self.patterns,
            "buckets": [b.as_dict() for b in self.buckets],
        }

    def bucket_names(self) -> List[str]:
        return [b.name for b in self.buckets]

    def get_bucket(self, name: str) -> Optional[SplitBucket]:
        for b in self.buckets:
            if b.name == name:
                return b
        return None


def split(
    parsed: ParseResult,
    patterns: Optional[List[str]] = None,
) -> SplitResult:
    """Split entries into named buckets based on key prefix patterns.

    Each pattern is a string like ``db:DB_*`` where the part before the colon
    is the bucket name and the part after is a glob pattern matched against
    entry keys.  Unmatched entries are placed in an ``other`` bucket.
    """
    resolved_patterns: List[str] = patterns or []

    import fnmatch

    named: Dict[str, List[EnvEntry]] = {}
    order: List[str] = []

    for pattern_spec in resolved_patterns:
        if ":" in pattern_spec:
            bucket_name, glob = pattern_spec.split(":", 1)
        else:
            bucket_name, glob = pattern_spec, f"{pattern_spec}_*"
        if bucket_name not in named:
            named[bucket_name] = []
            order.append(bucket_name)
        named[bucket_name]  # ensure key exists

    assigned: set = set()

    for entry in parsed.entries:
        if entry.key is None:
            continue
        placed = False
        for pattern_spec in resolved_patterns:
            if ":" in pattern_spec:
                bucket_name, glob = pattern_spec.split(":", 1)
            else:
                bucket_name, glob = pattern_spec, f"{pattern_spec}_*"
            if fnmatch.fnmatch(entry.key, glob):
                named[bucket_name].append(entry)
                assigned.add(entry.key)
                placed = True
                break
        if not placed:
            if "other" not in named:
                named["other"] = []
                order.append("other")
            named["other"].append(entry)
            assigned.add(entry.key)

    if "other" not in named:
        order.append("other")
        named["other"] = []

    buckets = [SplitBucket(name=n, entries=named[n]) for n in order]
    return SplitResult(
        source=parsed.source,
        buckets=buckets,
        patterns=resolved_patterns,
    )
