"""CLI entry point for the transform command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.formatter import OutputFormat
from envdiff.parser import parse_env_string
from envdiff.transformer import transform


def build_transform_parser(parent: argparse._SubParsersAction = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff transform",
        description="Apply value transforms to keys in a .env file.",
    )
    parser = parent.add_parser("transform", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    parser.add_argument("file", help="Path to the .env file")
    parser.add_argument(
        "--set",
        metavar="KEY=TRANSFORM",
        action="append",
        dest="assignments",
        default=[],
        help="Apply TRANSFORM to KEY (e.g. APP_ENV=lowercase). Repeatable.",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="fmt",
    )
    parser.add_argument("--output", "-o", metavar="FILE", help="Write result to FILE")
    return parser


def _parse_assignments(assignments: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in assignments:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"Invalid --set value: '{item}' (expected KEY=TRANSFORM)")
        key, _, tname = item.partition("=")
        result[key.strip()] = tname.strip()
    return result


def run_transform(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    try:
        transforms = _parse_assignments(args.assignments)
    except argparse.ArgumentTypeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    parsed = parse_env_string(text, source=str(path))

    try:
        result = transform(parsed, transforms)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fmt = args.fmt
    if fmt == OutputFormat.JSON.value:
        output = json.dumps(result.as_dict(), indent=2)
    else:
        output = result.to_env_string()

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)

    return 0 if result.changed_count >= 0 else 1


def main() -> None:  # pragma: no cover
    parser = build_transform_parser()
    args = parser.parse_args()
    sys.exit(run_transform(args))


if __name__ == "__main__":  # pragma: no cover
    main()
