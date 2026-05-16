"""Flattener: collapse nested/prefixed env groups into a flat canonical form."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class FlattenedEntry:
    original_key: str
    flat_key: str
    value: str
    was_renamed: bool

    def as_dict(self) -> dict:
        return {
            "original_key": self.original_key,
            "flat_key": self.flat_key,
            "value": self.value,
            "was_renamed": self.was_renamed,
        }


@dataclass
class FlattenResult:
    source: str
    entries: List[FlattenedEntry] = field(default_factory=list)
    strip_prefix: Optional[str] = None

    @property
    def renamed_count(self) -> int:
        return sum(1 for e in self.entries if e.was_renamed)

    def to_env_string(self) -> str:
        lines = []
        for e in self.entries:
            lines.append(f"{e.flat_key}={e.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "strip_prefix": self.strip_prefix,
            "renamed_count": self.renamed_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def flatten(parsed: ParseResult, strip_prefix: Optional[str] = None) -> FlattenResult:
    """Flatten env entries by optionally stripping a key prefix.

    Args:
        parsed: Parsed .env result.
        strip_prefix: If provided, remove this prefix (case-sensitive) from
                      matching keys. Keys that do not start with the prefix
                      are kept unchanged.

    Returns:
        FlattenResult with all entries mapped to their flat keys.
    """
    result = FlattenResult(source=parsed.source, strip_prefix=strip_prefix)

    for entry in parsed.entries:
        if entry.key is None:
            continue

        original_key = entry.key
        value = entry.value or ""

        if strip_prefix and original_key.startswith(strip_prefix):
            flat_key = original_key[len(strip_prefix):]
            was_renamed = flat_key != original_key
        else:
            flat_key = original_key
            was_renamed = False

        result.entries.append(
            FlattenedEntry(
                original_key=original_key,
                flat_key=flat_key,
                value=value,
                was_renamed=was_renamed,
            )
        )

    return result
