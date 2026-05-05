"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff import get_version
from envdiff.differ import diff_envs
from envdiff.formatter import OutputFormat, format_diff
from envdiff.parser import parse_env_string


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff and reconcile .env files across environments.",
    )
    p.add_argument("file_a", metavar="FILE_A", help="Base .env file")
    p.add_argument("file_b", metavar="FILE_B", help="Target .env file")
    p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text)",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Enable ANSI color output (text format only)",
    )
    p.add_argument(
        "--only-diff",
        action="store_true",
        default=False,
        help="Suppress unchanged keys from output",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    return p


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    path_a = Path(args.file_a)
    path_b = Path(args.file_b)

    for path in (path_a, path_b):
        if not path.exists():
            print(f"envdiff: error: file not found: {path}", file=sys.stderr)
            return 2

    result_a = parse_env_string(path_a.read_text(encoding="utf-8"))
    result_b = parse_env_string(path_b.read_text(encoding="utf-8"))

    entries = diff_envs(result_a.as_dict(), result_b.as_dict())

    if args.only_diff:
        from envdiff.differ import DiffStatus
        entries = [e for e in entries if e.status != DiffStatus.UNCHANGED]

    output = format_diff(
        entries,
        fmt=OutputFormat(args.format),
        color=args.color,
    )

    print(output)
    has_diff = any(True for e in entries)
    return 1 if has_diff else 0


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
