"""
Version utilities — single source of truth for parsing/comparing Prism version
strings (e.g. "v001", "v0010"). Used by both the UI and the node builder.
"""

import re
from typing import Iterable, Optional

# Strict: matches the full string "v###" or "v####"
VERSION_RE = re.compile(r'^v(\d{3,4})$')
# Loose: extracts a version token embedded in a longer path/string
VERSION_IN_TEXT_RE = re.compile(r'v(\d{3,4})')


def version_int(version_str: Optional[str]) -> int:
    """Convert 'v016' / 'v0123' to its integer for safe comparison.
    Returns -1 for anything that doesn't match the strict 'v###'/'v####' shape."""
    if not version_str:
        return -1
    m = VERSION_RE.match(version_str)
    return int(m.group(1)) if m else -1


def extract_version_from_path(path: str) -> Optional[str]:
    """Return the LAST 'v###'/'v####' token found in `path`, or None.

    The version folder lives at the deep end of the Prism path
    (.../<asset_name>/<version>/<file>), so taking the last match is robust
    against earlier 'v###' substrings appearing in the shot name, the render
    pass name, the project name, etc."""
    if not path:
        return None
    matches = VERSION_IN_TEXT_RE.findall(path)
    if not matches:
        return None
    return f"v{matches[-1]}"


def latest_version(versions: Iterable[str]) -> Optional[str]:
    """Return the highest version string from an iterable, by integer order.
    Versions that don't match the v### shape are ignored."""
    valid = [v for v in versions if VERSION_RE.match(v)]
    if not valid:
        return None
    return max(valid, key=version_int)
