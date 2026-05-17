"""CLI command: envdiff promote — promote keys from one .env to another."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.promoter import promote


def build_promote_parser(sub: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    desc = "Promote .env keys from SOURCE into TARGET environment."
    if sub is not None:
        parser = sub.add_parser("promote", help=desc, description=desc)
    else:
        parser = argparse.ArgumentParser(prog="envdiff promote", description=desc)

    parser.add_argument("source", help="Source .env file (values to promote from)")
    parser.add_argument("target", help="Target .env file (values to promote into)")
    parser.add_argument(
        "--keys", nargs="+", metavar="KEY",
        help="Specific keys to promote (default: all source keys)",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite existing target values that differ",
    )
    parser.add_argument(
        "--conflict", action="store_true",
        help="Mark differing existing keys as conflicts instead of skipping",
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text",
        dest="output_format",
    )
    parser.add_argument("--output", "-o", metavar="FILE", help="Write result .env to file")
    return parser


def _print_text(result, file=sys.stdout) -> None:
    status_icons = {"added": "+", "updated": "~", "skipped": "=", "conflict": "!"}
    for entry in result.entries:
        icon = status_icons.get(entry.status, "?")
        print(f"  [{icon}] {entry.key}", file=file)
    print(file=file)
    print(f"Promoted : {result.promoted_count}", file=file)
    print(f"Conflicts: {result.conflict_count}", file=file)
    print(f"Skipped  : {result.skipped_count}", file=file)


def run_promote(args: argparse.Namespace) -> int:
    src_path = Path(args.source)
    tgt_path = Path(args.target)

    if not src_path.exists():
        print(f"error: source file not found: {src_path}", file=sys.stderr)
        return 2
    if not tgt_path.exists():
        print(f"error: target file not found: {tgt_path}", file=sys.stderr)
        return 2

    src_parsed = parse_env_string(src_path.read_text(), source=str(src_path))
    tgt_parsed = parse_env_string(tgt_path.read_text(), source=str(tgt_path))

    result = promote(
        src_parsed,
        tgt_parsed,
        keys=args.keys,
        overwrite=args.overwrite,
        conflict_marker=args.conflict,
    )

    if args.output_format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if args.output:
        Path(args.output).write_text(result.to_env_string())

    return 1 if result.conflict_count > 0 else 0


def main() -> None:  # pragma: no cover
    parser = build_promote_parser()
    sys.exit(run_promote(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
