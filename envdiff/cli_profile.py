"""CLI sub-command: envdiff profile — check an env file against a profile."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.profiler import BUILTIN_PROFILES, check_profile


def build_profile_parser(sub) -> ArgumentParser:  # pragma: no cover
    p = sub.add_parser("profile", help="Check an .env file against a named profile")
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--profile",
        default="minimal",
        help=f"Profile name. Built-ins: {sorted(BUILTIN_PROFILES)} (default: minimal)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def run_profile(args: Namespace) -> int:
    path = Path(args.env_file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    parsed = parse_env_string(path.read_text(encoding="utf-8"), source=str(path))

    try:
        result = check_profile(parsed, args.profile)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    return 0 if result.is_compliant else 1


def _print_text(result) -> None:
    status = "COMPLIANT" if result.is_compliant else "NON-COMPLIANT"
    print(f"Profile : {result.profile_name}")
    print(f"Source  : {result.source}")
    print(f"Status  : {status}")
    if result.missing_keys:
        print("Missing keys:")
        for k in result.missing_keys:
            print(f"  - {k}")
    if result.extra_keys:
        print("Extra keys (not in profile):")
        for k in result.extra_keys:
            print(f"  + {k}")
    if result.is_compliant:
        print("All required keys present.")
