"""Truncator: shorten long env values to a maximum display length."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import ParseResult, EnvEntry

DEFAULT_MAX_LENGTH = 40
TRUNCATION_SUFFIX = "..."


@dataclass
class TruncatedEntry:
    key: str
    original_value: str
    display_value: str
    was_truncated: bool
    line: int

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "original_value": self.original_value,
            "display_value": self.display_value,
            "was_truncated": self.was_truncated,
            "line": self.line,
        }


@dataclass
class TruncateResult:
    source: str
    entries: List[TruncatedEntry] = field(default_factory=list)
    max_length: int = DEFAULT_MAX_LENGTH

    @property
    def truncated_count(self) -> int:
        return sum(1 for e in self.entries if e.was_truncated)

    @property
    def total_count(self) -> int:
        return len(self.entries)

    def to_env_string(self) -> str:
        lines = []
        for e in self.entries:
            lines.append(f"{e.key}={e.display_value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "max_length": self.max_length,
            "truncated_count": self.truncated_count,
            "total_count": self.total_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def truncate(parsed: ParseResult, max_length: int = DEFAULT_MAX_LENGTH) -> TruncateResult:
    """Return a TruncateResult with values shortened to *max_length* characters."""
    if max_length < len(TRUNCATION_SUFFIX):
        raise ValueError(
            f"max_length must be at least {len(TRUNCATION_SUFFIX)}, got {max_length}"
        )

    entries: List[TruncatedEntry] = []
    for entry in parsed.entries:
        if not isinstance(entry, EnvEntry):
            continue
        raw = entry.value
        if len(raw) > max_length:
            keep = max_length - len(TRUNCATION_SUFFIX)
            display = raw[:keep] + TRUNCATION_SUFFIX
            was_truncated = True
        else:
            display = raw
            was_truncated = False
        entries.append(
            TruncatedEntry(
                key=entry.key,
                original_value=raw,
                display_value=display,
                was_truncated=was_truncated,
                line=entry.line,
            )
        )

    return TruncateResult(source=parsed.source, entries=entries, max_length=max_length)
