"""Promote .env entries from one environment to another with conflict detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.parser import ParseResult


class PromoteStatus(str, Enum):
    ADDED = "added"
    UPDATED = "updated"
    SKIPPED = "skipped"
    CONFLICT = "conflict"


@dataclass
class PromotedEntry:
    key: str
    source_value: str
    target_value: Optional[str]
    status: PromoteStatus

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "status": self.status.value,
        }


@dataclass
class PromoteResult:
    source: str
    target: str
    entries: List[PromotedEntry] = field(default_factory=list)

    @property
    def promoted_count(self) -> int:
        return sum(
            1 for e in self.entries
            if e.status in (PromoteStatus.ADDED, PromoteStatus.UPDATED)
        )

    @property
    def conflict_count(self) -> int:
        return sum(1 for e in self.entries if e.status == PromoteStatus.CONFLICT)

    @property
    def skipped_count(self) -> int:
        return sum(1 for e in self.entries if e.status == PromoteStatus.SKIPPED)

    def to_env_string(self) -> str:
        lines = []
        for e in self.entries:
            val = e.source_value if e.status != PromoteStatus.SKIPPED else e.target_value
            lines.append(f"{e.key}={val}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "promoted_count": self.promoted_count,
            "conflict_count": self.conflict_count,
            "skipped_count": self.skipped_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def promote(
    source: ParseResult,
    target: ParseResult,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    conflict_marker: bool = False,
) -> PromoteResult:
    """Promote keys from source into target.

    Args:
        source: Parsed source environment.
        target: Parsed target environment.
        keys: Specific keys to promote; if None, promote all source keys.
        overwrite: If True, overwrite existing target values without conflict.
        conflict_marker: If True, mark existing differing values as CONFLICT instead of SKIPPED.
    """
    src_dict: Dict[str, str] = {e.key: e.value for e in source.entries if e.key}
    tgt_dict: Dict[str, str] = {e.key: e.value for e in target.entries if e.key}

    promote_keys = keys if keys is not None else list(src_dict.keys())

    result = PromoteResult(source=source.source, target=target.source)

    for key in promote_keys:
        if key not in src_dict:
            continue
        src_val = src_dict[key]
        tgt_val = tgt_dict.get(key)

        if tgt_val is None:
            status = PromoteStatus.ADDED
        elif tgt_val == src_val:
            status = PromoteStatus.SKIPPED
        elif overwrite:
            status = PromoteStatus.UPDATED
        elif conflict_marker:
            status = PromoteStatus.CONFLICT
        else:
            status = PromoteStatus.SKIPPED

        result.entries.append(
            PromotedEntry(
                key=key,
                source_value=src_val,
                target_value=tgt_val,
                status=status,
            )
        )

    return result
