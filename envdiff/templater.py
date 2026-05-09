"""Template generation from parsed .env files.

Generates a .env.template file by stripping secret values and
replacing them with placeholder hints.
"""

from dataclasses import dataclass, field
from typing import List

from envdiff.parser import ParseResult
from envdiff.differ import is_secret


PLACEHOLDER = "<YOUR_VALUE_HERE>"
SECRET_PLACEHOLDER = "<SECRET>"


@dataclass
class TemplateEntry:
    key: str
    placeholder: str
    is_secret: bool
    comment: str = ""

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "placeholder": self.placeholder,
            "is_secret": self.is_secret,
            "comment": self.comment,
        }


@dataclass
class TemplateResult:
    source: str
    entries: List[TemplateEntry] = field(default_factory=list)

    def to_env_string(self) -> str:
        """Render the template as a .env-style string."""
        lines = []
        for entry in self.entries:
            if entry.comment:
                lines.append(f"# {entry.comment}")
            lines.append(f"{entry.key}={entry.placeholder}")
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "entries": [e.as_dict() for e in self.entries],
        }


def generate_template(parsed: ParseResult) -> TemplateResult:
    """Generate a TemplateResult from a ParseResult.

    Secret keys receive a ``<SECRET>`` placeholder; all other keys
    receive a generic ``<YOUR_VALUE_HERE>`` placeholder.
    """
    result = TemplateResult(source=parsed.source)

    for entry in parsed.entries:
        secret = is_secret(entry.key)
        placeholder = SECRET_PLACEHOLDER if secret else PLACEHOLDER
        template_entry = TemplateEntry(
            key=entry.key,
            placeholder=placeholder,
            is_secret=secret,
        )
        result.entries.append(template_entry)

    return result
