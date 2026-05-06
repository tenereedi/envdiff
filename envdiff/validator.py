"""Validation utilities for .env file entries and keys."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.parser import ParseResult

# Valid env key pattern: starts with letter or underscore, followed by word chars
_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')

# Warn if value looks like it contains an unexpanded variable reference
_UNEXPANDED_RE = re.compile(r'\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*')


@dataclass
class ValidationIssue:
    line: Optional[int]
    key: Optional[str]
    severity: str  # 'error' | 'warning'
    message: str

    def as_dict(self) -> dict:
        return {
            "line": self.line,
            "key": self.key,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def as_dict(self) -> dict:
        return {
            "valid": not self.has_errors,
            "error_count": sum(1 for i in self.issues if i.severity == "error"),
            "warning_count": sum(1 for i in self.issues if i.severity == "warning"),
            "issues": [i.as_dict() for i in self.issues],
        }


def validate(parsed: ParseResult) -> ValidationResult:
    """Validate a parsed .env file and return a ValidationResult."""
    result = ValidationResult()
    seen_keys: dict[str, int] = {}

    for entry in parsed.entries:
        # Duplicate key check
        if entry.key in seen_keys:
            result.issues.append(ValidationIssue(
                line=entry.line,
                key=entry.key,
                severity="warning",
                message=(
                    f"Duplicate key '{entry.key}' "
                    f"(first seen on line {seen_keys[entry.key]})"
                ),
            ))
        else:
            seen_keys[entry.key] = entry.line

        # Invalid key name
        if not _KEY_RE.match(entry.key):
            result.issues.append(ValidationIssue(
                line=entry.line,
                key=entry.key,
                severity="error",
                message=f"Invalid key name '{entry.key}': must match [A-Za-z_][A-Za-z0-9_]*",
            ))

        # Unexpanded variable references in value
        if entry.value and _UNEXPANDED_RE.search(entry.value):
            result.issues.append(ValidationIssue(
                line=entry.line,
                key=entry.key,
                severity="warning",
                message=f"Value for '{entry.key}' appears to contain an unexpanded variable reference",
            ))

    return result
