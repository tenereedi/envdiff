"""Environment profile comparison: compare an env file against a named profile baseline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import ParseResult
from envdiff.differ import DiffEntry, diff_envs


BUILTIN_PROFILES: Dict[str, Dict[str, str]] = {
    "minimal": {
        "APP_ENV": "",
        "LOG_LEVEL": "",
    },
    "web": {
        "APP_ENV": "",
        "LOG_LEVEL": "",
        "PORT": "",
        "DATABASE_URL": "",
        "SECRET_KEY": "",
    },
    "worker": {
        "APP_ENV": "",
        "LOG_LEVEL": "",
        "QUEUE_URL": "",
        "WORKER_CONCURRENCY": "",
    },
}


@dataclass
class ProfileResult:
    profile_name: str
    source: str
    missing_keys: List[str] = field(default_factory=list)
    extra_keys: List[str] = field(default_factory=list)
    diffs: List[DiffEntry] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return len(self.missing_keys) == 0

    def as_dict(self) -> dict:
        return {
            "profile": self.profile_name,
            "source": self.source,
            "compliant": self.is_compliant,
            "missing_keys": self.missing_keys,
            "extra_keys": self.extra_keys,
            "diff_count": len(self.diffs),
        }


def check_profile(
    parsed: ParseResult,
    profile_name: str,
    custom_profiles: Optional[Dict[str, Dict[str, str]]] = None,
) -> ProfileResult:
    """Check whether *parsed* satisfies the required keys of *profile_name*."""
    profiles = {**BUILTIN_PROFILES, **(custom_profiles or {})}
    if profile_name not in profiles:
        raise ValueError(
            f"Unknown profile '{profile_name}'. Available: {sorted(profiles)}"
        )

    required = profiles[profile_name]
    actual_keys = set(parsed.as_dict().keys())
    required_keys = set(required.keys())

    missing = sorted(required_keys - actual_keys)
    extra = sorted(actual_keys - required_keys)

    from envdiff.parser import ParseResult as PR, EnvEntry

    baseline_entries = [
        EnvEntry(key=k, raw_value=v, line_number=0)
        for k, v in required.items()
    ]
    baseline = PR(entries=baseline_entries, source=f"profile:{profile_name}")
    diffs = diff_envs(baseline, parsed)

    return ProfileResult(
        profile_name=profile_name,
        source=parsed.source,
        missing_keys=missing,
        extra_keys=extra,
        diffs=diffs,
    )
