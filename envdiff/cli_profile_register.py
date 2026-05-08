"""Helpers to load user-defined profiles from a JSON config file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional


DEFAULT_PROFILE_CONFIG = Path(".envdiff_profiles.json")


def load_custom_profiles(
    config_path: Optional[Path] = None,
) -> Dict[str, Dict[str, str]]:
    """Load custom profiles from a JSON file.

    Expected format::

        {
          "myprofile": {
            "REQUIRED_KEY_1": "",
            "REQUIRED_KEY_2": ""
          }
        }

    Returns an empty dict if the file does not exist.
    """
    path = config_path or DEFAULT_PROFILE_CONFIG
    if not Path(path).exists():
        return {}
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid profile config '{path}': {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"Profile config '{path}' must be a JSON object.")
    validated: Dict[str, Dict[str, str]] = {}
    for name, keys in raw.items():
        if not isinstance(keys, dict):
            raise ValueError(
                f"Profile '{name}' must map to an object of key: value pairs."
            )
        validated[name] = {str(k): str(v) for k, v in keys.items()}
    return validated


def list_profiles(
    custom_profiles: Optional[Dict[str, Dict[str, str]]] = None,
) -> Dict[str, int]:
    """Return a mapping of profile name -> number of required keys."""
    from envdiff.profiler import BUILTIN_PROFILES

    merged = {**BUILTIN_PROFILES, **(custom_profiles or {})}
    return {name: len(keys) for name, keys in sorted(merged.items())}
