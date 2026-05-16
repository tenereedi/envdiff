"""CLI commands for freeze and verify operations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .parser import parse_env_string
from .freezer import freeze, verify, FreezeResult


def build_freeze_parser(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("file", help=".env file to freeze or verify")
    sub.add_argument(
        "--verify",
        metavar="FREEZE_JSON",
        help="Path to a freeze JSON file to verify against",
    )
    sub.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def _print_text(result: FreezeResult, *, verifying: bool) -> None:
    verb = "Verified" if verifying else "Frozen"
    print(f"{verb}: {result.source}  [{result.frozen_at}]")
    print(f"Manifest: {result.manifest_checksum}")
    if verifying:
        if result.is_intact:
            print("Status: INTACT")
        else:
            print(f"Status: TAMPERED — {len(result.tampered_keys)} key(s) changed")
            for k in result.tampered_keys:
                print(f"  ! {k}")
    else:
        print(f"Entries frozen: {len(result.entries)}")


def run_freeze(args: argparse.Namespace) -> int:
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 2

    parsed = parse_env_string(env_path.read_text(), source=str(env_path))

    verifying = bool(getattr(args, "verify", None))

    if verifying:
        freeze_path = Path(args.verify)
        if not freeze_path.exists():
            print(f"Error: freeze file not found: {args.verify}", file=sys.stderr)
            return 2
        raw = json.loads(freeze_path.read_text())
        from .freezer import FrozenEntry
        entries = [
            FrozenEntry(key=e["key"], value=e["value"], checksum=e["checksum"])
            for e in raw["entries"]
        ]
        from .freezer import FreezeResult as FR
        frozen = FR(
            source=raw["source"],
            frozen_at=raw["frozen_at"],
            entries=entries,
            manifest_checksum=raw["manifest_checksum"],
        )
        result = verify(parsed, frozen)
        exit_code = 0 if result.is_intact else 1
    else:
        result = freeze(parsed)
        exit_code = 0

    if args.output == "json":
        print(result.to_json())
    else:
        _print_text(result, verifying=verifying)

    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze or verify a .env file")
    build_freeze_parser(parser)
    args = parser.parse_args()
    sys.exit(run_freeze(args))
