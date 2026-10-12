"""Parsing and comparison of Prism version tokens ("v001", "v0010")."""

import re
from typing import Iterable, Optional

VERSION_RE = re.compile(r'^v(\d{3,4})$')
VERSION_IN_TEXT_RE = re.compile(r'v(\d{3,4})')


def version_int(version: Optional[str]) -> int:
    """'v016' -> 16. Anything that isn't a strict v###/v#### token -> -1."""
    if not version:
        return -1
    m = VERSION_RE.match(version)
    return int(m.group(1)) if m else -1


def extract_version_from_path(path: str) -> Optional[str]:
    """Return the LAST v###/v#### token in `path`.

    The version folder sits at the deep end of a Prism path, so the last
    match is immune to 'v###' substrings in the project/shot/pass names.
    """
    if not path:
        return None
    matches = VERSION_IN_TEXT_RE.findall(path)
    return f"v{matches[-1]}" if matches else None


def latest_version(versions: Iterable[str]) -> Optional[str]:
    """Highest valid version by integer order, or None."""
    valid = [v for v in versions if VERSION_RE.match(v)]
    return max(valid, key=version_int) if valid else None
