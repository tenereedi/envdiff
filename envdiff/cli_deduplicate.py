"""CLI entry point for the deduplicate subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.deduplicator import deduplicate


def build_deduplicate_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "deduplicate",
        help="Remove duplicate keys from a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--keep",
        choices=["first", "last"],
        default="last",
        help="Which occurrence to keep when duplicates are found (default: last)",
    )
    p.add_argument(
        "--format",
        dest="output_format",
        choices=["text", "json", "env"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--output",
        "-o",
        dest="output_file",
        default=None,
        help="Write output to file instead of stdout",
    )
    return p


def run_deduplicate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    content = path.read_text(encoding="utf-8")
    parsed = parse_env_string(content, source=str(path))
    result = deduplicate(parsed, keep=args.keep)

    fmt = args.output_format

    if fmt == "json":
        output = json.dumps(result.as_dict(), indent=2)
    elif fmt == "env":
        output = result.to_env_string()
    else:
        lines = [f"Source : {result.source}"]
        lines.append(f"Entries: {len(result.entries)}")
        if result.has_duplicates:
            lines.append(f"Duplicates found ({len(result.duplicates)} key(s)):")
            for group in result.duplicates:
                lnums = ", ".join(str(n) for n in group.as_dict()["line_numbers"])
                lines.append(f"  {group.key}  (lines: {lnums}, kept: {args.keep})")
        else:
            lines.append("No duplicate keys found.")
        output = "\n".join(lines)

    if args.output_file:
        Path(args.output_file).write_text(output, encoding="utf-8")
    else:
        print(output)

    return 1 if result.has_duplicates else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="envdiff-deduplicate")
    sub = parser.add_subparsers(dest="command")
    build_deduplicate_parser(sub)
    args = parser.parse_args()
    if args.command is None:
        # called directly without subcommand wrapper
        p2 = argparse.ArgumentParser(prog="envdiff deduplicate")
        p2.add_argument("file")
        p2.add_argument("--keep", choices=["first", "last"], default="last")
        p2.add_argument("--format", dest="output_format",
                        choices=["text", "json", "env"], default="text")
        p2.add_argument("--output", "-o", dest="output_file", default=None)
        args = p2.parse_args()
    sys.exit(run_deduplicate(args))


if __name__ == "__main__":  # pragma: no cover
    main()
