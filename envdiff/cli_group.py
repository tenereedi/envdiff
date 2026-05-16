"""CLI sub-command: envdiff group — display grouped .env entries."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.grouper import group_env


def build_group_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Group .env entries by key prefix or custom glob patterns."
    if sub is not None:
        p = sub.add_parser("group", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff group", description=desc)
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--pattern",
        metavar="GLOB=NAME",
        action="append",
        default=[],
        help="Custom grouping pattern, e.g. 'DB_*=database'. Repeatable.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def _parse_patterns(raw: list[str]) -> dict[str, str] | None:
    if not raw:
        return None
    result = {}
    for item in raw:
        if "=" not in item:
            print(f"[error] Invalid pattern '{item}', expected GLOB=NAME", file=sys.stderr)
            sys.exit(2)
        glob, name = item.split("=", 1)
        result[glob.strip()] = name.strip()
    return result or None


def _print_text(group_result) -> None:
    for name in group_result.group_names():
        entries = group_result.entries_for(name)
        print(f"[{name}]  ({len(entries)} keys)")
        for e in entries:
            print(f"  {e.key}")
        print()


def run_group(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"[error] File not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    parsed = parse_env_string(text, source=str(path))
    patterns = _parse_patterns(ns.pattern)
    result = group_env(parsed, patterns=patterns)

    if ns.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_group_parser()
    ns = parser.parse_args()
    sys.exit(run_group(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
