"""Tests for envdiff.validator module."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.validator import validate, ValidationResult


@pytest.fixture
def valid_env():
    return parse_env_string(
        "APP_NAME=myapp\n"
        "DEBUG=false\n"
        "PORT=8080\n"
        "SECRET_KEY=abc123\n"
    )


@pytest.fixture
def invalid_env():
    return parse_env_string(
        "APP_NAME=myapp\n"
        "123INVALID=bad_key\n"
        "APP_NAME=duplicate\n"
        "REF_VAR=${OTHER_VAR}\n"
    )


def test_valid_env_has_no_issues(valid_env):
    result = validate(valid_env)
    assert isinstance(result, ValidationResult)
    assert not result.has_errors
    assert not result.has_warnings
    assert len(result.issues) == 0


def test_valid_env_as_dict(valid_env):
    d = validate(valid_env).as_dict()
    assert d["valid"] is True
    assert d["error_count"] == 0
    assert d["warning_count"] == 0
    assert d["issues"] == []


def test_invalid_key_name_is_error(invalid_env):
    result = validate(invalid_env)
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("123INVALID" in i.message for i in errors)


def test_duplicate_key_is_warning(invalid_env):
    result = validate(invalid_env)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("APP_NAME" in i.message and "Duplicate" in i.message for i in warnings)


def test_unexpanded_variable_is_warning(invalid_env):
    result = validate(invalid_env)
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("REF_VAR" in i.message and "unexpanded" in i.message for i in warnings)


def test_has_errors_flag(invalid_env):
    result = validate(invalid_env)
    assert result.has_errors is True


def test_has_warnings_flag(invalid_env):
    result = validate(invalid_env)
    assert result.has_warnings is True


def test_issue_line_numbers_present(invalid_env):
    result = validate(invalid_env)
    for issue in result.issues:
        assert issue.line is not None
        assert issue.line > 0


def test_as_dict_counts(invalid_env):
    d = validate(invalid_env).as_dict()
    assert d["valid"] is False
    assert d["error_count"] >= 1
    assert d["warning_count"] >= 1
