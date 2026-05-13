"""Patch a .env file by applying a set of key-value overrides."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class PatchOperation:
    key: str
    old_value: Optional[str]  # None means key did not exist
    new_value: Optional[str]  # None means key was removed

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class PatchResult:
    source: str
    operations: List[PatchOperation] = field(default_factory=list)
    entries: List[EnvEntry] = field(default_factory=list)

    def to_env_string(self) -> str:
        lines: List[str] = []
        for entry in self.entries:
            if entry.comment and not entry.key:
                lines.append(entry.comment)
            elif entry.key:
                if entry.comment:
                    lines.append(f"{entry.key}={entry.value}  {entry.comment}")
                else:
                    lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "operations": [op.as_dict() for op in self.operations],
            "entry_count": len(self.entries),
        }


def patch(parsed: ParseResult, overrides: Dict[str, Optional[str]]) -> PatchResult:
    """Apply key-value overrides to a parsed env, returning a PatchResult.

    If a value in *overrides* is None the key is removed from the output.
    Keys not present in *overrides* are left unchanged.
    New keys are appended at the end.
    """
    existing: Dict[str, EnvEntry] = {e.key: e for e in parsed.entries if e.key}
    ops: List[PatchOperation] = []
    updated: Dict[str, EnvEntry] = {}

    # Carry over existing entries, applying overrides
    for entry in parsed.entries:
        if entry.key is None:
            # comment / blank line — preserve as-is
            updated[f"__blank_{id(entry)}"] = entry
            continue
        if entry.key in overrides:
            new_val = overrides[entry.key]
            if new_val is None:
                ops.append(PatchOperation(entry.key, entry.value, None))
                # skip — removal
                continue
            ops.append(PatchOperation(entry.key, entry.value, new_val))
            updated[entry.key] = EnvEntry(
                key=entry.key,
                value=new_val,
                comment=entry.comment,
                line_number=entry.line_number,
            )
        else:
            updated[entry.key] = entry

    # Append brand-new keys
    for key, new_val in overrides.items():
        if key not in existing and new_val is not None:
            ops.append(PatchOperation(key, None, new_val))
            updated[key] = EnvEntry(key=key, value=new_val, comment=None, line_number=None)

    return PatchResult(
        source=parsed.source,
        operations=ops,
        entries=list(updated.values()),
    )
