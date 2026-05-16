"""CLI command: envdiff split — split an .env file into multiple buckets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.splitter import split


def build_split_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "split",
        help="Split an .env file into named buckets by key pattern.",
    )
    p.add_argument("file", help="Path to the .env file to split.")
    p.add_argument(
        "--pattern",
        dest="patterns",
        action="append",
        default=[],
        metavar="NAME:GLOB",
        help="Bucket pattern in NAME:GLOB format (repeatable). E.g. db:DB_*",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--outdir",
        default=None,
        metavar="DIR",
        help="If set, write each bucket to DIR/<name>.env instead of stdout.",
    )
    return p


def run_split(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    parsed = parse_env_string(path.read_text(), source=str(path))
    result = split(parsed, patterns=args.patterns or [])

    if args.outdir:
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True)
        for bucket in result.buckets:
            out_path = outdir / f"{bucket.name}.env"
            out_path.write_text(bucket.to_env_string())
            print(f"wrote {len(bucket.entries)} entries -> {out_path}")
        return 0

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
        return 0

    _print_text(result)
    return 0


def _print_text(result) -> None:
    for bucket in result.buckets:
        keys = [e.key for e in bucket.entries if e.key]
        tag = f"({len(keys)} keys)"
        print(f"[{bucket.name}] {tag}")
        for key in keys:
            print(f"  {key}")


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="envdiff-split")
    sub = parser.add_subparsers(dest="command")
    build_split_parser(sub)
    args = parser.parse_args()
    sys.exit(run_split(args))
