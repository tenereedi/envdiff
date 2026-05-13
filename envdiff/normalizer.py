"""Normalize .env file entries: trim whitespace, sort keys, deduplicate."""

from dataclasses import dataclass, field
from typing import List, Optional
from envdiff.parser import ParseResult, EnvEntry


@dataclass
class NormalizeResult:
    source: str
    entries: List[EnvEntry]
    removed_duplicates: List[str] = field(default_factory=list)
    trimmed_keys: List[str] = field(default_factory=list)

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
            "removed_duplicates": self.removed_duplicates,
            "trimmed_keys": self.trimmed_keys,
            "entries": [
                {"key": e.key, "value": e.value, "line": e.line}
                for e in self.entries
            ],
        }


def normalize(parsed: ParseResult, sort_keys: bool = True) -> NormalizeResult:
    """Normalize a ParseResult by deduplicating and optionally sorting entries."""
    seen: dict = {}
    removed_duplicates: List[str] = []
    trimmed_keys: List[str] = []

    for entry in parsed.entries:
        original_key = entry.key
        trimmed_key = entry.key.strip()
        trimmed_value = entry.value.strip() if entry.value else entry.value

        if trimmed_key != original_key:
            trimmed_keys.append(original_key)

        normalized_entry = EnvEntry(
            key=trimmed_key,
            value=trimmed_value,
            line=entry.line,
            comment=entry.comment,
        )

        if trimmed_key in seen:
            removed_duplicates.append(trimmed_key)
        seen[trimmed_key] = normalized_entry

    entries = list(seen.values())
    if sort_keys:
        entries = sorted(entries, key=lambda e: e.key)

    return NormalizeResult(
        source=parsed.source,
        entries=entries,
        removed_duplicates=removed_duplicates,
        trimmed_keys=trimmed_keys,
    )
