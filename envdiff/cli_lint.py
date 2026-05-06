"""CLI sub-command: lint an .env file."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from envdiff.linter import lint
from envdiff.parser import parse_env_string


def run_lint(args) -> int:  # returns exit code
    """Entry point for the `envdiff lint` sub-command."""
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    parsed = parse_env_string(path.read_text(encoding="utf-8"), source=str(path))
    result = lint(parsed)

    if getattr(args, "format", "text") == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result, str(path))

    return 1 if result.has_errors else 0


def _print_text(result, source: str) -> None:
    if not result.issues:
        print(f"✓  No lint issues found in {source}")
        return

    print(f"Lint results for {source}:")
    for issue in result.issues:
        icon = "✖" if issue.severity == "error" else "⚠"
        print(
            f"  {icon} [{issue.code}] line {issue.line}: {issue.message}"
        )
    print()
    errors = sum(1 for i in result.issues if i.severity == "error")
    warnings = sum(1 for i in result.issues if i.severity == "warning")
    print(f"  {errors} error(s), {warnings} warning(s)")
