"""Compare two environments and produce a structured comparison report."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envdiff.parser import ParseResult
from envdiff.differ import diff_envs, DiffEntry, DiffStatus


@dataclass
class CompareStats:
    total_a: int
    total_b: int
    shared: int
    only_in_a: int
    only_in_b: int
    changed: int
    unchanged: int

    def as_dict(self) -> Dict:
        return {
            "total_a": self.total_a,
            "total_b": self.total_b,
            "shared": self.shared,
            "only_in_a": self.only_in_a,
            "only_in_b": self.only_in_b,
            "changed": self.changed,
            "unchanged": self.unchanged,
        }


@dataclass
class CompareResult:
    source_a: str
    source_b: str
    entries: List[DiffEntry]
    stats: CompareStats

    def has_differences(self) -> bool:
        return any(
            e.status != DiffStatus.UNCHANGED for e in self.entries
        )

    def as_dict(self) -> Dict:
        return {
            "source_a": self.source_a,
            "source_b": self.source_b,
            "has_differences": self.has_differences(),
            "stats": self.stats.as_dict(),
            "entries": [e.as_dict() for e in self.entries],
        }


def compare_envs(parsed_a: ParseResult, parsed_b: ParseResult) -> CompareResult:
    """Compare two parsed env files and return a CompareResult."""
    entries = diff_envs(parsed_a, parsed_b)

    dict_a = parsed_a.as_dict()
    dict_b = parsed_b.as_dict()
    keys_a = set(dict_a.keys())
    keys_b = set(dict_b.keys())

    only_in_a = sum(1 for e in entries if e.status == DiffStatus.REMOVED)
    only_in_b = sum(1 for e in entries if e.status == DiffStatus.ADDED)
    changed = sum(1 for e in entries if e.status == DiffStatus.CHANGED)
    unchanged = sum(1 for e in entries if e.status == DiffStatus.UNCHANGED)
    shared = len(keys_a & keys_b)

    stats = CompareStats(
        total_a=len(keys_a),
        total_b=len(keys_b),
        shared=shared,
        only_in_a=only_in_a,
        only_in_b=only_in_b,
        changed=changed,
        unchanged=unchanged,
    )

    return CompareResult(
        source_a=parsed_a.source,
        source_b=parsed_b.source,
        entries=entries,
        stats=stats,
    )
