"""Tests for envdiff.transformer."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.transformer import TransformResult, transform


ENV_TEXT = """\
DB_HOST=localhost
DB_PASSWORD=Secret123
APP_ENV=Production
DEBUG=  true  
# a comment
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_TEXT, source="test.env")


@pytest.fixture
def result(parsed):
    return transform(parsed, {"APP_ENV": "lowercase", "DB_HOST": "uppercase"})


def test_transform_returns_transform_result(result):
    assert isinstance(result, TransformResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_lowercase_applied(result):
    entry = next(e for e in result.entries if e.key == "APP_ENV")
    assert entry.value == "production"


def test_uppercase_applied(result):
    entry = next(e for e in result.entries if e.key == "DB_HOST")
    assert entry.value == "LOCALHOST"


def test_untransformed_key_unchanged(result):
    entry = next(e for e in result.entries if e.key == "DB_PASSWORD")
    assert entry.value == "Secret123"


def test_changed_count(result):
    assert result.changed_count == 2


def test_operations_record_original_and_new(result):
    op = next(o for o in result.operations if o.key == "APP_ENV")
    assert op.original_value == "Production"
    assert op.new_value == "production"
    assert op.transform_name == "lowercase"


def test_strip_transform(parsed):
    r = transform(parsed, {"DEBUG": "strip"})
    entry = next(e for e in r.entries if e.key == "DEBUG")
    assert entry.value == "true"


def test_strip_quotes_transform():
    raw = 'KEY="quoted value"\n'
    p = parse_env_string(raw, source="q.env")
    r = transform(p, {"KEY": "strip_quotes"})
    entry = next(e for e in r.entries if e.key == "KEY")
    assert entry.value == "quoted value"


def test_unknown_transform_raises(parsed):
    with pytest.raises(ValueError, match="Unknown transform"):
        transform(parsed, {"DB_HOST": "nonexistent"})


def test_custom_transform(parsed):
    r = transform(
        parsed,
        {"DB_HOST": "reverse"},
        custom_transforms={"reverse": lambda v: v[::-1]},
    )
    entry = next(e for e in r.entries if e.key == "DB_HOST")
    assert entry.value == "tsohlacol"


def test_to_env_string_contains_transformed_value(result):
    env_str = result.to_env_string()
    assert "APP_ENV=production" in env_str
    assert "DB_HOST=LOCALHOST" in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "changed_count" in d
    assert "operations" in d
    assert "entries" in d
    assert d["changed_count"] == 2
