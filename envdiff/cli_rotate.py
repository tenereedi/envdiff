"""CLI entry point for the rotate subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.rotator import rotate


def build_rotate_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Detect stale or placeholder keys that should be rotated."
    if subparsers is not None:
        parser = subparsers.add_parser("rotate", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envdiff rotate", description=desc)
    parser.add_argument("file", help="Path to the .env file to inspect")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-candidates",
        action="store_true",
        default=False,
        help="Exit with code 1 if rotation candidates are found",
    )
    return parser


def _print_text(result, file=sys.stdout) -> None:
    if not result.has_candidates:
        print("No rotation candidates found.", file=file)
        return
    print(f"Rotation candidates in {result.source}:", file=file)
    for cand in result.candidates:
        masked_val = "***" if cand.masked else cand.current_value
        print(
            f"  [{cand.key}]  value={masked_val!r}  reason={cand.reason}",
            file=file,
        )
        print(f"    suggested placeholder: {cand.suggested_placeholder}", file=file)


def run_rotate(args: argparse.Namespace) -> int:
    env_path = Path(args.file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 2

    raw = env_path.read_text(encoding="utf-8")
    parsed = parse_env_string(raw, source=str(env_path))
    result = rotate(parsed)

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.fail_on_candidates and result.has_candidates:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_rotate_parser()
    args = parser.parse_args()
    sys.exit(run_rotate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
