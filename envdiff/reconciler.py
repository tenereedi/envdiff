"""Reconcile two .env files by applying diffs to produce a merged output."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from envdiff.differ import DiffEntry, DiffStatus
from envdiff.parser import EnvEntry, ParseResult


@dataclass
class ReconcileAction:
    """Represents a single reconciliation decision for a key."""

    key: str
    action: str  # 'keep_a', 'keep_b', 'keep_both', 'skip'
    resolved_value: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class ReconcileResult:
    """Result of reconciling two env files."""

    entries: List[EnvEntry]
    actions: List[ReconcileAction]
    skipped_keys: List[str]

    def as_dict(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}

    def to_env_string(self) -> str:
        lines = []
        for entry in self.entries:
            if entry.comment:
                lines.append(f"# {entry.comment}")
            lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines) + "\n" if lines else ""


def reconcile(
    base: ParseResult,
    override: ParseResult,
    diffs: List[DiffEntry],
    prefer: str = "b",
) -> ReconcileResult:
    """Reconcile two parsed env files using diff entries.

    Args:
        base: Parsed result of the base (A) env file.
        override: Parsed result of the override (B) env file.
        diffs: List of DiffEntry from differ.diff().
        prefer: Which side to prefer for changed keys ('a' or 'b').

    Returns:
        ReconcileResult with merged entries and action log.
    """
    base_dict = base.as_dict()
    override_dict = override.as_dict()
    actions: List[ReconcileAction] = []
    resolved: Dict[str, str] = {}

    for diff_entry in diffs:
        key = diff_entry.key
        if diff_entry.status == DiffStatus.UNCHANGED:
            resolved[key] = base_dict[key]
            actions.append(ReconcileAction(key=key, action="keep_a", resolved_value=base_dict[key]))
        elif diff_entry.status == DiffStatus.ADDED:
            resolved[key] = override_dict[key]
            actions.append(ReconcileAction(key=key, action="keep_b", resolved_value=override_dict[key]))
        elif diff_entry.status == DiffStatus.REMOVED:
            actions.append(ReconcileAction(key=key, action="skip", comment="removed in B"))
        elif diff_entry.status == DiffStatus.CHANGED:
            if prefer == "a":
                resolved[key] = base_dict[key]
                actions.append(ReconcileAction(key=key, action="keep_a", resolved_value=base_dict[key]))
            else:
                resolved[key] = override_dict[key]
                actions.append(ReconcileAction(key=key, action="keep_b", resolved_value=override_dict[key]))

    skipped = [a.key for a in actions if a.action == "skip"]
    entries = [
        EnvEntry(key=k, value=v, line_number=i + 1)
        for i, (k, v) in enumerate(resolved.items())
    ]

    return ReconcileResult(entries=entries, actions=actions, skipped_keys=skipped)
