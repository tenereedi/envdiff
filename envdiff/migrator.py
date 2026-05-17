"""Migrate .env keys from old names to new names with optional value transforms."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class MigrateOperation:
    old_key: str
    new_key: str
    old_value: str
    new_value: str
    transformed: bool = False

    def as_dict(self) -> dict:
        return {
            "old_key": self.old_key,
            "new_key": self.new_key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "transformed": self.transformed,
        }


@dataclass
class MigrateResult:
    source: str
    entries: List[EnvEntry]
    operations: List[MigrateOperation] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    @property
    def migrated_count(self) -> int:
        return len(self.operations)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_keys)

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.key is not None:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "migrated_count": self.migrated_count,
            "skipped_count": self.skipped_count,
            "operations": [op.as_dict() for op in self.operations],
            "skipped_keys": self.skipped_keys,
        }


def migrate(
    parsed: ParseResult,
    mapping: Dict[str, str],
    value_transforms: Optional[Dict[str, str]] = None,
) -> MigrateResult:
    """Rename keys according to mapping; optionally override values via value_transforms."""
    transforms = value_transforms or {}
    existing_keys = {e.key for e in parsed.entries if e.key is not None}
    new_entries: List[EnvEntry] = []
    operations: List[MigrateOperation] = []
    skipped: List[str] = []

    for entry in parsed.entries:
        if entry.key is None:
            new_entries.append(entry)
            continue

        if entry.key in mapping:
            new_key = mapping[entry.key]
            # Skip if new key already exists in the file (avoid collision)
            if new_key in existing_keys and new_key != entry.key:
                skipped.append(entry.key)
                new_entries.append(entry)
                continue
            new_value = transforms.get(new_key, entry.value)
            transformed = new_key in transforms
            op = MigrateOperation(
                old_key=entry.key,
                new_key=new_key,
                old_value=entry.value,
                new_value=new_value,
                transformed=transformed,
            )
            operations.append(op)
            new_entry = EnvEntry(
                key=new_key,
                value=new_value,
                raw=f"{new_key}={new_value}",
                line_number=entry.line_number,
            )
            new_entries.append(new_entry)
        else:
            new_entries.append(entry)

    return MigrateResult(
        source=parsed.source,
        entries=new_entries,
        operations=operations,
        skipped_keys=skipped,
    )
