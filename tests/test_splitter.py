"""Tests for envdiff.splitter."""

import pytest

from envdiff.parser import parse_env_string
from envdiff.splitter import split, SplitResult, SplitBucket


ENV_CONTENT = """\
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
AWS_ACCESS_KEY=AKID
AWS_SECRET=secret
APP_ENV=production
APP_DEBUG=false
UNKNOWN=whatever
"""


@pytest.fixture
def parsed():
    return parse_env_string(ENV_CONTENT, source="test.env")


@pytest.fixture
def result(parsed):
    return split(
        parsed,
        patterns=["db:DB_*", "aws:AWS_*", "app:APP_*"],
    )


def test_returns_split_result(result):
    assert isinstance(result, SplitResult)


def test_source_preserved(result):
    assert result.source == "test.env"


def test_bucket_names_match_patterns(result):
    names = result.bucket_names()
    assert "db" in names
    assert "aws" in names
    assert "app" in names


def test_db_bucket_has_correct_keys(result):
    bucket = result.get_bucket("db")
    assert bucket is not None
    keys = [e.key for e in bucket.entries]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "DB_NAME" in keys


def test_aws_bucket_has_correct_keys(result):
    bucket = result.get_bucket("aws")
    assert bucket is not None
    keys = [e.key for e in bucket.entries]
    assert "AWS_ACCESS_KEY" in keys
    assert "AWS_SECRET" in keys


def test_unmatched_keys_go_to_other(result):
    bucket = result.get_bucket("other")
    assert bucket is not None
    keys = [e.key for e in bucket.entries]
    assert "UNKNOWN" in keys


def test_no_patterns_puts_all_in_other(parsed):
    result = split(parsed)
    assert result.bucket_names() == ["other"]
    other = result.get_bucket("other")
    assert len(other.entries) == len([e for e in parsed.entries if e.key])


def test_to_env_string_contains_keys(result):
    bucket = result.get_bucket("db")
    env_str = bucket.to_env_string()
    assert "DB_HOST" in env_str
    assert "DB_PORT" in env_str


def test_as_dict_structure(result):
    d = result.as_dict()
    assert "source" in d
    assert "bucket_count" in d
    assert "buckets" in d
    assert d["bucket_count"] == len(result.buckets)


def test_bucket_as_dict_has_keys(result):
    bucket = result.get_bucket("db")
    d = bucket.as_dict()
    assert d["name"] == "db"
    assert "entry_count" in d
    assert "keys" in d


def test_get_bucket_none_for_missing(result):
    assert result.get_bucket("nonexistent") is None


def test_all_keys_assigned_exactly_once(parsed, result):
    all_input_keys = {e.key for e in parsed.entries if e.key}
    all_output_keys = set()
    for bucket in result.buckets:
        for entry in bucket.entries:
            if entry.key:
                all_output_keys.add(entry.key)
    assert all_input_keys == all_output_keys
