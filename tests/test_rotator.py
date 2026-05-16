"""Tests for envdiff.rotator."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.rotator import rotate, RotateResult, RotationCandidate


ENV_CLEAN = """
DATABASE_URL=postgres://user:pass@host/db
APP_ENV=production
PORT=8080
"""

ENV_STALE = """
OLD_API_KEY=abc123
LEGACY_SECRET=supersecret
APP_ENV=production
DEBUG_TOKEN=tok_xyz
"""

ENV_PLACEHOLDER = """
SECRET_KEY=changeme
API_TOKEN=placeholder
APP_NAME=myapp
"""

ENV_EMPTY_SECRET = """
SECRET_KEY=
APP_ENV=staging
"""


@pytest.fixture
def clean_parsed():
    return parse_env_string(ENV_CLEAN, source="clean.env")


@pytest.fixture
def stale_parsed():
    return parse_env_string(ENV_STALE, source="stale.env")


@pytest.fixture
def placeholder_parsed():
    return parse_env_string(ENV_PLACEHOLDER, source="placeholder.env")


@pytest.fixture
def empty_secret_parsed():
    return parse_env_string(ENV_EMPTY_SECRET, source="empty_secret.env")


def test_rotate_returns_rotate_result(clean_parsed):
    result = rotate(clean_parsed)
    assert isinstance(result, RotateResult)


def test_source_preserved(clean_parsed):
    result = rotate(clean_parsed)
    assert result.source == "clean.env"


def test_clean_env_has_no_candidates(clean_parsed):
    result = rotate(clean_parsed)
    assert not result.has_candidates
    assert result.candidate_keys == []


def test_stale_key_detected(stale_parsed):
    result = rotate(stale_parsed)
    assert result.has_candidates
    assert "OLD_API_KEY" in result.candidate_keys
    assert "LEGACY_SECRET" in result.candidate_keys
    assert "DEBUG_TOKEN" in result.candidate_keys


def test_clean_key_not_flagged(stale_parsed):
    result = rotate(stale_parsed)
    assert "APP_ENV" not in result.candidate_keys


def test_placeholder_value_detected(placeholder_parsed):
    result = rotate(placeholder_parsed)
    assert "SECRET_KEY" in result.candidate_keys
    assert "API_TOKEN" in result.candidate_keys


def test_empty_secret_detected(empty_secret_parsed):
    result = rotate(empty_secret_parsed)
    assert "SECRET_KEY" in result.candidate_keys


def test_candidate_has_suggested_placeholder(stale_parsed):
    result = rotate(stale_parsed)
    cand = next(c for c in result.candidates if c.key == "OLD_API_KEY")
    assert cand.suggested_placeholder == "REPLACE_WITH_OLD_API_KEY"


def test_secret_candidate_is_masked(stale_parsed):
    result = rotate(stale_parsed)
    cand = next(c for c in result.candidates if c.key == "LEGACY_SECRET")
    assert cand.masked is True
    d = cand.as_dict()
    assert d["current_value"] == "***"


def test_as_dict_structure(stale_parsed):
    result = rotate(stale_parsed)
    d = result.as_dict()
    assert "source" in d
    assert "candidates" in d
    assert "candidate_count" in d
    assert d["has_candidates"] is True
    assert d["candidate_count"] == len(result.candidates)


def test_rotated_at_is_iso_format(clean_parsed):
    result = rotate(clean_parsed)
    # Should not raise
    from datetime import datetime
    datetime.fromisoformat(result.rotated_at)
