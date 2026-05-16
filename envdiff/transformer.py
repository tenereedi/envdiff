"""Transform .env entries by applying key/value mutations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envdiff.parser import EnvEntry, ParseResult


@dataclass
class TransformOperation:
    key: str
    original_value: str
    new_value: str
    transform_name: str

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "original_value": self.original_value,
            "new_value": self.new_value,
            "transform_name": self.transform_name,
        }


@dataclass
class TransformResult:
    source: str
    entries: List[EnvEntry]
    operations: List[TransformOperation] = field(default_factory=list)

    @property
    def changed_count(self) -> int:
        return len(self.operations)

    def to_env_string(self) -> str:
        lines: List[str] = []
        for entry in self.entries:
            if entry.key is not None:
                lines.append(f"{entry.key}={entry.value}")
            elif entry.comment is not None:
                lines.append(entry.comment)
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "changed_count": self.changed_count,
            "operations": [op.as_dict() for op in self.operations],
            "entries": [
                {"key": e.key, "value": e.value}
                for e in self.entries
                if e.key is not None
            ],
        }


# Built-in transform functions
_TRANSFORMS: Dict[str, Callable[[str], str]] = {
    "uppercase": str.upper,
    "lowercase": str.lower,
    "strip": str.strip,
    "strip_quotes": lambda v: v.strip('"\' '),
}


def transform(
    parsed: ParseResult,
    transforms: Dict[str, str],
    custom_transforms: Optional[Dict[str, Callable[[str], str]]] = None,
) -> TransformResult:
    """Apply named transforms to specified keys.

    Args:
        parsed: Parsed .env result.
        transforms: Mapping of key -> transform name.
        custom_transforms: Optional extra transform functions by name.

    Returns:
        TransformResult with updated entries and recorded operations.
    """
    registry = {**_TRANSFORMS, **(custom_transforms or {})}
    ops: List[TransformOperation] = []
    new_entries: List[EnvEntry] = []

    for entry in parsed.entries:
        if entry.key is not None and entry.key in transforms:
            name = transforms[entry.key]
            fn = registry.get(name)
            if fn is None:
                raise ValueError(f"Unknown transform '{name}' for key '{entry.key}'")
            new_val = fn(entry.value or "")
            ops.append(TransformOperation(entry.key, entry.value or "", new_val, name))
            new_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=new_val,
                    comment=entry.comment,
                    line_number=entry.line_number,
                    raw=entry.raw,
                )
            )
        else:
            new_entries.append(entry)

    return TransformResult(source=parsed.source, entries=new_entries, operations=ops)
