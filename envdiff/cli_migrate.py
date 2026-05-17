"""CLI entry point for the migrate command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.migrator import migrate


def build_migrate_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:
    description = "Rename .env keys according to a mapping."
    if parent is not None:
        parser = parent.add_parser("migrate", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-migrate", description=description)

    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        default=[],
        help="Key rename rule (repeatable). Example: --rename APP_HOST=HOST",
    )
    parser.add_argument(
        "--set",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        dest="value_transforms",
        help="Override value for a (new) key after rename (repeatable).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
    )
    parser.add_argument("--output", "-o", default=None, help="Write result to file instead of stdout")
    return parser


def _parse_kv_args(args: list[str]) -> dict:
    result = {}
    for item in args:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def run_migrate(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text()
    parsed = parse_env_string(text, source=str(path))
    mapping = _parse_kv_args(ns.rename)
    transforms = _parse_kv_args(ns.value_transforms)

    if not mapping:
        print("warning: no --rename rules provided; nothing to migrate.", file=sys.stderr)

    result = migrate(parsed, mapping=mapping, value_transforms=transforms or None)

    if ns.output_format == "json":
        output = json.dumps(result.as_dict(), indent=2)
    else:
        lines = [f"# Migrated: {result.migrated_count} key(s), skipped: {result.skipped_count}"]
        for op in result.operations:
            tag = " [transformed]" if op.transformed else ""
            lines.append(f"#   {op.old_key} -> {op.new_key}{tag}")
        lines.append("")
        lines.append(result.to_env_string())
        output = "\n".join(lines)

    if ns.output:
        Path(ns.output).write_text(output)
    else:
        print(output)

    return 1 if result.skipped_count > 0 else 0


def main() -> None:
    parser = build_migrate_parser()
    ns = parser.parse_args()
    sys.exit(run_migrate(ns))


if __name__ == "__main__":
    main()
