"""Filter .env entries by pattern, category, or secret status."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from envdiff.parser import ParseResult, EnvEntry
from envdiff.differ import is_secret


@dataclass
class FilterResult:
    source: str
    entries: List[EnvEntry]
    total_before: int
    pattern: Optional[str]
    secrets_only: bool
    non_secrets_only: bool

    @property
    def total_after(self) -> int:
        return len(self.entries)

    @property
    def removed_count(self) -> int:
        return self.total_before - self.total_after

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "pattern": self.pattern,
            "secrets_only": self.secrets_only,
            "non_secrets_only": self.non_secrets_only,
            "total_before": self.total_before,
            "total_after": self.total_after,
            "removed_count": self.removed_count,
            "entries": [
                {"key": e.key, "value": e.value, "line": e.line_number}
                for e in self.entries
            ],
        }

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.value is None:
                lines.append(entry.key)
            else:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)


def filter_env(
    parsed: ParseResult,
    *,
    pattern: Optional[str] = None,
    secrets_only: bool = False,
    non_secrets_only: bool = False,
) -> FilterResult:
    """Return a FilterResult containing only entries that match the given criteria.

    Args:
        parsed: Parsed .env file.
        pattern: Optional glob pattern matched against key names (e.g. ``DB_*``).
        secrets_only: When True, keep only keys detected as secrets.
        non_secrets_only: When True, keep only keys NOT detected as secrets.

    Note:
        ``secrets_only`` and ``non_secrets_only`` are mutually exclusive; if both
        are True, ``secrets_only`` takes precedence.
    """
    entries = list(parsed.entries)
    total_before = len(entries)

    if pattern:
        entries = [e for e in entries if fnmatch(e.key, pattern)]

    if secrets_only:
        entries = [e for e in entries if is_secret(e.key)]
    elif non_secrets_only:
        entries = [e for e in entries if not is_secret(e.key)]

    return FilterResult(
        source=parsed.source,
        entries=entries,
        total_before=total_before,
        pattern=pattern,
        secrets_only=secrets_only,
        non_secrets_only=non_secrets_only,
    )
