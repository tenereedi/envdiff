"""Lint .env files for style and best-practice issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import ParseResult


@dataclass
class LintIssue:
    line: int
    key: str
    code: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def as_dict(self) -> dict:
        return {
            "line": self.line,
            "key": self.key,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def as_dict(self) -> dict:
        return {
            "issue_count": len(self.issues),
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "issues": [i.as_dict() for i in self.issues],
        }


_BLANK_VALUE_KEYS = frozenset({"SECRET", "PASSWORD", "TOKEN", "KEY", "PASS"})


def lint(parsed: ParseResult) -> LintResult:
    """Run all lint checks on a parsed .env file."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for entry in parsed.entries:
        k = entry.key
        ln = entry.line_number

        # L001 – duplicate key
        if k in seen_keys:
            result.issues.append(LintIssue(
                line=ln, key=k, code="L001",
                message=f"Duplicate key '{k}' (first seen on line {seen_keys[k]})",
                severity="error",
            ))
        else:
            seen_keys[k] = ln

        # L002 – lowercase key
        if k != k.upper():
            result.issues.append(LintIssue(
                line=ln, key=k, code="L002",
                message=f"Key '{k}' is not UPPER_CASE",
                severity="warning",
            ))

        # L003 – blank value for sensitive-looking key
        if entry.value == "" and any(part in k.upper() for part in _BLANK_VALUE_KEYS):
            result.issues.append(LintIssue(
                line=ln, key=k, code="L003",
                message=f"Sensitive key '{k}' has an empty value",
                severity="warning",
            ))

        # L004 – value contains unquoted whitespace
        if entry.value != entry.value.strip() and not (
            entry.value.startswith('"') or entry.value.startswith("'")
        ):
            result.issues.append(LintIssue(
                line=ln, key=k, code="L004",
                message=f"Value for '{k}' has leading/trailing whitespace",
                severity="warning",
            ))

    return result
