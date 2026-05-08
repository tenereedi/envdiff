"""Tests for envdiff.profiler."""
from __future__ import annotations

import pytest

from envdiff.parser import parse_env_string
from envdiff.profiler import (
    BUILTIN_PROFILES,
    ProfileResult,
    check_profile,
)


FULL_WEB_ENV = """
APP_ENV=production
LOG_LEVEL=info
PORT=8080
DATABASE_URL=postgres://localhost/db
SECRET_KEY=supersecret
""".strip()

PARTIAL_ENV = """
APP_ENV=development
LOG_LEVEL=debug
""".strip()


@pytest.fixture
def full_web_parsed():
    return parse_env_string(FULL_WEB_ENV, source="full.env")


@pytest.fixture
def partial_parsed():
    return parse_env_string(PARTIAL_ENV, source="partial.env")


def test_compliant_web_profile(full_web_parsed):
    result = check_profile(full_web_parsed, "web")
    assert isinstance(result, ProfileResult)
    assert result.is_compliant is True
    assert result.missing_keys == []


def test_non_compliant_minimal_profile_missing_keys(partial_parsed):
    # partial only has APP_ENV and LOG_LEVEL — minimal requires both, so compliant
    result = check_profile(partial_parsed, "minimal")
    assert result.is_compliant is True


def test_non_compliant_web_profile_missing_keys(partial_parsed):
    result = check_profile(partial_parsed, "web")
    assert result.is_compliant is False
    assert "DATABASE_URL" in result.missing_keys
    assert "SECRET_KEY" in result.missing_keys
    assert "PORT" in result.missing_keys


def test_extra_keys_reported(full_web_parsed):
    # 'minimal' only requires APP_ENV and LOG_LEVEL
    result = check_profile(full_web_parsed, "minimal")
    assert "PORT" in result.extra_keys
    assert "DATABASE_URL" in result.extra_keys


def test_profile_result_as_dict(full_web_parsed):
    result = check_profile(full_web_parsed, "web")
    d = result.as_dict()
    assert d["profile"] == "web"
    assert d["compliant"] is True
    assert d["source"] == "full.env"
    assert isinstance(d["missing_keys"], list)
    assert isinstance(d["extra_keys"], list)


def test_unknown_profile_raises(full_web_parsed):
    with pytest.raises(ValueError, match="Unknown profile"):
        check_profile(full_web_parsed, "nonexistent")


def test_custom_profile(full_web_parsed):
    custom = {"myprofile": {"APP_ENV": "", "PORT": "", "CUSTOM_KEY": ""}}
    result = check_profile(full_web_parsed, "myprofile", custom_profiles=custom)
    assert "CUSTOM_KEY" in result.missing_keys
    assert result.is_compliant is False


def test_builtin_profiles_not_empty():
    assert len(BUILTIN_PROFILES) >= 3
    for name, keys in BUILTIN_PROFILES.items():
        assert isinstance(keys, dict)
        assert len(keys) > 0
