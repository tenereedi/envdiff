"""CLI commands for pinning env files and detecting drift."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.pinner import pin, check_drift, PinResult


def build_pin_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff pin",
        description="Pin env values or check for drift against a lockfile.",
    )
    sub = p.add_subparsers(dest="pin_cmd", required=True)

    create_p = sub.add_parser("create", help="Create a pin lockfile from an env file.")
    create_p.add_argument("env_file", help="Path to .env file")
    create_p.add_argument("--output", "-o", default=None, help="Output lockfile path (default: stdout)")

    check_p = sub.add_parser("check", help="Check current env against a pin lockfile.")
    check_p.add_argument("env_file", help="Path to current .env file")
    check_p.add_argument("lockfile", help="Path to existing pin lockfile (JSON)")
    check_p.add_argument("--format", choices=["text", "json"], default="text")

    return p


def run_pin(args: argparse.Namespace) -> int:
    if args.pin_cmd == "create":
        return _run_create(args)
    if args.pin_cmd == "check":
        return _run_check(args)
    return 2


def _run_create(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 2
    parsed = parse_env_string(env_path.read_text(), source=str(env_path))
    result = pin(parsed)
    output = result.to_json()
    if args.output:
        Path(args.output).write_text(output)
        print(f"Pinned {len(result.entries)} keys to {args.output}")
    else:
        print(output)
    return 0


def _run_check(args: argparse.Namespace) -> int:
    env_path = Path(args.env_file)
    lock_path = Path(args.lockfile)
    for p in (env_path, lock_path):
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2
    parsed = parse_env_string(env_path.read_text(), source=str(env_path))
    lock_data = json.loads(lock_path.read_text())
    from envdiff.pinner import PinnedEntry, PinResult
    entries = [
        PinnedEntry(key=e["key"], value=e.get("value", ""), is_secret=e["is_secret"], pinned_at=e["pinned_at"])
        for e in lock_data.get("entries", [])
    ]
    loaded_pin = PinResult(source=lock_data["source"], pinned_at=lock_data["pinned_at"], entries=entries)
    result = check_drift(parsed, loaded_pin)
    if args.format == "json":
        print(result.to_json())
    else:
        if result.has_drift:
            print(f"Drift detected in {len(result.drift_keys)} key(s):")
            for k in result.drift_keys:
                print(f"  ~ {k}")
        else:
            print("No drift detected.")
    return 1 if result.has_drift else 0
