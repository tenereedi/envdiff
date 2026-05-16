"""CLI entry point for the envdiff report command."""

from __future__ import annotations

import argparse
import sys

from envdiff.parser import parse_env_string
from envdiff.scorer import check_score
from envdiff.linter import lint
from envdiff.reporter import build_report


def build_report_parser(subparsers: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    kwargs: dict = dict(
        description="Generate a summary report for a .env file.",
    )
    if subparsers is not None:
        parser = subparsers.add_parser("report", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-score",
        action="store_true",
        help="Skip the score section",
    )
    parser.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip the lint section",
    )
    return parser


def run_report(args: argparse.Namespace) -> int:
    try:
        raw = open(args.file).read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2
    except PermissionError:
        print(f"error: permission denied: {args.file}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: could not read file: {args.file}: {exc}", file=sys.stderr)
        return 2

    parsed = parse_env_string(raw, source=args.file)

    score_result = None if args.no_score else check_score(parsed)
    lint_result = None if args.no_lint else lint(parsed)

    report = build_report(
        source=args.file,
        score=score_result,
        lint=lint_result,
    )

    if args.fmt == "json":
        print(report.to_json())
    else:
        _print_text(report)

    return 0 if report.overall_status == "ok" else 1


def _print_text(report) -> None:
    status_icon = {"ok": "✓", "warn": "!", "error": "✗"}
    print(f"Report for: {report.source}")
    print(f"Overall:    {status_icon.get(report.overall_status, '?')} {report.overall_status.upper()}")
    print()
    for section in report.sections:
        icon = status_icon.get(section.status, "?")
        print(f"  [{icon}] {section.name}: {section.summary}")
    print()


def main() -> None:
    parser = build_report_parser()
    args = parser.parse_args()
    sys.exit(run_report(args))


if __name__ == "__main__":
    main()
