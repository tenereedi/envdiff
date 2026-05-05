"""Parser for .env files — handles reading and tokenizing key-value pairs."""

import re
from dataclasses import dataclass, field
from typing import Optional


# Matches: KEY=VALUE, KEY="VALUE", KEY='VALUE', export KEY=VALUE
_ENV_LINE_RE = re.compile(
    r'^(?:export\s+)?'
    r'(?P<key>[A-Za-z_][A-Za-z0-9_]*)'
    r'\s*=\s*'
    r'(?P<value>.*)$'
)


@dataclass
class EnvEntry:
    key: str
    raw_value: str
    line_number: int
    comment: Optional[str] = None

    @property
    def value(self) -> str:
        """Return unquoted value."""
        v = self.raw_value.strip()
        if (v.startswith('"') and v.endswith('"')) or \
           (v.startswith("'") and v.endswith("'")):
            return v[1:-1]
        return v


@dataclass
class ParseResult:
    entries: list[EnvEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, str]:
        return {e.key: e.value for e in self.entries}


def parse_env_string(content: str) -> ParseResult:
    """Parse the text content of a .env file into a ParseResult."""
    result = ParseResult()
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        # Inline comment stripping (outside quotes)
        comment = None
        match = _ENV_LINE_RE.match(line)
        if not match:
            result.errors.append(f"Line {lineno}: cannot parse '{raw_line}'")
            continue
        key = match.group('key')
        value_part = match.group('value').strip()
        # Detect inline comment only for unquoted values
        if not (value_part.startswith('"') or value_part.startswith("'")):
            comment_idx = value_part.find(' #')
            if comment_idx != -1:
                comment = value_part[comment_idx + 2:]
                value_part = value_part[:comment_idx].strip()
        result.entries.append(
            EnvEntry(key=key, raw_value=value_part, line_number=lineno, comment=comment)
        )
    return result


def parse_env_file(path: str) -> ParseResult:
    """Read a .env file from disk and parse it."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            content = fh.read()
    except OSError as exc:
        result = ParseResult()
        result.errors.append(f"Cannot read file '{path}': {exc}")
        return result
    return parse_env_string(content)
