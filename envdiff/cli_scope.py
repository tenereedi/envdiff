"""CLI entry-point for the *scope* subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.scoper import scope


def build_scope_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Filter .env entries by scope/environment prefix.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    if parent is not None:
        parser = parent.add_parser("scope", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff scope", **kwargs)

    parser.add_argument("file", help="Path to the .env file.")
    parser.add_argument("prefix", help="Scope prefix to filter by (e.g. PROD).")
    parser.add_argument(
        "--strip-prefix",
        action="store_true",
        default=False,
        help="Remove the matched prefix from output keys.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def run_scope(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    parsed = parse_env_string(path.read_text(), source=str(path))
    result = scope(parsed, args.prefix, strip_prefix=args.strip_prefix)

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        if not result.entries:
            print(f"No entries matched scope '{result.scope}'.")
        else:
            print(result.to_env_string())

    return 0


def main() -> None:  # pragma: no cover
    parser = build_scope_parser()
    args = parser.parse_args()
    sys.exit(run_scope(args))


if __name__ == "__main__":  # pragma: no cover
    main()
