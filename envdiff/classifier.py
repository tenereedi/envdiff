"""Classify .env entries by category based on key naming conventions."""

from dataclasses import dataclass, field
from typing import Dict, List
from envdiff.parser import ParseResult, EnvEntry


KEY_CATEGORIES: Dict[str, List[str]] = {
    "database": ["DB_", "DATABASE_", "POSTGRES_", "MYSQL_", "MONGO_", "REDIS_"],
    "auth": ["AUTH_", "JWT_", "OAUTH_", "TOKEN_", "SECRET_", "API_KEY", "PASSWORD", "PASSWD"],
    "network": ["HOST", "PORT", "URL", "ENDPOINT", "DOMAIN", "BASE_URL", "ALLOWED_HOSTS"],
    "logging": ["LOG_", "LOGGING_", "SENTRY_", "DEBUG", "VERBOSE"],
    "feature_flags": ["FEATURE_", "FLAG_", "ENABLE_", "DISABLE_"],
    "cloud": ["AWS_", "GCP_", "AZURE_", "S3_", "GCS_"],
    "email": ["EMAIL_", "SMTP_", "MAIL_", "SENDGRID_", "MAILGUN_"],
}


@dataclass
class ClassifiedEntry:
    key: str
    value: str
    category: str
    line_number: int

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "line_number": self.line_number,
        }


@dataclass
class ClassifyResult:
    source: str
    entries: List[ClassifiedEntry] = field(default_factory=list)
    categories: Dict[str, List[str]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "categories": {
                cat: keys for cat, keys in self.categories.items()
            },
            "entries": [e.as_dict() for e in self.entries],
        }


def _detect_category(key: str) -> str:
    upper = key.upper()
    for category, prefixes in KEY_CATEGORIES.items():
        for prefix in prefixes:
            if upper.startswith(prefix) or prefix in upper:
                return category
    return "general"


def classify(parsed: ParseResult) -> ClassifyResult:
    """Classify all entries in a ParseResult by key category."""
    result = ClassifyResult(source=parsed.source)

    for entry in parsed.entries:
        category = _detect_category(entry.key)
        classified = ClassifiedEntry(
            key=entry.key,
            value=entry.value,
            category=category,
            line_number=entry.line_number,
        )
        result.entries.append(classified)
        result.categories.setdefault(category, []).append(entry.key)

    return result
