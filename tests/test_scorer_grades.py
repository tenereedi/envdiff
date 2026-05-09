"""Parametrized grade boundary tests for envdiff.scorer."""
import pytest
from envdiff.scorer import ScoreBreakdown, ScoreResult
from envdiff.linter import LintResult
from envdiff.validator import ValidationResult


def _make_result(score: float) -> ScoreResult:
    """Build a minimal ScoreResult with a forced total for grade testing."""
    # Distribute score across breakdown buckets proportionally
    lint_s = min(40.0, score * 0.4)
    val_s = min(40.0, score * 0.4)
    prof_s = min(20.0, score * 0.2)
    breakdown = ScoreBreakdown(
        lint_score=round(lint_s, 1),
        validation_score=round(val_s, 1),
        profile_score=round(prof_s, 1),
    )
    return ScoreResult(
        source="test.env",
        breakdown=breakdown,
        lint=LintResult(source="test.env", issues=[]),
        validation=ValidationResult(source="test.env", issues=[]),
        profile=None,
    )


@pytest.mark.parametrize("score,expected_grade", [
    (95.0, "A"),
    (90.0, "A"),
    (89.9, "B"),
    (75.0, "B"),
    (74.9, "C"),
    (60.0, "C"),
    (59.9, "D"),
    (40.0, "D"),
    (39.9, "F"),
    (0.0,  "F"),
])
def test_grade_boundaries(score, expected_grade):
    result = _make_result(score)
    # Override total via breakdown so grade() reads correct value
    # Manually patch breakdown to hit exact boundary
    result.breakdown.lint_score = round(score * 0.4, 1)
    result.breakdown.validation_score = round(score * 0.4, 1)
    result.breakdown.profile_score = round(score * 0.2, 1)
    assert result.grade == expected_grade


def test_breakdown_total_is_sum():
    b = ScoreBreakdown(lint_score=35.0, validation_score=38.0, profile_score=18.0)
    assert b.total == pytest.approx(91.0)


def test_as_dict_breakdown_sums_to_score():
    from envdiff.parser import parse_env_string
    from envdiff.scorer import score_env
    parsed = parse_env_string("KEY=value\nOTHER=123", source="t.env")
    result = score_env(parsed)
    d = result.as_dict()
    bd = d["breakdown"]
    expected = round(bd["lint"] + bd["validation"] + bd["profile"], 1)
    assert d["score"] == pytest.approx(expected)
