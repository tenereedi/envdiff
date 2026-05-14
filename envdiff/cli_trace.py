"""CLI entry-point for the trace subcommand."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.parser import parse_env_string
from envdiff.tracer import trace


def build_trace_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Trace key-level changes between two .env files."
    if subparsers is not None:
        p = subparsers.add_parser("trace", help=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff trace", description=desc)
    p.add_argument("file_a", help="Base .env file")
    p.add_argument("file_b", help="Target .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    return p


def run_trace(ns: argparse.Namespace) -> int:
    try:
        with open(ns.file_a) as f:
            content_a = f.read()
        with open(ns.file_b) as f:
            content_b = f.read()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parsed_a = parse_env_string(content_a, source=ns.file_a)
    parsed_b = parse_env_string(content_b, source=ns.file_b)
    result = trace(parsed_a, parsed_b)

    if ns.fmt == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        if not result.has_changes:
            print("No changes detected.")
        else:
            print(f"Changes between {result.source_a} and {result.source_b}:")
            for ev in result.events:
                old = ev.old_value if ev.old_value is not None else "<absent>"
                new = ev.new_value if ev.new_value is not None else "<absent>"
                print(f"  {ev.key}: {old!r} -> {new!r}")

    return 1 if result.has_changes else 0


def main() -> None:  # pragma: no cover
    parser = build_trace_parser()
    ns = parser.parse_args()
    sys.exit(run_trace(ns))


if __name__ == "__main__":  # pragma: no cover
    main()
