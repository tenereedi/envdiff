"""CLI subcommand: compare two .env files."""

import argparse
import json
import sys
from envdiff.parser import parse_env_string
from envdiff.comparator import compare_envs
from envdiff.formatter import format_diff, OutputFormat


def build_compare_parser(subparsers) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "compare",
        help="Compare two .env files and show a structured diff with stats.",
    )
    p.add_argument("file_a", help="First .env file (base)")
    p.add_argument("file_b", help="Second .env file (target)")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Disable secret masking in output",
    )
    return p


def run_compare(args: argparse.Namespace) -> int:
    """Execute the compare subcommand. Returns exit code."""
    try:
        with open(args.file_a) as f:
            text_a = f.read()
        with open(args.file_b) as f:
            text_b = f.read()
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    parsed_a = parse_env_string(text_a, source=args.file_a)
    parsed_b = parse_env_string(text_b, source=args.file_b)
    result = compare_envs(parsed_a, parsed_b)

    fmt = OutputFormat.JSON if args.output_format == "json" else OutputFormat.TEXT
    mask = not args.no_mask

    if fmt == OutputFormat.JSON:
        out = result.as_dict()
        # Rebuild entries with masking applied via formatter
        out["entries"] = json.loads(
            format_diff(result.entries, OutputFormat.JSON, mask_secrets=mask)
        )
        print(json.dumps(out, indent=2))
    else:
        stats = result.stats
        print(f"Comparing: {result.source_a}  vs  {result.source_b}")
        print(
            f"Stats: {stats.total_a} keys in A, {stats.total_b} keys in B, "
            f"{stats.changed} changed, {stats.only_in_a} only-in-A, "
            f"{stats.only_in_b} only-in-B, {stats.unchanged} unchanged"
        )
        print()
        print(format_diff(result.entries, OutputFormat.TEXT, mask_secrets=mask))

    return 1 if result.has_differences() else 0
