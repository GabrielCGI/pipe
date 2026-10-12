"""Frame-coverage checks of asset versions against the scene frame range."""

import os
from typing import Dict, Optional, Set, Tuple

from . import asset_discoverer as fs
from .asset_item import AssetItem
from .versions import version_int

FrameRange = Optional[Tuple[int, int]]


def _key(folder: str) -> str:
    return os.path.normcase(os.path.normpath(folder))


class FrameCoverage:
    """Answers "does version X cover the scene range?" with a per-folder
    frame-set cache, so status checks and label syncs scan disk once.
    Cleared by a manual refresh; folders known to have changed (a loaded
    Read's folder receiving frames) are forgotten individually."""

    def __init__(self):
        self._cache: Dict[str, Optional[Set[int]]] = {}

    def clear(self):
        self._cache.clear()

    def forget(self, folder: str):
        self._cache.pop(_key(folder), None)

    def frames(self, folder: str) -> Optional[Set[int]]:
        key = _key(folder)
        if key not in self._cache:
            self._cache[key] = fs.frame_numbers(folder)
        return self._cache[key]

    def covers(self, item: AssetItem, version: str, scene_range: FrameRange) -> bool:
        """True only if EVERY scene frame exists on disk — endpoints alone
        would let first/middle/last preview renders pass as complete."""
        if item.asset_type == "Camera" or not scene_range:
            return True
        try:
            folder = item.folder(version)
            if not folder:
                return False
            frames = self.frames(folder)
            if not frames:
                # Static image assets (.psd paintover, stMap) have no frames.
                return fs.folder_has_image(folder)
            return frames.issuperset(range(scene_range[0], scene_range[1] + 1))
        except Exception as e:
            print(f"[ShotAssetLoader] Frame coverage check failed for {item.asset_name}: {e}")
            return False

    def missing_count(self, item: AssetItem, version: Optional[str], scene_range: FrameRange) -> Optional[int]:
        """Scene frames absent on disk. 0 when complete or not applicable,
        None when the version can't be read (callers treat it as 0)."""
        if not version or item.asset_type == "Camera" or not scene_range:
            return 0
        folder = item.folder(version)
        if not folder:
            return None
        frames = self.frames(folder)
        if not frames:
            return None
        return sum(1 for f in range(scene_range[0], scene_range[1] + 1) if f not in frames)

    def frame_range(self, item: AssetItem, version: Optional[str]) -> FrameRange:
        """(first, last) frame on disk for a version, None if not per-frame."""
        if not version or item.asset_type == "Camera":
            return None
        folder = item.folder(version)
        if not folder:
            return None
        frames = self.frames(folder)
        return (min(frames), max(frames)) if frames else None

    def pick_update_target(self, item: AssetItem, scene_range: FrameRange) -> Tuple[Optional[str], bool]:
        """(version, is_full): the highest fully-covering version wins over
        any higher partial one; falls back to the highest version (partial)."""
        if not item.versions:
            return None, False
        if item.asset_type == "Camera":
            return max(item.versions, key=version_int), True
        ordered = sorted(item.versions, key=version_int, reverse=True)
        for version in ordered:
            if self.covers(item, version, scene_range):
                return version, True
        return ordered[0], False
