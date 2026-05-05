"""Tests for envdiff.reconciler module."""

import pytest

from envdiff.differ import diff
from envdiff.parser import parse_env_string
from envdiff.reconciler import ReconcileAction, reconcile


ENV_A = """
APP_NAME=myapp
DEBUG=true
DATABASE_URL=postgres://localhost/dev
OLD_KEY=old_value
""".strip()

ENV_B = """
APP_NAME=myapp
DEBUG=false
DATABASE_URL=postgres://prod-host/prod
NEW_KEY=new_value
""".strip()


@pytest.fixture
def parsed_a():
    return parse_env_string(ENV_A)


@pytest.fixture
def parsed_b():
    return parse_env_string(ENV_B)


@pytest.fixture
def diffs(parsed_a, parsed_b):
    return diff(parsed_a, parsed_b)


@pytest.fixture
def result_prefer_b(parsed_a, parsed_b, diffs):
    return reconcile(parsed_a, parsed_b, diffs, prefer="b")


@pytest.fixture
def result_prefer_a(parsed_a, parsed_b, diffs):
    return reconcile(parsed_a, parsed_b, diffs, prefer="a")


def test_reconcile_keeps_unchanged(result_prefer_b):
    d = result_prefer_b.as_dict()
    assert d["APP_NAME"] == "myapp"


def test_reconcile_prefer_b_uses_b_value(result_prefer_b):
    d = result_prefer_b.as_dict()
    assert d["DEBUG"] == "false"
    assert d["DATABASE_URL"] == "postgres://prod-host/prod"


def test_reconcile_prefer_a_uses_a_value(result_prefer_a):
    d = result_prefer_a.as_dict()
    assert d["DEBUG"] == "true"
    assert d["DATABASE_URL"] == "postgres://localhost/dev"


def test_reconcile_includes_added_key(result_prefer_b):
    assert "NEW_KEY" in result_prefer_b.as_dict()
    assert result_prefer_b.as_dict()["NEW_KEY"] == "new_value"


def test_reconcile_skips_removed_key(result_prefer_b):
    assert "OLD_KEY" not in result_prefer_b.as_dict()
    assert "OLD_KEY" in result_prefer_b.skipped_keys


def test_reconcile_actions_logged(result_prefer_b):
    assert len(result_prefer_b.actions) > 0
    action_keys = [a.key for a in result_prefer_b.actions]
    assert "APP_NAME" in action_keys
    assert "OLD_KEY" in action_keys


def test_to_env_string_format(result_prefer_b):
    output = result_prefer_b.to_env_string()
    assert "=" in output
    assert "APP_NAME=myapp" in output
    assert output.endswith("\n")


def test_skipped_action_has_comment(result_prefer_b):
    skip_actions = [a for a in result_prefer_b.actions if a.action == "skip"]
    assert len(skip_actions) == 1
    assert skip_actions[0].comment is not None
