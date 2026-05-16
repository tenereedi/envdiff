"""Edge-case tests for envdiff.renamer."""
import pytest
from envdiff.parser import parse_env_string
from envdiff.renamer import rename


def _parsed(text: str, source: str = "edge.env"):
    return parse_env_string(text, source=source)


def test_empty_mapping_returns_unchanged_entries():
    parsed = _parsed("FOO=bar\nBAZ=qux\n")
    result = rename(parsed, {})
    assert result.renamed_count == 0
    keys = [e.key for e in result.entries]
    assert keys == ["FOO", "BAZ"]


def test_rename_to_same_name_is_no_op():
    """Renaming FOO -> FOO should succeed and count as one operation."""
    parsed = _parsed("FOO=bar\n")
    result = rename(parsed, {"FOO": "FOO"})
    # same-name rename: new_key == old_key, so it's not a conflict
    assert result.renamed_count == 1
    assert result.entries[0].key == "FOO"


def test_multiple_renames_all_applied():
    parsed = _parsed("A=1\nB=2\nC=3\n")
    result = rename(parsed, {"A": "X", "B": "Y", "C": "Z"})
    assert result.renamed_count == 3
    keys = [e.key for e in result.entries]
    assert keys == ["X", "Y", "Z"]


def test_order_of_entries_preserved():
    parsed = _parsed("ALPHA=1\nBETA=2\nGAMMA=3\n")
    result = rename(parsed, {"BETA": "DELTA"})
    keys = [e.key for e in result.entries]
    assert keys.index("ALPHA") < keys.index("DELTA") < keys.index("GAMMA")


def test_as_dict_operations_count_matches():
    parsed = _parsed("KEY1=v1\nKEY2=v2\n")
    result = rename(parsed, {"KEY1": "NEW1", "KEY2": "NEW2"})
    d = result.as_dict()
    assert len(d["operations"]) == 2


def test_to_env_string_all_keys_present():
    parsed = _parsed("HOST=localhost\nPORT=8080\n")
    result = rename(parsed, {"HOST": "APP_HOST"})
    env_str = result.to_env_string()
    assert "APP_HOST=localhost" in env_str
    assert "PORT=8080" in env_str


def test_skipped_does_not_affect_other_renames():
    parsed = _parsed("REAL=value\n")
    result = rename(parsed, {"REAL": "RENAMED", "FAKE": "WHATEVER"})
    assert result.renamed_count == 1
    assert "FAKE" in result.skipped
    keys = [e.key for e in result.entries]
    assert "RENAMED" in keys
