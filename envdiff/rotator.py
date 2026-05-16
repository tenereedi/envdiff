"""Key rotation support: detect stale keys and generate rotation candidates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from envdiff.parser import ParseResult, EnvEntry
from envdiff.differ import is_secret


@dataclass
class RotationCandidate:
    key: str
    current_value: str
    masked: bool
    reason: str
    suggested_placeholder: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "current_value": "***" if self.masked else self.current_value,
            "masked": self.masked,
            "reason": self.reason,
            "suggested_placeholder": self.suggested_placeholder,
        }


@dataclass
class RotateResult:
    source: str
    candidates: List[RotationCandidate] = field(default_factory=list)
    rotated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def has_candidates(self) -> bool:
        return len(self.candidates) > 0

    @property
    def candidate_keys(self) -> List[str]:
        return [c.key for c in self.candidates]

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "rotated_at": self.rotated_at,
            "has_candidates": self.has_candidates,
            "candidate_count": len(self.candidates),
            "candidates": [c.as_dict() for c in self.candidates],
        }


_STALE_PATTERNS = ("old", "legacy", "deprecated", "backup", "tmp", "test", "debug")
_PLACEHOLDER_PATTERNS = ("changeme", "placeholder", "fixme", "todo", "xxx", "replace")


def _reason_for(entry: EnvEntry) -> Optional[str]:
    key_lower = entry.key.lower()
    val_lower = entry.value.lower() if entry.value else ""
    for pat in _STALE_PATTERNS:
        if pat in key_lower:
            return f"key contains stale marker '{pat}'"
    for pat in _PLACEHOLDER_PATTERNS:
        if pat in val_lower:
            return f"value looks like a placeholder ('{pat}')"
    if is_secret(entry.key) and not entry.value:
        return "secret key has empty value"
    return None


def rotate(parsed: ParseResult) -> RotateResult:
    """Identify keys that are candidates for rotation."""
    result = RotateResult(source=parsed.source)
    for entry in parsed.entries:
        if entry.key is None:
            continue
        reason = _reason_for(entry)
        if reason:
            placeholder = f"REPLACE_WITH_{entry.key}"
            result.candidates.append(
                RotationCandidate(
                    key=entry.key,
                    current_value=entry.value or "",
                    masked=is_secret(entry.key),
                    reason=reason,
                    suggested_placeholder=placeholder,
                )
            )
    return result
