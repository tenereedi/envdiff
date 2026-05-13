"""Tests for envdiff.reporter — build_report and Report."""

from __future__ import annotations

import pytest

from envdiff.parser import parse_env_string
from envdiff.scorer import check_score
from envdiff.linter import lint
from envdiff.reporter import build_report, Report, ReportSection


CLEAN_ENV = """APP_NAME=myapp
DATABASE_URL=postgres://localhost/db
SECRET_KEY=supersecret
DEBUG=false
"""

DIRTY_ENV = """1INVALID=bad
DUPE=first
DUPE=second
=nokey
"""


@pytest.fixture
def clean_parsed():
    return parse_env_string(CLEAN_ENV, source="clean.env")


@pytest.fixture
def dirty_parsed():
    return parse_env_string(DIRTY_ENV, source="dirty.env")


def test_build_report_returns_report(clean_parsed):
    result = build_report("clean.env")
    assert isinstance(result, Report)


def test_source_preserved(clean_parsed):
    result = build_report("clean.env")
    assert result.source == "clean.env"


def test_empty_report_is_ok(clean_parsed):
    result = build_report("clean.env")
    assert result.overall_status == "ok"
    assert result.sections == []


def test_report_with_score_section(clean_parsed):
    score = check_score(clean_parsed)
    result = build_report("clean.env", score=score)
    names = [s.name for s in result.sections]
    assert "score" in names


def test_report_with_lint_section(dirty_parsed):
    lint_result = lint(dirty_parsed)
    result = build_report("dirty.env", lint=lint_result)
    names = [s.name for s in result.sections]
    assert "lint" in names


def test_dirty_lint_status_is_error(dirty_parsed):
    lint_result = lint(dirty_parsed)
    result = build_report("dirty.env", lint=lint_result)
    lint_section = next(s for s in result.sections if s.name == "lint")
    assert lint_section.status == "error"


def test_clean_lint_status_is_ok(clean_parsed):
    lint_result = lint(clean_parsed)
    result = build_report("clean.env", lint=lint_result)
    lint_section = next(s for s in result.sections if s.name == "lint")
    assert lint_section.status == "ok"


def test_overall_status_error_when_any_section_errors(dirty_parsed):
    lint_result = lint(dirty_parsed)
    result = build_report("dirty.env", lint=lint_result)
    assert result.overall_status == "error"


def test_as_dict_has_expected_keys(clean_parsed):
    score = check_score(clean_parsed)
    result = build_report("clean.env", score=score)
    d = result.as_dict()
    assert "source" in d
    assert "overall_status" in d
    assert "sections" in d


def test_to_json_is_valid_json(clean_parsed):
    import json
    score = check_score(clean_parsed)
    result = build_report("clean.env", score=score)
    parsed = json.loads(result.to_json())
    assert parsed["source"] == "clean.env"


def test_section_as_dict_structure():
    section = ReportSection(name="lint", status="ok", summary="no issues", details={"issues": []})
    d = section.as_dict()
    assert d["name"] == "lint"
    assert d["status"] == "ok"
    assert d["summary"] == "no issues"
    assert "details" in d
