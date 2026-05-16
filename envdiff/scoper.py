"""Scope filtering: restrict env entries to a named scope/environment prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class ScopedEntry:
    original_key: str
    scoped_key: str
    value: str
    line_number: int
    is_secret: bool = False

    def as_dict(self) -> dict:
        return {
            "original_key": self.original_key,
            "scoped_key": self.scoped_key,
            "value": self.value,
            "line_number": self.line_number,
            "is_secret": self.is_secret,
        }


@dataclass
class ScopeResult:
    source: str
    scope: str
    strip_prefix: bool
    entries: List[ScopedEntry] = field(default_factory=list)
    excluded_count: int = 0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "scope": self.scope,
            "strip_prefix": self.strip_prefix,
            "matched_count": len(self.entries),
            "excluded_count": self.excluded_count,
            "entries": [e.as_dict() for e in self.entries],
        }

    def to_env_string(self) -> str:
        lines = []
        for e in self.entries:
            key = e.scoped_key if self.strip_prefix else e.original_key
            lines.append(f"{key}={e.value}")
        return "\n".join(lines)


def scope(parsed: ParseResult, scope_prefix: str, strip_prefix: bool = False) -> ScopeResult:
    """Filter entries to those matching *scope_prefix* (case-insensitive).

    Args:
        parsed: A parsed .env file.
        scope_prefix: Prefix to match, e.g. ``"PROD"`` matches ``PROD_DB_HOST``.
        strip_prefix: When *True*, the matched prefix and trailing underscore are
            removed from ``scoped_key``.
    """
    from envdiff.differ import is_secret as _is_secret

    normalised = scope_prefix.upper().rstrip("_") + "_"
    matched: List[ScopedEntry] = []
    excluded = 0

    for entry in parsed.entries:
        if entry.key is None:
            continue
        if entry.key.upper().startswith(normalised):
            scoped_key = entry.key[len(normalised):] if strip_prefix else entry.key
            matched.append(
                ScopedEntry(
                    original_key=entry.key,
                    scoped_key=scoped_key,
                    value=entry.value or "",
                    line_number=entry.line_number,
                    is_secret=_is_secret(entry.key),
                )
            )
        else:
            excluded += 1

    return ScopeResult(
        source=parsed.source,
        scope=scope_prefix,
        strip_prefix=strip_prefix,
        entries=matched,
        excluded_count=excluded,
    )
