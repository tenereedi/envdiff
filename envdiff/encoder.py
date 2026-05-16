"""Encoder: serialize parsed env data to various output formats."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.parser import ParseResult, EnvEntry


@dataclass
class EncodedResult:
    source: str
    format: str
    encoded: str
    entry_count: int

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "format": self.format,
            "encoded": self.encoded,
            "entry_count": self.entry_count,
        }


def _entries_to_pairs(parsed: ParseResult) -> List[dict]:
    return [
        {"key": e.key, "value": e.value}
        for e in parsed.entries
        if e.key is not None
    ]


def encode(parsed: ParseResult, fmt: str = "json") -> EncodedResult:
    """Encode a ParseResult into the requested format.

    Supported formats: 'json', 'base64', 'csv'.
    """
    pairs = _entries_to_pairs(parsed)
    entry_count = len(pairs)

    if fmt == "json":
        encoded = json.dumps({p["key"]: p["value"] for p in pairs}, indent=2)
    elif fmt == "base64":
        raw = "\n".join(f"{p['key']}={p['value']}" for p in pairs)
        encoded = base64.b64encode(raw.encode()).decode()
    elif fmt == "csv":
        lines = ["key,value"] + [f"{p['key']},{p['value']}" for p in pairs]
        encoded = "\n".join(lines)
    else:
        raise ValueError(f"Unsupported encode format: {fmt!r}")

    return EncodedResult(
        source=parsed.source,
        format=fmt,
        encoded=encoded,
        entry_count=entry_count,
    )
