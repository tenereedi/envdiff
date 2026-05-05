"""Export reconciled env results to various output formats."""

import json
from typing import IO, Optional

from envdiff.reconciler import ReconcileResult


def export_env(result: ReconcileResult, stream: IO[str]) -> None:
    """Write reconciled result as a .env file to the given stream."""
    stream.write(result.to_env_string())


def export_json(result: ReconcileResult, stream: IO[str], mask_secrets: bool = True) -> None:
    """Write reconciled result as JSON to the given stream.

    Args:
        result: The reconciled result to export.
        stream: Output stream to write to.
        mask_secrets: If True, mask values for secret-like keys.
    """
    from envdiff.differ import is_secret

    data = {
        "entries": [
            {
                "key": e.key,
                "value": "***" if mask_secrets and is_secret(e.key) else e.value,
            }
            for e in result.entries
        ],
        "skipped_keys": result.skipped_keys,
        "actions": [
            {
                "key": a.key,
                "action": a.action,
                "resolved_value": (
                    "***"
                    if mask_secrets and a.resolved_value and is_secret(a.key)
                    else a.resolved_value
                ),
                "comment": a.comment,
            }
            for a in result.actions
        ],
    }
    json.dump(data, stream, indent=2)
    stream.write("\n")


def export_summary(result: ReconcileResult, stream: IO[str]) -> None:
    """Write a human-readable summary of reconciliation actions."""
    total = len(result.actions)
    skipped = len(result.skipped_keys)
    kept = total - skipped

    stream.write(f"Reconciliation Summary\n")
    stream.write(f"  Total keys processed : {total}\n")
    stream.write(f"  Keys kept            : {kept}\n")
    stream.write(f"  Keys skipped         : {skipped}\n")

    if result.skipped_keys:
        stream.write("  Skipped keys:\n")
        for key in result.skipped_keys:
            stream.write(f"    - {key}\n")

    action_counts: dict = {}
    for a in result.actions:
        action_counts[a.action] = action_counts.get(a.action, 0) + 1

    stream.write("  Action breakdown:\n")
    for action, count in sorted(action_counts.items()):
        stream.write(f"    {action:<12}: {count}\n")
