"""Group .env entries by prefix, category, or custom pattern."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class GroupEntry:
    key: str
    value: str
    group: str
    line_number: int

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "group": self.group,
            "line_number": self.line_number,
        }


@dataclass
class GroupResult:
    source: str
    groups: Dict[str, List[GroupEntry]] = field(default_factory=dict)

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def entries_for(self, group: str) -> List[GroupEntry]:
        return self.groups.get(group, [])

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "groups": {
                name: [e.as_dict() for e in entries]
                for name, entries in self.groups.items()
            },
        }


def _resolve_group(key: str, patterns: Optional[Dict[str, str]]) -> str:
    """Return the first matching pattern group name, or derive from prefix."""
    if patterns:
        for pattern, group_name in patterns.items():
            if fnmatch(key, pattern):
                return group_name
    # Default: use the part before the first underscore, or 'default'
    if "_" in key:
        return key.split("_")[0].upper()
    return "DEFAULT"


def group_env(
    parsed: ParseResult,
    patterns: Optional[Dict[str, str]] = None,
) -> GroupResult:
    """Group all entries in *parsed* by prefix or custom *patterns*.

    *patterns* maps glob patterns to group names, evaluated in insertion order.
    """
    result = GroupResult(source=parsed.source)
    for entry in parsed.entries:
        group_name = _resolve_group(entry.key, patterns)
        ge = GroupEntry(
            key=entry.key,
            value=entry.value,
            group=group_name,
            line_number=entry.line_number,
        )
        result.groups.setdefault(group_name, []).append(ge)
    return result
