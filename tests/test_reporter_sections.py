"""Additional tests for ReportSection status logic and edge cases."""

from __future__ import annotations

import pytest

from envdiff.parser import parse_env_string
from envdiff.comparator import compare
from envdiff.profiler import check_profile
from envdiff.reporter import build_report, ReportSection


ENV_A = "DB_URL=postgres://a\nSECRET=abc\nAPP=foo\n"
ENV_B = "DB_URL=postgres://b\nSECRET=xyz\nNEW_KEY=bar\n"


@pytest.fixture
def parsed_a():
    return parse_env_string(ENV_A, source="a.env")


@pytest.fixture
def parsed_b():
    return parse_env_string(ENV_B, source="b.env")


def test_compare_section_added(parsed_a, parsed_b):
    compare_result = compare(parsed_a, parsed_b)
    report = build_report("a.env", compare=compare_result)
    section = next(s for s in report.sections if s.name == "compare")
    assert section is not None


def test_compare_section_status_warn_when_differences(parsed_a, parsed_b):
    compare_result = compare(parsed_a, parsed_b)
    report = build_report("a.env", compare=compare_result)
    section = next(s for s in report.sections if s.name == "compare")
    assert section.status == "warn"


def test_compare_section_ok_when_identical(parsed_a):
    compare_result = compare(parsed_a, parsed_a)
    report = build_report("a.env", compare=compare_result)
    section = next(s for s in report.sections if s.name == "compare")
    assert section.status == "ok"


def test_profile_section_error_when_missing_keys(parsed_a):
    profile_result = check_profile(parsed_a, required_keys=["MISSING_KEY", "ALSO_MISSING"])
    report = build_report("a.env", profile=profile_result)
    section = next(s for s in report.sections if s.name == "profile")
    assert section.status == "error"


def test_profile_section_ok_when_compliant(parsed_a):
    profile_result = check_profile(parsed_a, required_keys=["DB_URL", "SECRET"])
    report = build_report("a.env", profile=profile_result)
    section = next(s for s in report.sections if s.name == "profile")
    assert section.status == "ok"


def test_multiple_sections_error_dominates(parsed_a, parsed_b):
    compare_result = compare(parsed_a, parsed_b)
    profile_result = check_profile(parsed_a, required_keys=["NONEXISTENT"])
    report = build_report("a.env", compare=compare_result, profile=profile_result)
    assert report.overall_status == "error"


def test_section_summary_contains_count(parsed_a):
    profile_result = check_profile(parsed_a, required_keys=["MISSING_ONE", "MISSING_TWO"])
    report = build_report("a.env", profile=profile_result)
    section = next(s for s in report.sections if s.name == "profile")
    assert "2" in section.summary


def test_all_sections_combined(parsed_a, parsed_b):
    from envdiff.scorer import check_score
    from envdiff.linter import lint
    score = check_score(parsed_a)
    lint_result = lint(parsed_a)
    compare_result = compare(parsed_a, parsed_b)
    profile_result = check_profile(parsed_a, required_keys=["DB_URL"])
    report = build_report(
        "a.env",
        score=score,
        lint=lint_result,
        compare=compare_result,
        profile=profile_result,
    )
    section_names = [s.name for s in report.sections]
    assert set(section_names) == {"score", "lint", "compare", "profile"}
