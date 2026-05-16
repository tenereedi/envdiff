"""CLI subcommand: encode an .env file to json, base64, or csv."""
from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_string
from envdiff.encoder import encode


def build_encode_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Encode a .env file to json, base64, or csv."
    if subparsers is not None:
        parser = subparsers.add_parser("encode", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff encode", description=description)

    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--format",
        choices=["json", "base64", "csv"],
        default="json",
        dest="fmt",
        help="Output encoding format (default: json)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write output to this file instead of stdout",
    )
    return parser


def run_encode(ns: argparse.Namespace) -> int:
    try:
        with open(ns.file, "r") as fh:
            raw = fh.read()
    except FileNotFoundError:
        print(f"Error: file not found: {ns.file}", file=sys.stderr)
        return 2

    parsed = parse_env_string(raw, source=ns.file)
    result = encode(parsed, fmt=ns.fmt)

    if ns.output:
        try:
            with open(ns.output, "w") as fh:
                fh.write(result.encoded)
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 2
        print(f"Encoded {result.entry_count} entries to {ns.output}")
    else:
        print(result.encoded)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_encode_parser()
    ns = parser.parse_args()
    sys.exit(run_encode(ns))
