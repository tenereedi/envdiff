"""CLI handler for the normalize subcommand."""

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.normalizer import normalize


def build_normalize_parser(subparsers=None) -> argparse.ArgumentParser:
    desc = "Normalize a .env file: deduplicate keys and optionally sort."
    if subparsers is not None:
        parser = subparsers.add_parser("normalize", help=desc)
    else:
        parser = argparse.ArgumentParser(prog="envdiff normalize", description=desc)

    parser.add_argument("file", help="Path to the .env file to normalize.")
    parser.add_argument(
        "--no-sort",
        action="store_true",
        default=False,
        help="Preserve original key order instead of sorting alphabetically.",
    )
    parser.add_argument(
        "--output",
        choices=["env", "json"],
        default="env",
        help="Output format (default: env).",
    )
    parser.add_argument(
        "--write",
        metavar="DEST",
        default=None,
        help="Write normalized output to DEST instead of stdout.",
    )
    return parser


def run_normalize(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    raw = path.read_text(encoding="utf-8")
    parsed = parse_env_string(raw, source=str(path))
    sort_keys = not args.no_sort
    result = normalize(parsed, sort_keys=sort_keys)

    if args.output == "json":
        output = json.dumps(result.as_dict(), indent=2)
    else:
        output = result.to_env_string()

    if args.write:
        dest = Path(args.write)
        dest.write_text(output, encoding="utf-8")
        removed = len(result.removed_duplicates)
        print(
            f"Normalized {len(result.entries)} entries "
            f"({removed} duplicate(s) removed) -> {dest}"
        )
    else:
        print(output)

    return 1 if result.removed_duplicates else 0


def main() -> None:  # pragma: no cover
    parser = build_normalize_parser()
    args = parser.parse_args()
    sys.exit(run_normalize(args))


if __name__ == "__main__":  # pragma: no cover
    main()
