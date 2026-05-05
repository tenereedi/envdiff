"""envdiff — diff and reconcile .env files across environments."""

__version__ = "0.1.0"
__author__ = "envdiff contributors"

from envdiff.parser import parse_env_file, parse_env_string, EnvEntry, ParseResult


def get_version() -> str:
    """Return the current version of envdiff.

    Returns
    -------
    str
        The version string in ``MAJOR.MINOR.PATCH`` format.

    Examples
    --------
    >>> import envdiff
    >>> envdiff.get_version()
    '0.1.0'
    """
    return __version__


__all__ = [
    "parse_env_file",
    "parse_env_string",
    "EnvEntry",
    "ParseResult",
    "get_version",
]
