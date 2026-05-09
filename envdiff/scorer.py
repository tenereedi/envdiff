"""Env file health scorer — produces a numeric score based on lint, validation, and profile compliance."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from envdiff.parser import ParseResult
from envdiff.linter import lint, LintResult
from envdiff.validator import validate, ValidationResult
from envdiff.profiler import check_profile, ProfileResult


@dataclass
class ScoreBreakdown:
    lint_score: float        # 0-40
    validation_score: float  # 0-40
    profile_score: float     # 0-20

    @property
    def total(self) -> float:
        return round(self.lint_score + self.validation_score + self.profile_score, 1)


@dataclass
class ScoreResult:
    source: str
    breakdown: ScoreBreakdown
    lint: LintResult
    validation: ValidationResult
    profile: Optional[ProfileResult]

    @property
    def score(self) -> float:
        return self.breakdown.total

    @property
    def grade(self) -> str:
        s = self.score
        if s >= 90:
            return "A"
        if s >= 75:
            return "B"
        if s >= 60:
            return "C"
        if s >= 40:
            return "D"
        return "F"

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "score": self.score,
            "grade": self.grade,
            "breakdown": {
                "lint": self.breakdown.lint_score,
                "validation": self.breakdown.validation_score,
                "profile": self.breakdown.profile_score,
            },
            "lint_errors": len([i for i in self.lint.issues if i.severity == "error"]),
            "lint_warnings": len([i for i in self.lint.issues if i.severity == "warning"]),
            "validation_errors": len([i for i in self.validation.issues if i.severity == "error"]),
            "profile_compliant": self.profile.is_compliant if self.profile else None,
        }


def score_env(parsed: ParseResult, profile_name: Optional[str] = None) -> ScoreResult:
    """Score a parsed env file and return a ScoreResult."""
    lint_result = lint(parsed)
    validation_result = validate(parsed)
    profile_result = check_profile(parsed, profile_name) if profile_name else None

    lint_errors = sum(1 for i in lint_result.issues if i.severity == "error")
    lint_warnings = sum(1 for i in lint_result.issues if i.severity == "warning")
    lint_score = max(0.0, 40.0 - lint_errors * 10.0 - lint_warnings * 2.0)

    val_errors = sum(1 for i in validation_result.issues if i.severity == "error")
    val_warnings = sum(1 for i in validation_result.issues if i.severity == "warning")
    validation_score = max(0.0, 40.0 - val_errors * 10.0 - val_warnings * 2.0)

    if profile_result is None:
        profile_score = 20.0
    elif profile_result.is_compliant:
        profile_score = 20.0
    else:
        missing = len(profile_result.missing_keys)
        profile_score = max(0.0, 20.0 - missing * 4.0)

    breakdown = ScoreBreakdown(
        lint_score=round(lint_score, 1),
        validation_score=round(validation_score, 1),
        profile_score=round(profile_score, 1),
    )
    return ScoreResult(
        source=parsed.source,
        breakdown=breakdown,
        lint=lint_result,
        validation=validation_result,
        profile=profile_result,
    )
