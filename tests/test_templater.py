"""Tests for envdiff.templater."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.templater import (
    generate_template,
    TemplateResult,
    TemplateEntry,
    PLACEHOLDER,
    SECRET_PLACEHOLDER,
)


ENV_STRING = """\
APP_NAME=myapp
DATABASE_URL=postgres://localhost/db
SECRET_KEY=supersecret
API_KEY=abc123
DEBUG=true
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_STRING, source=".env")


@pytest.fixture
def template(parsed):
    return generate_template(parsed)


def test_returns_template_result(template):
    assert isinstance(template, TemplateResult)


def test_source_preserved(template):
    assert template.source == ".env"


def test_entry_count(template, parsed):
    assert len(template.entries) == len(parsed.entries)


def test_entries_are_template_entry(template):
    for entry in template.entries:
        assert isinstance(entry, TemplateEntry)


def test_secret_key_gets_secret_placeholder(template):
    secret_entries = [e for e in template.entries if e.is_secret]
    assert len(secret_entries) > 0
    for entry in secret_entries:
        assert entry.placeholder == SECRET_PLACEHOLDER


def test_non_secret_key_gets_generic_placeholder(template):
    plain_entries = [e for e in template.entries if not e.is_secret]
    assert len(plain_entries) > 0
    for entry in plain_entries:
        assert entry.placeholder == PLACEHOLDER


def test_secret_key_flag_set_for_secret(template):
    keys = {e.key: e for e in template.entries}
    assert keys["SECRET_KEY"].is_secret is True
    assert keys["API_KEY"].is_secret is True


def test_non_secret_key_flag_not_set(template):
    keys = {e.key: e for e in template.entries}
    assert keys["APP_NAME"].is_secret is False
    assert keys["DEBUG"].is_secret is False


def test_to_env_string_contains_all_keys(template):
    output = template.to_env_string()
    for entry in template.entries:
        assert entry.key in output


def test_to_env_string_no_real_values(template, parsed):
    output = template.to_env_string()
    real_values = [e.value for e in parsed.entries if e.value]
    for val in real_values:
        assert val not in output


def test_as_dict_structure(template):
    d = template.as_dict()
    assert "source" in d
    assert "entries" in d
    assert isinstance(d["entries"], list)
    assert all("key" in e and "placeholder" in e for e in d["entries"])
