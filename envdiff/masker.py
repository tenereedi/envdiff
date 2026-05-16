"""Masker: selectively mask values in a parsed env file based on patterns or secret detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.parser import ParseResult, EnvEntry
from envdiff.differ import is_secret

DEFAULT_MASK = "***"


@dataclass
class MaskedEntry:
    key: str
    original_value: str
    masked_value: str
    was_masked: bool
    line: int

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "original_value": self.original_value if not self.was_masked else None,
            "masked_value": self.masked_value,
            "was_masked": self.was_masked,
            "line": self.line,
        }


@dataclass
class MaskResult:
    source: str
    entries: List[MaskedEntry] = field(default_factory=list)
    mask_token: str = DEFAULT_MASK

    @property
    def masked_count(self) -> int:
        return sum(1 for e in self.entries if e.was_masked)

    @property
    def total_count(self) -> int:
        return len(self.entries)

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            lines.append(f"{entry.key}={entry.masked_value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "mask_token": self.mask_token,
            "masked_count": self.masked_count,
            "total_count": self.total_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def mask(
    parsed: ParseResult,
    keys: Optional[List[str]] = None,
    auto_detect: bool = True,
    mask_token: str = DEFAULT_MASK,
) -> MaskResult:
    """Mask values in *parsed*.

    If *keys* is provided those keys are always masked.  When *auto_detect* is
    True, keys that look like secrets (via :func:`is_secret`) are also masked.
    """
    explicit = set(keys) if keys else set()
    result = MaskResult(source=parsed.source, mask_token=mask_token)

    for entry in parsed.entries:
        if entry.key is None:
            continue
        should_mask = entry.key in explicit or (auto_detect and is_secret(entry.key))
        original = entry.value or ""
        masked = mask_token if should_mask else original
        result.entries.append(
            MaskedEntry(
                key=entry.key,
                original_value=original,
                masked_value=masked,
                was_masked=should_mask,
                line=entry.line,
            )
        )

    return result
