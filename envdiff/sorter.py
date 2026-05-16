"""Sort .env entries by key, value, or line order with optional grouping."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envdiff.parser import EnvEntry, ParseResult


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortBy(str, Enum):
    KEY = "key"
    VALUE = "value"
    LINE = "line"


@dataclass
class SortResult:
    source: str
    entries: List[EnvEntry]
    sort_by: SortBy
    order: SortOrder

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.key is None:
                lines.append(entry.raw)
            else:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "sort_by": self.sort_by.value,
            "order": self.order.value,
            "entry_count": len(self.entries),
            "keys": [
                e.key for e in self.entries if e.key is not None
            ],
        }


def sort(
    parsed: ParseResult,
    sort_by: SortBy = SortBy.KEY,
    order: SortOrder = SortOrder.ASC,
    comments_first: bool = False,
) -> SortResult:
    """Return a SortResult with entries sorted by the given criterion."""
    kv_entries = [e for e in parsed.entries if e.key is not None]
    non_kv = [e for e in parsed.entries if e.key is None]

    reverse = order == SortOrder.DESC

    if sort_by == SortBy.KEY:
        key_fn = lambda e: (e.key or "").lower()
    elif sort_by == SortBy.VALUE:
        key_fn = lambda e: (e.value or "").lower()
    else:  # LINE
        key_fn = lambda e: e.line

    sorted_kv = sorted(kv_entries, key=key_fn, reverse=reverse)

    if comments_first:
        final_entries: List[EnvEntry] = non_kv + sorted_kv
    else:
        final_entries = sorted_kv + non_kv

    return SortResult(
        source=parsed.source,
        entries=final_entries,
        sort_by=sort_by,
        order=order,
    )
