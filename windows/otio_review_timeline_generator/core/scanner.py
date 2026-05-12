"""
core/scanner.py — Prism project filesystem scanner.

Walks the 03_Production/Shots tree, discovers shots, and resolves media
versions for requested pipeline tasks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import SHOTS_SUBPATH, RENDER_ROOTS, VERSION_PATTERN, NATURAL_SORT_RE
from core.media import MediaDiscovery, MediaItem
from core.project import PrismProject


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class VersionEntry:
    """A single versioned render/playblast folder for a task."""
    version_str: str        # "v001", "v003"
    version_num: int        # 1, 3
    path: Path              # absolute path to the version folder
    task: str               # canonical task name: "Compo", "Anim"
    render_root: str        # which RENDER_ROOTS entry this came from


@dataclass
class ShotEntry:
    """All information about a single shot inside the project."""
    sequence: str                               # e.g. "SEQ_mcdo", "sq010"
    shot: str                                   # e.g. "SH060", "sh010", "040"
    shot_path: Path                             # absolute path to shot folder
    frame_range: Tuple[int, int]                # (frame_in, frame_out)
    has_shot_range: bool = False               # True if range comes from shotInfo.json
    # task_name -> list of VersionEntry sorted by version_num ascending
    versions_by_task: Dict[str, List[VersionEntry]] = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        """Hierarchical key: "SEQ_mcdo/SH060"."""
        return f"{self.sequence}/{self.shot}"

    @property
    def display_name(self) -> str:
        """Human-readable clip name: "SEQ_mcdo-SH060"."""
        return f"{self.sequence}-{self.shot}"

    def latest_version(self, task: str) -> Optional[VersionEntry]:
        """Return the highest-numbered VersionEntry for *task*, or None."""
        versions = self.versions_by_task.get(task, [])
        return versions[-1] if versions else None

    def available_tasks(self) -> List[str]:
        return list(self.versions_by_task.keys())


# ---------------------------------------------------------------------------
# Natural sort helper
# ---------------------------------------------------------------------------

def _natural_key(s: str) -> list:
    """Key function for natural (human) sort order: 'sh2' < 'sh10'."""
    parts = NATURAL_SORT_RE.split(s.lower())
    return [int(p) if p.isdigit() else p for p in parts]


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class ProjectScanner:
    """
    Scans a PrismProject's shots folder and resolves media per task.

    Usage:
        scanner = ProjectScanner(project)
        shots = scanner.scan_shots()          # basic shot list (fast)
        scanner.scan_versions(shots, tasks)   # populate versions_by_task
    """

    def __init__(self, project: PrismProject) -> None:
        self.project = project
        self._shots_root = project.root_path / SHOTS_SUBPATH

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan_shots(self) -> List[ShotEntry]:
        """
        Traverse the two-level Shots directory and return a sorted ShotEntry list.
        Sequence-level folders named "_sequence" are skipped.
        """
        shots: List[ShotEntry] = []

        if not self._shots_root.is_dir():
            return shots

        for seq_dir in sorted(self._shots_root.iterdir(), key=lambda p: _natural_key(p.name)):
            if not seq_dir.is_dir():
                continue
            sequence = seq_dir.name

            for shot_dir in sorted(seq_dir.iterdir(), key=lambda p: _natural_key(p.name)):
                if not shot_dir.is_dir():
                    continue
                shot_name = shot_dir.name
                # Skip sequence-level pseudo-shot folders
                if shot_name.startswith("_"):
                    continue

                frame_range = self.project.get_frame_range(sequence, shot_name)
                shots.append(ShotEntry(
                    sequence=sequence,
                    shot=shot_name,
                    shot_path=shot_dir,
                    frame_range=frame_range,
                    has_shot_range=self.project.has_shot_range(sequence, shot_name),
                ))

        return shots

    def scan_versions(
        self,
        shots: List[ShotEntry],
        tasks: List[str],
    ) -> None:
        """
        Populate *versions_by_task* on each ShotEntry in *shots*.
        Only versions for the requested *tasks* (canonical names) are scanned.
        Modifies shots in-place.
        """
        for shot in shots:
            shot.versions_by_task = self._scan_versions_for_shot(shot, tasks)

    def scan_versions_for_shot(
        self,
        shot: ShotEntry,
        tasks: List[str],
    ) -> Dict[str, List[VersionEntry]]:
        """Public single-shot version scan (useful for incremental/lazy loading)."""
        result = self._scan_versions_for_shot(shot, tasks)
        shot.versions_by_task = result
        return result

    def find_media(
        self,
        version: VersionEntry,
        fps: Optional[float] = None,
        fallback_frame_range: Optional[Tuple[int, int]] = None,
    ) -> Optional[MediaItem]:
        """Resolve a VersionEntry to a concrete MediaItem."""
        return MediaDiscovery.find_in_version_folder(
            version.path,
            fps=fps or self.project.fps,
            fallback_frame_range=fallback_frame_range,
        )

    def find_complete_media(
        self,
        versions: List[VersionEntry],
        expected_frame_count: int,
        fps: Optional[float] = None,
        fallback_frame_range: Optional[Tuple[int, int]] = None,
        cache=None,  # Optional[VersionCache] — local import to avoid circular
        has_shot_range: bool = True,
    ) -> Tuple[Optional[MediaItem], Optional[VersionEntry], bool]:
        """
        Walk *versions* from latest to oldest and return the first complete one.

        Two completeness strategies:
        - has_shot_range=True  → compare frame_count against expected_frame_count
                                 (from shotInfo.json)
        - has_shot_range=False → compare frame_count of vN against v(N-1).
                                 If vN has fewer frames than its predecessor, it is
                                 considered incomplete (render still in progress).
                                 Only version 1 (no predecessor) is always complete.

        Returns:
            (media, version_entry, was_complete)
            - was_complete=True  → selected version passed the completeness check
            - was_complete=False → no complete version found; latest is returned

        *cache* is an optional VersionCache instance. complete=True hits skip the
        disk scan; incomplete entries are always re-scanned.
        """
        if not versions:
            return None, None, False

        resolved_fps = fps or self.project.fps
        last_media: Optional[MediaItem] = None
        last_entry: Optional[VersionEntry] = versions[-1]

        # If shotInfo.json had no entry for this shot, use inter-version comparison
        is_fallback_range = not has_shot_range

        # Build an index for fast predecessor lookup (version_num -> index in versions)
        # versions is sorted ascending by version_num
        version_index = {v.version_num: i for i, v in enumerate(versions)}

        for version_entry in reversed(versions):
            # --- positive cache hit: skip disk scan ---
            # Only trust the cache for completeness when shotInfo.json is available.
            # In fallback mode (no shotInfo.json), the cache frame_count may be stale
            # (frames deleted after the last scan), so always re-scan from disk.
            if cache is not None and not is_fallback_range:
                cached = cache.get(version_entry.path)
                if cached is not None:
                    # complete=True entry — still need to resolve the media object
                    media = self.find_media(version_entry, resolved_fps, fallback_frame_range)
                    if media is not None:
                        media.is_complete = True
                        return media, version_entry, True
                    # folder disappeared — try older version
                    continue

            # --- disk scan ---
            media = self.find_media(version_entry, resolved_fps, fallback_frame_range)
            if media is None:
                continue

            if is_fallback_range and media.media_type == "image_sequence":
                # No shotInfo.json: compare against predecessor frame_count
                idx = version_index[version_entry.version_num]
                if idx == 0:
                    # Oldest version — no predecessor, always consider complete
                    complete = True
                else:
                    prev_entry = versions[idx - 1]
                    # Try cache first to avoid an extra disk scan
                    prev_frame_count: Optional[int] = None
                    if cache is not None:
                        prev_frame_count = cache.get_frame_count(prev_entry.path)
                    if prev_frame_count is None:
                        prev_media = self.find_media(prev_entry, resolved_fps, fallback_frame_range)
                        if prev_media is not None:
                            prev_frame_count = prev_media.frame_count
                            if cache is not None:
                                # Store predecessor in cache (completeness unknown → use complete=True
                                # as best-effort since it's a "reference" version)
                                cache.set(prev_entry.path, True, prev_frame_count)
                    complete = (prev_frame_count is None) or (media.frame_count >= prev_frame_count)
            else:
                complete = MediaDiscovery.check_completeness(
                    media, expected_frame_count, is_fallback_range=False
                )

            media.is_complete = complete

            if cache is not None:
                cache.set(version_entry.path, complete, media.frame_count)

            if complete:
                return media, version_entry, True

            # Keep latest as fallback in case no complete version exists
            if last_media is None:
                last_media = media
                last_entry = version_entry

        # No complete version found — return latest incomplete
        if last_media is None:
            # latest was not scanned yet (all were positive cache hits that failed)
            last_media = self.find_media(last_entry, resolved_fps, fallback_frame_range)
            if last_media is not None:
                last_media.is_complete = False

        return last_media, last_entry, False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scan_versions_for_shot(
        self, shot: ShotEntry, tasks: List[str]
    ) -> Dict[str, List[VersionEntry]]:
        """
        For *shot*, look inside each RENDER_ROOTS subfolder for task folders,
        then version subfolders inside those.
        """
        result: Dict[str, List[VersionEntry]] = {}
        tasks_lower = {t.lower(): t for t in tasks}

        for render_root in RENDER_ROOTS:
            render_dir = shot.shot_path / render_root
            if not render_dir.is_dir():
                continue

            for task_dir in render_dir.iterdir():
                if not task_dir.is_dir():
                    continue

                canonical = self._resolve_task_folder(task_dir.name, tasks_lower)
                if canonical is None:
                    continue

                versions = self._collect_versions(task_dir, canonical, render_root)
                if not versions:
                    continue

                if canonical not in result:
                    result[canonical] = versions
                else:
                    # Merge: keep all unique version numbers, re-sort
                    existing_nums = {v.version_num for v in result[canonical]}
                    for v in versions:
                        if v.version_num not in existing_nums:
                            result[canonical].append(v)
                    result[canonical].sort(key=lambda v: v.version_num)

        return result

    def _resolve_task_folder(
        self, folder_name: str, tasks_lower: Dict[str, str]
    ) -> Optional[str]:
        """
        Map a filesystem folder name to a canonical task requested by the user.
        Returns the canonical task name or None if not matched.
        """
        lower = folder_name.lower()

        # Direct case-insensitive match against requested tasks
        if lower in tasks_lower:
            return tasks_lower[lower]

        # Fallback: ask the project to resolve via abbreviations / all known tasks
        resolved = self.project.resolve_task_name(folder_name)
        if resolved:
            resolved_lower = resolved.lower()
            if resolved_lower in tasks_lower:
                return tasks_lower[resolved_lower]

        return None

    @staticmethod
    def _collect_versions(
        task_dir: Path, canonical_task: str, render_root: str
    ) -> List[VersionEntry]:
        """
        Return all valid version entries inside *task_dir*, sorted ascending.
        """
        versions: List[VersionEntry] = []
        for v_dir in task_dir.iterdir():
            if not v_dir.is_dir():
                continue
            m = VERSION_PATTERN.match(v_dir.name)
            if not m:
                continue
            version_num = int(m.group(1))
            versions.append(VersionEntry(
                version_str=v_dir.name.lower(),  # normalise to "v001"
                version_num=version_num,
                path=v_dir,
                task=canonical_task,
                render_root=render_root,
            ))
        versions.sort(key=lambda v: v.version_num)
        return versions
