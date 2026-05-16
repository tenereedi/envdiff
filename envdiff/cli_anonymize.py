"""CLI sub-command: anonymize — replace secrets with deterministic tokens."""
from __future__ import annotations

import argparse
import json
import sys

from .parser import parse_env_string
from .anonymizer import anonymize


def build_anonymize_parser(sub=None) -> argparse.ArgumentParser:
    desc = "Replace secret values with deterministic tokens for safe sharing."
    if sub is not None:
        p = sub.add_parser("anonymize", help=desc, description=desc)
    else:
        p = argparse.ArgumentParser(prog="envdiff anonymize", description=desc)
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--salt",
        default="",
        help="Optional salt to vary token generation (default: empty)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--show-map",
        action="store_true",
        help="Include the token map in JSON output",
    )
    return p


def run_anonymize(args: argparse.Namespace) -> int:
    try:
        with open(args.file, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parsed = parse_env_string(raw, source=args.file)
    result = anonymize(parsed, salt=args.salt)

    if args.format == "json":
        data = result.as_dict()
        if not args.show_map:
            data.pop("token_map", None)
        print(json.dumps(data, indent=2))
        return 0

    # text: emit the anonymized .env content
    print(result.to_env_string(), end="")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_anonymize_parser()
    args = parser.parse_args()
    sys.exit(run_anonymize(args))


if __name__ == "__main__":  # pragma: no cover
    main()
