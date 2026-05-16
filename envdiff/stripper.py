"""Strip comments and blank lines from .env files, producing a clean output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import EnvEntry, ParseResult


@dataclass
class StripResult:
    source: str
    entries: List[EnvEntry]
    removed_comments: int
    removed_blanks: int

    def to_env_string(self) -> str:
        """Render stripped entries back to .env format."""
        lines = []
        for entry in self.entries:
            if entry.value is None:
                lines.append(entry.key)
            else:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "removed_comments": self.removed_comments,
            "removed_blanks": self.removed_blanks,
            "entry_count": len(self.entries),
            "entries": [
                {"key": e.key, "value": e.value, "line": e.line}
                for e in self.entries
            ],
        }


def strip(parsed: ParseResult, *, keep_blanks: bool = False) -> StripResult:
    """Return a StripResult with comments and optionally blank lines removed.

    Args:
        parsed: A ParseResult from ``parse_env_string``.
        keep_blanks: When True, blank lines between entries are preserved.

    Returns:
        StripResult with only key=value entries retained.
    """
    removed_comments = 0
    removed_blanks = 0
    clean_entries: List[EnvEntry] = []

    for entry in parsed.entries:
        # Entries whose key starts with '#' are comment pseudo-entries
        if entry.key.startswith("#"):
            removed_comments += 1
            continue
        # Entries with an empty key represent blank lines
        if entry.key == "":
            removed_blanks += 1
            if keep_blanks:
                clean_entries.append(entry)
            continue
        clean_entries.append(entry)

    return StripResult(
        source=parsed.source,
        entries=clean_entries,
        removed_comments=removed_comments,
        removed_blanks=removed_blanks,
    )
