"""Merge two parsed .env files with configurable conflict resolution strategies."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.parser import ParseResult, EnvEntry


class MergeStrategy(str, Enum):
    PREFER_A = "prefer_a"
    PREFER_B = "prefer_b"
    UNION = "union"          # include all keys; conflicts resolved by strategy
    INTERSECTION = "intersection"  # only keys present in both


@dataclass
class MergeConflict:
    key: str
    value_a: str
    value_b: str
    resolved_value: str

    def as_dict(self) -> Dict:
        return {
            "key": self.key,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "resolved_value": self.resolved_value,
        }


@dataclass
class MergeResult:
    entries: List[EnvEntry] = field(default_factory=list)
    conflicts: List[MergeConflict] = field(default_factory=list)
    strategy: MergeStrategy = MergeStrategy.PREFER_B

    def as_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "entry_count": len(self.entries),
            "conflict_count": len(self.conflicts),
            "conflicts": [c.as_dict() for c in self.conflicts],
        }

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.comment and not entry.key:
                lines.append(entry.comment)
            elif entry.key:
                lines.append(f"{entry.key}={entry.value}")
            else:
                lines.append("")
        return "\n".join(lines)


def merge(
    parsed_a: ParseResult,
    parsed_b: ParseResult,
    strategy: MergeStrategy = MergeStrategy.PREFER_B,
) -> MergeResult:
    """Merge two ParseResult objects according to the given strategy."""
    dict_a: Dict[str, EnvEntry] = {e.key: e for e in parsed_a.entries if e.key}
    dict_b: Dict[str, EnvEntry] = {e.key: e for e in parsed_b.entries if e.key}

    if strategy == MergeStrategy.INTERSECTION:
        keys = sorted(set(dict_a) & set(dict_b))
    else:
        keys = sorted(set(dict_a) | set(dict_b))

    result = MergeResult(strategy=strategy)

    for key in keys:
        in_a = key in dict_a
        in_b = key in dict_b

        if in_a and in_b and dict_a[key].value != dict_b[key].value:
            # Conflict
            resolved_entry = dict_b[key] if strategy != MergeStrategy.PREFER_A else dict_a[key]
            resolved_value = resolved_entry.value
            result.conflicts.append(
                MergeConflict(
                    key=key,
                    value_a=dict_a[key].value,
                    value_b=dict_b[key].value,
                    resolved_value=resolved_value,
                )
            )
            result.entries.append(resolved_entry)
        elif in_b:
            result.entries.append(dict_b[key])
        else:
            result.entries.append(dict_a[key])

    return result
