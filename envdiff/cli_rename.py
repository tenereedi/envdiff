"""CLI entry point for the rename subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.renamer import rename


def build_rename_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Rename one or more keys in a .env file."
    if parent is not None:
        parser = parent.add_parser("rename", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff rename", description=description)

    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--rename",
        metavar="OLD=NEW",
        dest="renames",
        action="append",
        default=[],
        required=True,
        help="Rename mapping in OLD=NEW format (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write result to FILE instead of stdout",
    )
    return parser


def _parse_rename_args(renames: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in renames:
        if "=" not in item:
            raise ValueError(f"Invalid rename spec (expected OLD=NEW): {item!r}")
        old, new = item.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def run_rename(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        mapping = _parse_rename_args(ns.renames)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parsed = parse_env_string(path.read_text(), source=str(path))
    result = rename(parsed, mapping)

    if ns.format == "json":
        output = json.dumps(result.as_dict(), indent=2)
    else:
        lines = [f"# renamed {op.old_key} -> {op.new_key}" for op in result.operations]
        if result.skipped:
            lines.append(f"# skipped (not found or conflict): {', '.join(result.skipped)}")
        lines.append("")
        lines.append(result.to_env_string())
        output = "\n".join(lines)

    if ns.output:
        Path(ns.output).write_text(output)
    else:
        print(output)

    return 1 if result.skipped else 0


def main() -> None:  # pragma: no cover
    parser = build_rename_parser()
    sys.exit(run_rename(parser.parse_args()))
