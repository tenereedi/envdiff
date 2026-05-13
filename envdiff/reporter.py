"""Generate structured summary reports from multiple envdiff results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json

from envdiff.scorer import ScoreResult
from envdiff.comparator import CompareResult
from envdiff.linter import LintResult
from envdiff.profiler import ProfileResult


@dataclass
class ReportSection:
    name: str
    status: str  # "ok" | "warn" | "error"
    summary: str
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "details": self.details,
        }


@dataclass
class Report:
    source: str
    sections: list[ReportSection] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        statuses = {s.status for s in self.sections}
        if "error" in statuses:
            return "error"
        if "warn" in statuses:
            return "warn"
        return "ok"

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "overall_status": self.overall_status,
            "sections": [s.as_dict() for s in self.sections],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent)


def build_report(
    source: str,
    *,
    score: ScoreResult | None = None,
    compare: CompareResult | None = None,
    lint: LintResult | None = None,
    profile: ProfileResult | None = None,
) -> Report:
    """Assemble a Report from optional envdiff result objects."""
    report = Report(source=source)

    if score is not None:
        status = "ok" if score.grade in ("A", "B") else "warn" if score.grade == "C" else "error"
        report.sections.append(ReportSection(
            name="score",
            status=status,
            summary=f"Grade {score.grade} ({score.score}/100)",
            details=score.breakdown.as_dict() if hasattr(score.breakdown, "as_dict") else {},
        ))

    if lint is not None:
        status = "error" if lint.has_errors() else "warn" if lint.has_warnings() else "ok"
        report.sections.append(ReportSection(
            name="lint",
            status=status,
            summary=f"{len(lint.issues)} issue(s) found",
            details={"issues": [i.as_dict() for i in lint.issues]},
        ))

    if compare is not None:
        status = "warn" if compare.has_differences() else "ok"
        report.sections.append(ReportSection(
            name="compare",
            status=status,
            summary=f"{compare.stats.changed + compare.stats.added + compare.stats.removed} difference(s)",
            details=compare.stats.as_dict(),
        ))

    if profile is not None:
        status = "ok" if profile.is_compliant() else "error"
        report.sections.append(ReportSection(
            name="profile",
            status=status,
            summary="compliant" if profile.is_compliant() else f"{len(profile.missing_keys)} missing key(s)",
            details={"missing_keys": profile.missing_keys},
        ))

    return report
