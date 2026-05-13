"""CLI entry-point for the `envdiff patch` sub-command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from envdiff.parser import parse_env_string
from envdiff.patcher import patch


def build_patch_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Patch a .env file with key=value overrides."
    if subparsers is not None:
        p = subparsers.add_parser("patch", help=description, description=description)
    else:
        p = argparse.ArgumentParser(prog="envdiff patch", description=description)

    p.add_argument("env_file", help="Path to the .env file to patch")
    p.add_argument(
        "overrides",
        nargs="+",
        metavar="KEY=VALUE",
        help="Overrides in KEY=VALUE format. Use KEY= to remove a key.",
    )
    p.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        help="Output format (default: env)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print operations without writing output",
    )
    return p


def _parse_overrides(raw: list[str]) -> dict[str, Optional[str]]:
    result: dict[str, Optional[str]] = {}
    for item in raw:
        if "=" not in item:
            print(f"[error] Invalid override (missing '='): {item}", file=sys.stderr)
            sys.exit(2)
        key, _, value = item.partition("=")
        key = key.strip()
        if not key:
            print(f"[error] Override has empty key: {item}", file=sys.stderr)
            sys.exit(2)
        result[key] = value if value else None
    return result


def run_patch(args: argparse.Namespace) -> int:
    try:
        with open(args.env_file) as fh:
            raw = fh.read()
    except FileNotFoundError:
        print(f"[error] File not found: {args.env_file}", file=sys.stderr)
        return 2

    parsed = parse_env_string(raw, source=args.env_file)
    overrides = _parse_overrides(args.overrides)
    result = patch(parsed, overrides)

    if args.dry_run:
        print(f"[dry-run] {len(result.operations)} operation(s) would be applied:")
        for op in result.operations:
            action = "remove" if op.new_value is None else ("add" if op.old_value is None else "change")
            print(f"  {action}: {op.key}  {op.old_value!r} -> {op.new_value!r}")
        return 0

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.to_env_string())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_patch_parser()
    args = parser.parse_args()
    sys.exit(run_patch(args))


if __name__ == "__main__":  # pragma: no cover
    main()
