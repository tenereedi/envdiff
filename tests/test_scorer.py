"""Tests for envdiff.scorer."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.scorer import score_env, ScoreResult, ScoreBreakdown


CLEAN_ENV = """
DB_HOST=localhost
DB_PORT=5432
APP_SECRET=supersecret
DEBUG=false
""".strip()

DIRTY_ENV = """
1INVALID=bad
DB_HOST=localhost
DB_HOST=duplicate
 =nokey
""".strip()


@pytest.fixture
def clean_parsed():
    return parse_env_string(CLEAN_ENV, source="clean.env")


@pytest.fixture
def dirty_parsed():
    return parse_env_string(DIRTY_ENV, source="dirty.env")


def test_score_returns_score_result(clean_parsed):
    result = score_env(clean_parsed)
    assert isinstance(result, ScoreResult)


def test_clean_env_high_score(clean_parsed):
    result = score_env(clean_parsed)
    assert result.score >= 75


def test_dirty_env_lower_score(dirty_parsed):
    result = score_env(dirty_parsed)
    assert result.score < 75


def test_grade_a_for_perfect(clean_parsed):
    result = score_env(clean_parsed)
    assert result.grade in ("A", "B")


def test_grade_f_for_terrible(dirty_parsed):
    result = score_env(dirty_parsed)
    assert result.grade in ("D", "F", "C")


def test_source_preserved(clean_parsed):
    result = score_env(clean_parsed)
    assert result.source == "clean.env"


def test_breakdown_fields(clean_parsed):
    result = score_env(clean_parsed)
    b = result.breakdown
    assert isinstance(b, ScoreBreakdown)
    assert 0 <= b.lint_score <= 40
    assert 0 <= b.validation_score <= 40
    assert 0 <= b.profile_score <= 20


def test_as_dict_keys(clean_parsed):
    result = score_env(clean_parsed)
    d = result.as_dict()
    assert "score" in d
    assert "grade" in d
    assert "breakdown" in d
    assert "source" in d


def test_no_profile_gives_full_profile_score(clean_parsed):
    result = score_env(clean_parsed, profile_name=None)
    assert result.breakdown.profile_score == 20.0
    assert result.profile is None


def test_with_known_profile(clean_parsed):
    result = score_env(clean_parsed, profile_name="minimal")
    assert result.profile is not None
    assert isinstance(result.breakdown.profile_score, float)
