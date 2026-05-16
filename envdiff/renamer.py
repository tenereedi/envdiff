"""Renamer: rename keys across a parsed .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class RenameOperation:
    old_key: str
    new_key: str
    value: str
    line: int

    def as_dict(self) -> dict:
        return {
            "old_key": self.old_key,
            "new_key": self.new_key,
            "value": self.value,
            "line": self.line,
        }


@dataclass
class RenameResult:
    source: str
    entries: List[EnvEntry]
    operations: List[RenameOperation] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def renamed_count(self) -> int:
        return len(self.operations)

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.comment is not None:
                lines.append(f"{entry.key}={entry.value}  # {entry.comment}")
            else:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "renamed_count": self.renamed_count,
            "skipped": self.skipped,
            "operations": [op.as_dict() for op in self.operations],
            "entries": [
                {"key": e.key, "value": e.value, "line": e.line}
                for e in self.entries
            ],
        }


def rename(parsed: ParseResult, mapping: Dict[str, str]) -> RenameResult:
    """Rename keys according to *mapping* (old_key -> new_key).

    Keys in *mapping* that do not exist in *parsed* are recorded in
    ``skipped``.  If a ``new_key`` already exists in the file the
    operation is also skipped to avoid duplicate keys.
    """
    existing_keys = {e.key for e in parsed.entries}
    operations: List[RenameOperation] = []
    skipped: List[str] = []

    # Validate mapping before mutating anything
    effective: Dict[str, str] = {}
    for old, new in mapping.items():
        if old not in existing_keys:
            skipped.append(old)
        elif new in existing_keys and new != old:
            skipped.append(old)
        else:
            effective[old] = new

    new_entries: List[EnvEntry] = []
    for entry in parsed.entries:
        if entry.key in effective:
            new_key = effective[entry.key]
            op = RenameOperation(
                old_key=entry.key,
                new_key=new_key,
                value=entry.value,
                line=entry.line,
            )
            operations.append(op)
            new_entries.append(
                EnvEntry(key=new_key, value=entry.value, line=entry.line, comment=entry.comment)
            )
        else:
            new_entries.append(entry)

    return RenameResult(
        source=parsed.source,
        entries=new_entries,
        operations=operations,
        skipped=skipped,
    )
