"""Extract a subset of keys from a parsed env into a new result."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from envdiff.parser import EnvEntry, ParseResult


@dataclass
class ExtractedEntry:
    key: str
    value: str
    original_line: int
    was_requested: bool

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "original_line": self.original_line,
            "was_requested": self.was_requested,
        }


@dataclass
class ExtractResult:
    source: str
    entries: List[ExtractedEntry] = field(default_factory=list)
    missing_keys: List[str] = field(default_factory=list)

    @property
    def found_count(self) -> int:
        return len(self.entries)

    @property
    def missing_count(self) -> int:
        return len(self.missing_keys)

    def to_env_string(self) -> str:
        lines = []
        for e in self.entries:
            if " " in e.value or "#" in e.value:
                lines.append(f'{e.key}="{e.value}"')
            else:
                lines.append(f"{e.key}={e.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "found_count": self.found_count,
            "missing_count": self.missing_count,
            "missing_keys": self.missing_keys,
            "entries": [e.as_dict() for e in self.entries],
        }


def extract(
    parsed: ParseResult,
    keys: Sequence[str],
    ignore_missing: bool = False,
) -> ExtractResult:
    """Extract *keys* from *parsed*, returning an ExtractResult.

    Args:
        parsed: The parsed env to extract from.
        keys: The ordered list of keys to extract.
        ignore_missing: When True, missing keys are recorded but do not
            raise an error.  When False (default) they are still recorded
            in ``missing_keys`` – callers decide how to handle them.
    """
    lookup: dict[str, EnvEntry] = {
        e.key: e for e in parsed.entries if e.key is not None
    }

    requested_set = list(dict.fromkeys(keys))  # deduplicate, preserve order

    entries: List[ExtractedEntry] = []
    missing: List[str] = []

    for key in requested_set:
        if key in lookup:
            e = lookup[key]
            entries.append(
                ExtractedEntry(
                    key=e.key,
                    value=e.value or "",
                    original_line=e.line,
                    was_requested=True,
                )
            )
        else:
            missing.append(key)

    return ExtractResult(
        source=parsed.source,
        entries=entries,
        missing_keys=missing,
    )
