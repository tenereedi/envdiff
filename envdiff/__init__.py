"""envdiff — diff and reconcile .env files across environments."""

__version__ = "0.1.0"
__author__ = "envdiff contributors"

from envdiff.parser import parse_env_file, parse_env_string, EnvEntry, ParseResult

__all__ = [
    "parse_env_file",
    "parse_env_string",
    "EnvEntry",
    "ParseResult",
]
