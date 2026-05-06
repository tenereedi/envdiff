"""CLI helpers for the audit sub-command."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from envdiff.auditor import AuditLog, build_audit_event
from envdiff.differ import diff_envs
from envdiff.parser import parse_env_string


def run_audit(
    path_a: str,
    path_b: str,
    output: Optional[str] = None,
    operation: str = "diff",
    note: Optional[str] = None,
    append: bool = False,
) -> int:
    """Diff two env files and append an audit event to an audit log file.

    Returns exit code: 0 on success, 1 on error.
    """
    try:
        text_a = Path(path_a).read_text(encoding="utf-8")
        text_b = Path(path_b).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parsed_a = parse_env_string(text_a)
    parsed_b = parse_env_string(text_b)
    diffs = diff_envs(parsed_a, parsed_b)

    event = build_audit_event(
        diffs,
        source_a=path_a,
        source_b=path_b,
        operation=operation,
        note=note,
    )

    log = AuditLog()

    if output:
        out_path = Path(output)
        if append and out_path.exists():
            import json
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            from envdiff.auditor import AuditEvent
            for raw in existing:
                s = raw["summary"]
                log.add(AuditEvent(
                    timestamp=raw["timestamp"],
                    operation=raw["operation"],
                    source_a=raw["source_a"],
                    source_b=raw["source_b"],
                    total_keys=s["total_keys"],
                    added=s["added"],
                    removed=s["removed"],
                    changed=s["changed"],
                    unchanged=s["unchanged"],
                    note=raw.get("note"),
                ))
        log.add(event)
        out_path.write_text(log.to_json(), encoding="utf-8")
        print(f"Audit log written to {output}")
    else:
        log.add(event)
        print(log.to_json())

    return 0
