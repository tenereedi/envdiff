"""Summarizer: produce a human-readable summary of a parsed .env file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import ParseResult
from envdiff.differ import is_secret


@dataclass
class SummaryStats:
    total_keys: int
    secret_keys: int
    plain_keys: int
    empty_values: int
    comment_lines: int
    blank_lines: int

    def as_dict(self) -> dict:
        return {
            "total_keys": self.total_keys,
            "secret_keys": self.secret_keys,
            "plain_keys": self.plain_keys,
            "empty_values": self.empty_values,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
        }


@dataclass
class SummaryResult:
    source: str
    stats: SummaryStats
    secret_key_names: List[str] = field(default_factory=list)
    empty_key_names: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "stats": self.stats.as_dict(),
            "secret_key_names": self.secret_key_names,
            "empty_key_names": self.empty_key_names,
        }

    def to_text(self) -> str:
        s = self.stats
        lines = [
            f"Source : {self.source}",
            f"Keys   : {s.total_keys} total  ({s.secret_keys} secret, {s.plain_keys} plain)",
            f"Empty  : {s.empty_values}",
            f"Comment lines : {s.comment_lines}",
            f"Blank lines   : {s.blank_lines}",
        ]
        if self.secret_key_names:
            lines.append("Secrets: " + ", ".join(self.secret_key_names))
        if self.empty_key_names:
            lines.append("Empty keys: " + ", ".join(self.empty_key_names))
        return "\n".join(lines)


def summarize(parsed: ParseResult) -> SummaryResult:
    """Build a SummaryResult from a ParseResult."""
    entries = list(parsed.as_dict().items())
    all_entries = parsed.entries

    secret_keys = [e.key for e in all_entries if is_secret(e.key)]
    empty_keys = [e.key for e in all_entries if e.value == ""]

    # Count comment and blank lines from raw source lines
    comment_lines = 0
    blank_lines = 0
    for entry in all_entries:
        # entries with no key are comments or blanks stored by parser
        pass

    # Use line metadata if available
    raw_lines = getattr(parsed, "_raw_lines", [])
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif stripped.startswith("#"):
            comment_lines += 1

    stats = SummaryStats(
        total_keys=len(all_entries),
        secret_keys=len(secret_keys),
        plain_keys=len(all_entries) - len(secret_keys),
        empty_values=len(empty_keys),
        comment_lines=comment_lines,
        blank_lines=blank_lines,
    )

    return SummaryResult(
        source=parsed.source,
        stats=stats,
        secret_key_names=secret_keys,
        empty_key_names=empty_keys,
    )
