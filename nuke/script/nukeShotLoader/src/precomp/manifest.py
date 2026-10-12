"""precomp.json manifests, version folders and frames on disk (no nuke import).

Each rendered version folder holds a manifest written when the render is
prepared:
    {"schema": 2, "hash": <upstream content hash>, "renderpath": ".../x.####.exr",
     "first": 1001, "last": 1100, "node": "PrecompWrite1", "script": "...", "created": "..."}
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..core.jsonio import UnreadableJson, atomic_write_json, read_json
from .spec import SCHEMA

MANIFEST_NAME = "precomp.json"
_VERSION_DIR_RE = re.compile(r"^v(\d{3,})$")
_FRAME_TOKEN_RE = re.compile(r"#+|%0?(\d*)d")

FrameRange = Tuple[int, int]


@dataclass
class CacheEntry:
    version: int
    folder: str
    path: str          # full file pattern (####)
    first: int
    last: int


@dataclass
class Pending:
    """A version rendered for the current hash but not complete (yet)."""
    version: int
    present: int
    needed: int


# folder -> (folder mtime when read, manifest): a manifest is written once
# when its render is prepared, so it is re-read only when its folder changed.
_manifests: Dict[str, Tuple[int, Optional[dict]]] = {}


def write_manifest(folder: str, data: dict):
    os.makedirs(folder, exist_ok=True)
    atomic_write_json(os.path.join(folder, MANIFEST_NAME), dict(data, schema=SCHEMA))
    _manifests.pop(folder, None)


def discard_manifest(folder: str) -> bool:
    """Remove the manifest of a version that will not be rendered, and its
    folder with it. Refused (False) as soon as the folder holds anything
    else: frames are never deleted."""
    try:
        if os.listdir(folder) != [MANIFEST_NAME]:
            return False
        os.remove(os.path.join(folder, MANIFEST_NAME))
        os.rmdir(folder)
    except OSError:
        return False
    finally:
        _manifests.pop(folder, None)
    return True


def read_manifest(folder: str) -> Optional[dict]:
    """The manifest, None when absent, unreadable or of another schema
    (the version is then simply not a candidate cache)."""
    try:
        data = read_json(os.path.join(folder, MANIFEST_NAME))
    except UnreadableJson:
        return None
    return data if isinstance(data, dict) and data.get("schema") == SCHEMA else None


def _cached_manifest(folder: str, folder_mtime: int) -> Optional[dict]:
    cached = _manifests.get(folder)
    if cached is None or cached[0] != folder_mtime:
        cached = _manifests[folder] = (folder_mtime, read_manifest(folder))
    return cached[1]


def _version_entries(root: str) -> List[Tuple[int, str, int]]:
    """(version, folder, folder mtime) of the v### sub-folders of `root`,
    newest first. One directory read: on Windows scandir returns the
    folder stats with the listing."""
    found = []
    try:
        with os.scandir(root) as it:
            for entry in it:
                m = _VERSION_DIR_RE.match(entry.name)
                if not m:
                    continue
                try:
                    if entry.is_dir():
                        found.append((int(m.group(1)), entry.path, entry.stat().st_mtime_ns))
                except OSError:
                    continue
    except OSError:
        return []
    return sorted(found, reverse=True)


def version_folders(root: str) -> List[Tuple[int, str]]:
    """(version, folder) of the v### sub-folders of `root`, newest first."""
    return [(version, folder) for version, folder, _ in _version_entries(root)]


def next_version(root: str) -> int:
    """Version the next render goes to: right after the highest version
    folder on disk, whatever the Write's version knob says, so version
    numbers never leave a gap (a version bumped without being rendered is
    simply the one rendered next)."""
    return max((v for v, _ in version_folders(root)), default=0) + 1


def _pattern_regex(basename: str) -> Optional[re.Pattern]:
    """'x.####.exr' / 'x.%04d.exr' -> regex capturing the frame number."""
    m = _FRAME_TOKEN_RE.search(basename)
    if not m:
        return None
    width = len(m.group(0)) if m.group(0).startswith("#") else int(m.group(1) or 1)
    return re.compile("^" + re.escape(basename[:m.start()]) + r"(\d{%d,})" % width
                      + re.escape(basename[m.end():]) + "$", re.IGNORECASE)


class DiskListing:
    """One os.listdir per folder for the lifetime of an evaluation."""

    def __init__(self):
        self._names: Dict[str, List[str]] = {}

    def frames(self, folder: str, basename: str) -> Set[int]:
        regex = _pattern_regex(basename)
        if regex is None:
            return set()
        if folder not in self._names:
            try:
                self._names[folder] = os.listdir(folder)
            except OSError:
                self._names[folder] = []
        return {int(m.group(1)) for m in map(regex.match, self._names[folder]) if m}


def find_cache(root: str, content_hash: str, needed: FrameRange,
               listing: Optional[DiskListing] = None) -> Tuple[Optional[CacheEntry], Optional[Pending]]:
    """Newest complete version rendered for `content_hash`, plus the newest
    incomplete one (a render in progress or a failed one) for reporting."""
    listing = listing or DiskListing()
    wanted = set(range(needed[0], needed[1] + 1))
    pending = None
    for version, folder, folder_mtime in _version_entries(root):
        manifest = _cached_manifest(folder, folder_mtime)
        if not manifest or manifest.get("hash") != content_hash:
            continue
        basename = os.path.basename(manifest.get("renderpath", "").replace("\\", "/"))
        frames = listing.frames(folder, basename)
        if wanted <= frames:
            path = os.path.join(folder, basename).replace("\\", "/")
            return CacheEntry(version, folder, path, needed[0], needed[1]), pending
        if pending is None:
            pending = Pending(version, len(wanted & frames), len(wanted))
    return None, pending
