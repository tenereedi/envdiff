"""Edge-case tests for envdiff.promoter."""
import pytest

from envdiff.parser import parse_env_string
from envdiff.promoter import PromoteStatus, promote


def _parse(text, source="test.env"):
    return parse_env_string(text, source=source)


def test_empty_source_produces_no_entries():
    src = _parse("", source="empty.env")
    tgt = _parse("FOO=bar", source="tgt.env")
    result = promote(src, tgt)
    assert result.entries == []


def test_empty_target_all_keys_added():
    src = _parse("A=1\nB=2", source="src.env")
    tgt = _parse("", source="tgt.env")
    result = promote(src, tgt)
    assert all(e.status == PromoteStatus.ADDED for e in result.entries)
    assert result.promoted_count == 2


def test_identical_values_are_skipped():
    src = _parse("KEY=same", source="src.env")
    tgt = _parse("KEY=same", source="tgt.env")
    result = promote(src, tgt)
    assert result.entries[0].status == PromoteStatus.SKIPPED
    assert result.skipped_count == 1


def test_keys_not_in_source_are_ignored():
    src = _parse("A=1", source="src.env")
    tgt = _parse("B=2", source="tgt.env")
    result = promote(src, tgt, keys=["MISSING_KEY"])
    assert result.entries == []


def test_entry_as_dict_structure():
    src = _parse("X=hello", source="src.env")
    tgt = _parse("", source="tgt.env")
    result = promote(src, tgt)
    d = result.entries[0].as_dict()
    assert set(d.keys()) == {"key", "source_value", "target_value", "status"}


def test_target_value_none_when_key_not_in_target():
    src = _parse("NEW_KEY=val", source="src.env")
    tgt = _parse("", source="tgt.env")
    result = promote(src, tgt)
    assert result.entries[0].target_value is None


def test_overwrite_and_conflict_overwrite_takes_precedence():
    """When both overwrite and conflict_marker are True, overwrite wins (UPDATED, not CONFLICT)."""
    src = _parse("K=new", source="src.env")
    tgt = _parse("K=old", source="tgt.env")
    result = promote(src, tgt, overwrite=True, conflict_marker=True)
    assert result.entries[0].status == PromoteStatus.UPDATED
