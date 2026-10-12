"""JSON files shared by every Nuke session of a project (loader prefs,
precomp manifests), possibly read by one artist while another writes them."""

import json
import os
import tempfile
import time

_REPLACE_ATTEMPTS = 6
_RETRY_DELAY_S = 0.1


class UnreadableJson(Exception):
    """The file exists but can't be read or parsed right now."""


def read_json(path: str):
    """Parsed content, None when the file doesn't exist. Raises
    UnreadableJson otherwise, so that a caller never mistakes a file it
    could not read for an empty one (and writes that back)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        raise UnreadableJson(f"{path}: {e}") from e


def atomic_write_json(path: str, data):
    """Readers see the old file or the new one, never a partial write
    (temp file + os.replace). On Windows the replace fails while another
    process has the file open — another session reading it at that very
    moment — so it is retried briefly before giving up."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if attempt == _REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(_RETRY_DELAY_S)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
