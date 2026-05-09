"""CLI subcommand: envdiff score — show health score for a .env file."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_string
from envdiff.scorer import score_env


def build_score_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Score the health of a .env file (0-100)."
    if subparsers is not None:
        parser = subparsers.add_parser("score", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff score", description=description)

    parser.add_argument("file", help="Path to .env file")
    parser.add_argument(
        "--profile",
        default=None,
        metavar="NAME",
        help="Optional profile name to include compliance in score",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        metavar="N",
        help="Exit with code 1 if score is below N",
    )
    return parser


def run_score(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    content = path.read_text(encoding="utf-8")
    parsed = parse_env_string(content, source=str(path))
    result = score_env(parsed, profile_name=getattr(args, "profile", None))

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_text(result)

    if result.score < args.min_score:
        return 1
    return 0


def _print_text(result) -> None:
    print(f"File   : {result.source}")
    print(f"Score  : {result.score} / 100  [{result.grade}]")
    print(f"  Lint        : {result.breakdown.lint_score} / 40")
    print(f"  Validation  : {result.breakdown.validation_score} / 40")
    print(f"  Profile     : {result.breakdown.profile_score} / 20", end="")
    if result.profile:
        status = "compliant" if result.profile.is_compliant else "non-compliant"
        print(f"  ({result.profile.profile_name}: {status})", end="")
    print()
    if result.lint.issues:
        print(f"  Lint issues : {len(result.lint.issues)}")
    if result.validation.issues:
        print(f"  Val issues  : {len(result.validation.issues)}")


if __name__ == "__main__":
    _parser = build_score_parser()
    _args = _parser.parse_args()
    sys.exit(run_score(_args))
