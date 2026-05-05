"""Diff logic for comparing two parsed .env files."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.parser import ParseResult


class DiffStatus(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    value_a: Optional[str] = None  # value in env A (None if not present)
    value_b: Optional[str] = None  # value in env B (None if not present)

    @property
    def is_secret(self) -> bool:
        """Heuristic: key contains SECRET, PASSWORD, TOKEN, KEY, etc."""
        upper = self.key.upper()
        return any(
            word in upper
            for word in ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "KEY", "PRIVATE", "CREDENTIAL")
        )

    def masked_value_a(self) -> Optional[str]:
        return _mask(self.value_a) if self.is_secret else self.value_a

    def masked_value_b(self) -> Optional[str]:
        return _mask(self.value_b) if self.is_secret else self.value_b


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.ADDED]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.REMOVED]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.CHANGED]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.UNCHANGED]

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def _mask(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if len(value) <= 4:
        return "***"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def diff_envs(result_a: ParseResult, result_b: ParseResult) -> DiffResult:
    """Compare two ParseResult objects and return a DiffResult."""
    dict_a: Dict[str, str] = result_a.as_dict()
    dict_b: Dict[str, str] = result_b.as_dict()
    all_keys = sorted(set(dict_a) | set(dict_b))

    entries: List[DiffEntry] = []
    for key in all_keys:
        in_a = key in dict_a
        in_b = key in dict_b
        if in_a and not in_b:
            entries.append(DiffEntry(key=key, status=DiffStatus.REMOVED, value_a=dict_a[key]))
        elif in_b and not in_a:
            entries.append(DiffEntry(key=key, status=DiffStatus.ADDED, value_b=dict_b[key]))
        elif dict_a[key] != dict_b[key]:
            entries.append(DiffEntry(key=key, status=DiffStatus.CHANGED, value_a=dict_a[key], value_b=dict_b[key]))
        else:
            entries.append(DiffEntry(key=key, status=DiffStatus.UNCHANGED, value_a=dict_a[key], value_b=dict_b[key]))

    return DiffResult(entries=entries)
