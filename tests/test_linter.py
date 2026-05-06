"""Tests for envdiff.linter."""
import pytest

from envdiff.linter import lint, LintResult
from envdiff.parser import parse_env_string


@pytest.fixture
def clean_env():
    src = "APP_NAME=myapp\nDEBUG=false\nPORT=8080\n"
    return parse_env_string(src, source="clean.env")


@pytest.fixture
def dirty_env():
    src = (
        "app_name=myapp\n"        # L002 – lowercase
        "DEBUG=false\n"
        "DEBUG=true\n"            # L001 – duplicate
        "SECRET_TOKEN=\n"        # L003 – blank sensitive
        "PORT= 8080 \n"          # L004 – whitespace
    )
    return parse_env_string(src, source="dirty.env")


def test_clean_env_has_no_issues(clean_env):
    result = lint(clean_env)
    assert isinstance(result, LintResult)
    assert result.issues == []
    assert not result.has_errors
    assert not result.has_warnings


def test_dirty_env_has_issues(dirty_env):
    result = lint(dirty_env)
    assert len(result.issues) > 0


def test_duplicate_key_is_error(dirty_env):
    result = lint(dirty_env)
    codes = [i.code for i in result.issues]
    assert "L001" in codes
    l001 = next(i for i in result.issues if i.code == "L001")
    assert l001.severity == "error"
    assert l001.key == "DEBUG"


def test_lowercase_key_is_warning(dirty_env):
    result = lint(dirty_env)
    l002 = next((i for i in result.issues if i.code == "L002"), None)
    assert l002 is not None
    assert l002.severity == "warning"
    assert l002.key == "app_name"


def test_blank_sensitive_value_is_warning(dirty_env):
    result = lint(dirty_env)
    l003 = next((i for i in result.issues if i.code == "L003"), None)
    assert l003 is not None
    assert l003.severity == "warning"
    assert "SECRET_TOKEN" in l003.key


def test_whitespace_value_is_warning(dirty_env):
    result = lint(dirty_env)
    l004 = next((i for i in result.issues if i.code == "L004"), None)
    assert l004 is not None
    assert l004.severity == "warning"


def test_has_errors_true_when_error_present(dirty_env):
    result = lint(dirty_env)
    assert result.has_errors is True


def test_as_dict_structure(dirty_env):
    result = lint(dirty_env)
    d = result.as_dict()
    assert "issue_count" in d
    assert "has_errors" in d
    assert "has_warnings" in d
    assert isinstance(d["issues"], list)
    assert d["issue_count"] == len(result.issues)
