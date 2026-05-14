"""Tag .env entries with custom labels for grouping and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import ParseResult


# Built-in auto-tag rules: (tag_name, callable that accepts key -> bool)
_AUTO_RULES: List[tuple] = [
    ("secret", lambda k: any(w in k.upper() for w in ("SECRET", "PASSWORD", "TOKEN", "KEY", "PASS", "PRIVATE"))),
    ("url", lambda k: any(w in k.upper() for w in ("URL", "URI", "HOST", "ENDPOINT"))),
    ("database", lambda k: any(w in k.upper() for w in ("DB", "DATABASE", "POSTGRES", "MYSQL", "REDIS", "MONGO"))),
    ("feature_flag", lambda k: k.upper().startswith(("FEATURE_", "FLAG_", "ENABLE_", "DISABLE_"))),
    ("port", lambda k: "PORT" in k.upper()),
    ("debug", lambda k: "DEBUG" in k.upper() or "LOG_LEVEL" in k.upper()),
]


@dataclass
class TaggedEntry:
    key: str
    value: str
    tags: List[str]
    line_number: Optional[int] = None

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "tags": sorted(self.tags),
            "line_number": self.line_number,
        }


@dataclass
class TagResult:
    source: str
    entries: List[TaggedEntry]
    tag_index: Dict[str, List[str]] = field(default_factory=dict)  # tag -> [keys]

    def keys_for_tag(self, tag: str) -> List[str]:
        return self.tag_index.get(tag, [])

    def tags_for_key(self, key: str) -> List[str]:
        for entry in self.entries:
            if entry.key == key:
                return entry.tags
        return []

    def all_tags(self) -> List[str]:
        return sorted(self.tag_index.keys())

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "entries": [e.as_dict() for e in self.entries],
            "tag_index": {t: sorted(keys) for t, keys in sorted(self.tag_index.items())},
        }


def tag_env(parsed: ParseResult, extra_tags: Optional[Dict[str, List[str]]] = None) -> TagResult:
    """Tag all entries in a ParseResult using built-in rules and optional extra tags.

    Args:
        parsed: A ParseResult from parse_env_string.
        extra_tags: Optional mapping of key -> list of custom tag strings.

    Returns:
        A TagResult with per-entry tags and a tag index.
    """
    extra_tags = extra_tags or {}
    tagged_entries: List[TaggedEntry] = []
    tag_index: Dict[str, List[str]] = {}

    for entry in parsed.entries:
        tags: List[str] = []
        for tag_name, rule in _AUTO_RULES:
            if rule(entry.key):
                tags.append(tag_name)
        for custom_tag in extra_tags.get(entry.key, []):
            if custom_tag not in tags:
                tags.append(custom_tag)

        tagged = TaggedEntry(
            key=entry.key,
            value=entry.value,
            tags=sorted(tags),
            line_number=entry.line_number,
        )
        tagged_entries.append(tagged)

        for t in tagged.tags:
            tag_index.setdefault(t, []).append(entry.key)

    return TagResult(source=parsed.source, entries=tagged_entries, tag_index=tag_index)
