"""Deduplicator: detect and remove duplicate keys from a parsed env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class DuplicateGroup:
    key: str
    entries: List[EnvEntry]

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "occurrences": len(self.entries),
            "line_numbers": [e.line_number for e in self.entries],
        }


@dataclass
class DeduplicateResult:
    source: str
    entries: List[EnvEntry]
    duplicates: List[DuplicateGroup]

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicates) > 0

    @property
    def duplicate_keys(self) -> List[str]:
        return [g.key for g in self.duplicates]

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.comment is not None:
                lines.append(f"{entry.key}={entry.value}  # {entry.comment}")
            else:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "entry_count": len(self.entries),
            "has_duplicates": self.has_duplicates,
            "duplicate_count": len(self.duplicates),
            "duplicates": [g.as_dict() for g in self.duplicates],
        }


def deduplicate(
    parsed: ParseResult,
    keep: str = "last",
) -> DeduplicateResult:
    """Remove duplicate keys, keeping either the 'first' or 'last' occurrence.

    Args:
        parsed: A ParseResult from parse_env_string.
        keep: 'first' keeps the first occurrence; 'last' keeps the last.

    Returns:
        DeduplicateResult with deduplicated entries and duplicate metadata.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    seen: Dict[str, List[EnvEntry]] = {}
    for entry in parsed.entries:
        seen.setdefault(entry.key, []).append(entry)

    duplicates = [
        DuplicateGroup(key=k, entries=v)
        for k, v in seen.items()
        if len(v) > 1
    ]

    # Build deduplicated list preserving original order
    chosen: Dict[str, EnvEntry] = {}
    for entry in parsed.entries:
        if keep == "first" and entry.key not in chosen:
            chosen[entry.key] = entry
        elif keep == "last":
            chosen[entry.key] = entry

    # Preserve original order by iterating entries once more
    seen_keys: set = set()
    deduped: List[EnvEntry] = []
    order_source = parsed.entries if keep == "first" else reversed(parsed.entries)
    for entry in order_source:
        if entry.key not in seen_keys:
            seen_keys.add(entry.key)
            deduped.append(chosen[entry.key])

    if keep == "last":
        deduped = list(reversed(deduped))

    return DeduplicateResult(
        source=parsed.source,
        entries=deduped,
        duplicates=duplicates,
    )
