"""Tests for envdiff.encoder."""
import base64
import json
import pytest

from envdiff.parser import parse_env_string
from envdiff.encoder import encode, EncodedResult


RAW = """APP_ENV=production
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=abc123
"""


@pytest.fixture
def parsed():
    return parse_env_string(RAW, source="test.env")


def test_encode_returns_encoded_result(parsed):
    result = encode(parsed, fmt="json")
    assert isinstance(result, EncodedResult)


def test_source_preserved(parsed):
    result = encode(parsed, fmt="json")
    assert result.source == "test.env"


def test_entry_count(parsed):
    result = encode(parsed, fmt="json")
    assert result.entry_count == 4


def test_json_format_is_valid(parsed):
    result = encode(parsed, fmt="json")
    assert result.format == "json"
    data = json.loads(result.encoded)
    assert data["APP_ENV"] == "production"
    assert data["DB_PORT"] == "5432"


def test_base64_format_decodes_correctly(parsed):
    result = encode(parsed, fmt="base64")
    assert result.format == "base64"
    decoded = base64.b64decode(result.encoded).decode()
    assert "APP_ENV=production" in decoded
    assert "SECRET_KEY=abc123" in decoded


def test_csv_format_has_header(parsed):
    result = encode(parsed, fmt="csv")
    assert result.format == "csv"
    lines = result.encoded.splitlines()
    assert lines[0] == "key,value"
    assert any("APP_ENV,production" in l for l in lines)


def test_csv_entry_count_matches(parsed):
    result = encode(parsed, fmt="csv")
    # header + 4 entries
    assert len(result.encoded.splitlines()) == 5


def test_unsupported_format_raises(parsed):
    with pytest.raises(ValueError, match="Unsupported encode format"):
        encode(parsed, fmt="xml")


def test_as_dict_keys(parsed):
    result = encode(parsed, fmt="json")
    d = result.as_dict()
    assert set(d.keys()) == {"source", "format", "encoded", "entry_count"}
