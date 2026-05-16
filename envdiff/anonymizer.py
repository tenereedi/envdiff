"""Anonymizer: replace secret values with deterministic tokens for safe sharing."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Dict

from .parser import ParseResult, EnvEntry
from .differ import is_secret


@dataclass
class AnonymizedEntry:
    key: str
    original_value: str
    anonymized_value: str
    is_secret: bool
    line_number: int

    def as_dict(self) -> Dict:
        return {
            "key": self.key,
            "anonymized_value": self.anonymized_value,
            "is_secret": self.is_secret,
            "line_number": self.line_number,
        }


@dataclass
class AnonymizeResult:
    source: str
    entries: List[AnonymizedEntry] = field(default_factory=list)
    token_map: Dict[str, str] = field(default_factory=dict)

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            lines.append(f"{entry.key}={entry.anonymized_value}")
        return "\n".join(lines) + "\n" if lines else ""

    def as_dict(self) -> Dict:
        return {
            "source": self.source,
            "entries": [e.as_dict() for e in self.entries],
            "token_map": self.token_map,
        }


def _make_token(key: str, value: str, salt: str = "") -> str:
    """Produce a short deterministic token for a secret value."""
    digest = hashlib.sha256(f"{salt}{key}:{value}".encode()).hexdigest()[:12]
    return f"REDACTED_{digest.upper()}"


def anonymize(parsed: ParseResult, salt: str = "") -> AnonymizeResult:
    """Replace secret values with deterministic tokens.

    Non-secret values are left unchanged. The token_map records the
    mapping from original value to token so callers can reverse or audit.
    """
    result = AnonymizeResult(source=parsed.source)
    for entry in parsed.entries:
        if not hasattr(entry, "key") or entry.key is None:
            continue
        secret = is_secret(entry.key)
        if secret:
            token = _make_token(entry.key, entry.value, salt)
            result.token_map[entry.value] = token
            anon_value = token
        else:
            anon_value = entry.value
        result.entries.append(
            AnonymizedEntry(
                key=entry.key,
                original_value=entry.value,
                anonymized_value=anon_value,
                is_secret=secret,
                line_number=entry.line_number,
            )
        )
    return result
