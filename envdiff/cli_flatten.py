"""CLI entry point for the flatten command."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.parser import parse_env_string
from envdiff.flattener import flatten
from envdiff.formatter import OutputFormat


def build_flatten_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="envdiff flatten",
        description="Strip a common prefix from all matching env keys.",
    )
    parser = parent.add_parser("flatten", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to .env file")
    parser.add_argument(
        "--prefix",
        default=None,
        metavar="PREFIX",
        help="Prefix to strip from matching keys (e.g. APP_)",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="output_format",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print rename statistics instead of env output",
    )
    return parser


def run_flatten(args: argparse.Namespace) -> int:
    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    parsed = parse_env_string(content, source=args.file)
    result = flatten(parsed, strip_prefix=args.prefix)

    if args.output_format == OutputFormat.JSON.value:
        print(json.dumps(result.as_dict(), indent=2))
        return 0

    if args.stats:
        print(f"source      : {result.source}")
        print(f"strip_prefix: {result.strip_prefix or '(none)'}")
        print(f"total keys  : {len(result.entries)}")
        print(f"renamed     : {result.renamed_count}")
        return 0

    print(result.to_env_string())
    return 0


def main() -> None:
    parser = build_flatten_parser()
    args = parser.parse_args()
    sys.exit(run_flatten(args))


if __name__ == "__main__":
    main()
