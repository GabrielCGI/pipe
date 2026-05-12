"""
core/version_cache.py — Persistent cache for version completeness results.

Cache file format (JSON):
{
  "C:/project/.../Renders/2dRender/Compo/v003": {
    "complete": true,
    "frame_count": 100,
    "scanned_at": "2026-04-13T14:30:00+00:00"
  }
}

Rules:
  - complete=True entries are permanent: a finished render never loses frames.
  - complete=False entries are re-checked on every app launch (not reused as
    a positive cache hit). They are kept in the file only for diagnostic purposes
    and are pruned by invalidate_incomplete().
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from config import VERSION_CACHE_SUBPATH

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

class VersionCacheEntry:
    """In-memory representation of one cached version result."""
    __slots__ = ("complete", "frame_count", "scanned_at")

    def __init__(self, complete: bool, frame_count: int, scanned_at: datetime) -> None:
        self.complete = complete
        self.frame_count = frame_count
        self.scanned_at = scanned_at

    def to_dict(self) -> dict:
        return {
            "complete": self.complete,
            "frame_count": self.frame_count,
            "scanned_at": self.scanned_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VersionCacheEntry":
        return cls(
            complete=bool(d["complete"]),
            frame_count=int(d.get("frame_count", 0)),
            scanned_at=datetime.fromisoformat(d["scanned_at"]),
        )


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

class VersionCache:
    """
    Load-once, flush-once cache for version completeness.

    Typical usage inside ScanWorker:
        cache = VersionCache.load(project_root)   # once before the loop
        ... use cache.get / cache.set ...
        cache.flush()                              # once after scan_complete

    Only complete=True entries are used as positive cache hits.
    complete=False entries are ignored on read (the version is re-scanned).
    """

    def __init__(self, entries: Dict[str, VersionCacheEntry], path: Path) -> None:
        self._entries = entries
        self._path = path
        self._dirty = False

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, project_root: Path) -> "VersionCache":
        """
        Load the cache from {project_root}/VERSION_CACHE_SUBPATH.
        Returns an empty cache if the file does not exist or is corrupt.
        """
        cache_path = project_root / VERSION_CACHE_SUBPATH
        entries: Dict[str, VersionCacheEntry] = {}

        if cache_path.is_file():
            try:
                raw: dict = json.loads(cache_path.read_text(encoding="utf-8"))
                for key, val in raw.items():
                    try:
                        entries[key] = VersionCacheEntry.from_dict(val)
                    except Exception:
                        pass  # skip malformed entries silently
            except Exception as exc:
                log.warning("Could not load version cache (%s): %s", cache_path, exc)

        instance = cls(entries, cache_path)

        # Prune missing paths when cache grows large
        if len(entries) > 500:
            instance._prune_missing_paths()

        return instance

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, version_path: Path) -> Optional[VersionCacheEntry]:
        """
        Return a cached entry only if complete=True.
        Incomplete entries are never returned (always re-checked).
        """
        key = str(version_path)
        entry = self._entries.get(key)
        if entry is None or not entry.complete:
            return None
        return entry

    def get_frame_count(self, version_path: Path) -> Optional[int]:
        """
        Return the cached frame_count regardless of completeness, or None if unknown.
        Used for inter-version comparison when no shotInfo.json is available.
        """
        entry = self._entries.get(str(version_path))
        return entry.frame_count if entry is not None else None

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def set(self, version_path: Path, complete: bool, frame_count: int) -> None:
        """Store a result. Marks the cache dirty for the next flush."""
        key = str(version_path)
        self._entries[key] = VersionCacheEntry(
            complete=complete,
            frame_count=frame_count,
            scanned_at=datetime.now(timezone.utc),
        )
        self._dirty = True

    def invalidate_incomplete(self) -> None:
        """Remove all incomplete entries. Called when 'Recheck Renders' is triggered."""
        keys = [k for k, v in self._entries.items() if not v.complete]
        for k in keys:
            del self._entries[k]
        if keys:
            self._dirty = True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def flush(self) -> None:
        """Write cache to disk only if it was modified. Silently swallows I/O errors."""
        if not self._dirty:
            return
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = {k: v.to_dict() for k, v in self._entries.items()}
            self._path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as exc:
            log.warning("Could not save version cache (%s): %s", self._path, exc)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def _prune_missing_paths(self) -> None:
        """Remove entries whose version folder no longer exists on disk."""
        keys_to_delete = [k for k in self._entries if not Path(k).is_dir()]
        for k in keys_to_delete:
            del self._entries[k]
        if keys_to_delete:
            self._dirty = True
