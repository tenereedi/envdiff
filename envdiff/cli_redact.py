"""CLI sub-command: redact secrets from a .env file."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.parser import parse_env_string
from envdiff.redactor import redact, DEFAULT_MASK


def build_redact_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Mask secrets in a .env file before sharing or logging."
    if subparsers is not None:
        parser = subparsers.add_parser("redact", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff redact", description=description)

    parser.add_argument("file", help="Path to the .env file to redact.")
    parser.add_argument(
        "--mask",
        default=DEFAULT_MASK,
        help=f"Replacement string for secrets (default: {DEFAULT_MASK!r}).",
    )
    parser.add_argument(
        "--extra-keys",
        nargs="*",
        metavar="KEY",
        default=[],
        help="Additional keys to always redact.",
    )
    parser.add_argument(
        "--keep-keys",
        nargs="*",
        metavar="KEY",
        default=[],
        help="Keys to never redact even if they look like secrets.",
    )
    parser.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        help="Output format (default: env).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    return parser


def run_redact(args: argparse.Namespace) -> int:
    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parsed = parse_env_string(raw, source=args.file)
    result = redact(
        parsed,
        mask=args.mask,
        extra_keys=args.extra_keys or [],
        keep_keys=args.keep_keys or [],
    )

    if args.format == "json":
        output = json.dumps(result.as_dict(), indent=2)
    else:
        output = result.to_env_string()

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(output + "\n")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(
            f"Redacted {result.redacted_count} secret(s) → {args.output}",
            file=sys.stderr,
        )
    else:
        print(output)

    return 0
