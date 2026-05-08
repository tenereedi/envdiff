"""Redactor module: mask or strip secrets from env content before sharing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.parser import ParseResult, EnvEntry
from envdiff.differ import is_secret

DEFAULT_MASK = "***REDACTED***"


@dataclass
class RedactedEntry:
    key: str
    original_value: Optional[str]
    redacted_value: str
    was_redacted: bool
    line_number: int

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "redacted_value": self.redacted_value,
            "was_redacted": self.was_redacted,
            "line_number": self.line_number,
        }


@dataclass
class RedactResult:
    source: str
    entries: List[RedactedEntry] = field(default_factory=list)
    redacted_count: int = 0

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            lines.append(f"{entry.key}={entry.redacted_value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "redacted_count": self.redacted_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def redact(
    parsed: ParseResult,
    mask: str = DEFAULT_MASK,
    extra_keys: Optional[List[str]] = None,
    keep_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Return a RedactResult with secrets replaced by *mask*.

    Args:
        parsed:     Parsed env file to redact.
        mask:       Replacement string for secret values.
        extra_keys: Additional key names (case-insensitive) to always redact.
        keep_keys:  Key names (case-insensitive) to never redact even if they
                    look like secrets.
    """
    extra = {k.upper() for k in (extra_keys or [])}
    keep = {k.upper() for k in (keep_keys or [])}

    result = RedactResult(source=parsed.source)

    for entry in parsed.entries:
        upper = entry.key.upper()
        should_redact = (is_secret(entry.key) or upper in extra) and upper not in keep
        redacted_value = mask if should_redact else (entry.value or "")
        result.entries.append(
            RedactedEntry(
                key=entry.key,
                original_value=entry.value,
                redacted_value=redacted_value,
                was_redacted=should_redact,
                line_number=entry.line_number,
            )
        )
        if should_redact:
            result.redacted_count += 1

    return result
