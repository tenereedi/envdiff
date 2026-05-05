"""Tests for envdiff.parser module."""

import pytest
from envdiff.parser import parse_env_string, EnvEntry


SIMPLE_ENV = """
# This is a comment
DB_HOST=localhost
DB_PORT=5432
APP_SECRET="my_secret_value"
DEBUG='true'
export PATH_PREFIX=/usr/local
"""


def test_basic_parsing():
    result = parse_env_string(SIMPLE_ENV)
    assert not result.errors
    d = result.as_dict()
    assert d['DB_HOST'] == 'localhost'
    assert d['DB_PORT'] == '5432'
    assert d['APP_SECRET'] == 'my_secret_value'
    assert d['DEBUG'] == 'true'
    assert d['PATH_PREFIX'] == '/usr/local'


def test_entry_count():
    result = parse_env_string(SIMPLE_ENV)
    assert len(result.entries) == 5


def test_line_numbers():
    result = parse_env_string(SIMPLE_ENV)
    keys = {e.key: e.line_number for e in result.entries}
    assert keys['DB_HOST'] == 3
    assert keys['DB_PORT'] == 4


def test_inline_comment_stripped():
    env = "TIMEOUT=30 # seconds\n"
    result = parse_env_string(env)
    assert result.entries[0].value == '30'
    assert result.entries[0].comment == 'seconds'


def test_quoted_value_with_hash_preserved():
    env = 'TOKEN="abc#def"\n'
    result = parse_env_string(env)
    assert result.entries[0].value == 'abc#def'


def test_empty_value():
    result = parse_env_string('EMPTY=\n')
    assert result.as_dict()['EMPTY'] == ''


def test_invalid_line_recorded():
    result = parse_env_string('THIS IS INVALID\n')
    assert len(result.errors) == 1
    assert 'Line 1' in result.errors[0]


def test_as_dict_last_wins():
    env = "KEY=first\nKEY=second\n"
    result = parse_env_string(env)
    assert result.as_dict()['KEY'] == 'second'


def test_blank_lines_and_comments_ignored():
    env = "\n# comment\n   \nFOO=bar\n"
    result = parse_env_string(env)
    assert len(result.entries) == 1
