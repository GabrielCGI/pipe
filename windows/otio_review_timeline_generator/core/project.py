"""
core/project.py — PrismProject dataclass and ProjectLoader.

Reads pipeline.json and shotInfo.json from a Prism project root to expose:
  - project metadata (name, fps)
  - departments and tasks defined in the project
  - authoritative shot frame ranges
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import (
    PIPELINE_JSON,
    SHOTINFO_JSON,
    DEFAULT_FPS,
    DEFAULT_FRAME_START,
    PRISM_CONFIG_PATH,
)
from core.exceptions import InvalidProjectError, PipelineConfigError, ShotInfoError


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Department:
    """Represents a pipeline department as defined in pipeline.json."""
    name: str                    # e.g. "Compo"
    abbreviation: str            # e.g. "cmp"
    default_tasks: List[str]     # e.g. ["Compo", "MattePaint"]
    color: Optional[str] = None  # hex color string if defined


@dataclass
class PrismProject:
    """All metadata needed from a Prism project to drive the scanner and builder."""
    name: str
    root_path: Path
    fps: float
    departments_shot: List[Department]          # departments applicable to shots
    shot_ranges: Dict[str, Tuple[int, int]]     # "seq/shot" -> (frame_in, frame_out)

    def get_frame_range(self, sequence: str, shot: str) -> Tuple[int, int]:
        """
        Return (frame_in, frame_out) for a shot.
        Falls back to (DEFAULT_FRAME_START, DEFAULT_FRAME_START + 99) if not found.
        """
        key = f"{sequence}/{shot}"
        return self.shot_ranges.get(key, (DEFAULT_FRAME_START, DEFAULT_FRAME_START + 99))

    def resolve_task_name(self, folder_name: str) -> Optional[str]:
        """
        Map a filesystem folder name to a canonical task name.
        Handles direct name match and abbreviation lookup.
        Returns None if no match is found.
        """
        lower = folder_name.lower()
        for dept in self.departments_shot:
            # Match by abbreviation
            if dept.abbreviation.lower() == lower:
                return dept.default_tasks[0] if dept.default_tasks else dept.name
            # Match directly against department name or any default task
            if dept.name.lower() == lower:
                return dept.name
            for task in dept.default_tasks:
                if task.lower() == lower:
                    return task
        return None

    def all_task_names(self) -> List[str]:
        """Return a flat, deduplicated list of all canonical task names."""
        seen: dict = {}
        for dept in self.departments_shot:
            for task in dept.default_tasks:
                seen[task] = None
            seen[dept.name] = None
        return list(seen)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

class ProjectLoader:
    """Static helpers to load a PrismProject from the filesystem."""

    @staticmethod
    def from_path(root: Path) -> PrismProject:
        """
        Build a PrismProject from a project root directory.
        Raises InvalidProjectError if the path is not a valid Prism project.
        """
        root = Path(root)
        pipeline_path = root / PIPELINE_JSON
        shotinfo_path = root / SHOTINFO_JSON

        if not pipeline_path.exists():
            raise InvalidProjectError(
                f"Not a valid Prism project (missing {PIPELINE_JSON}): {root}"
            )

        try:
            pipeline_data = json.loads(pipeline_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise PipelineConfigError(f"Cannot read pipeline.json: {exc}") from exc

        name = root.name
        fps = ProjectLoader._parse_fps(pipeline_data)
        departments = ProjectLoader._parse_departments(pipeline_data)

        shot_ranges: Dict[str, Tuple[int, int]] = {}
        if shotinfo_path.exists():
            try:
                shot_ranges = ProjectLoader._parse_shot_ranges(shotinfo_path)
            except Exception as exc:
                raise ShotInfoError(f"Cannot read shotInfo.json: {exc}") from exc

        return PrismProject(
            name=name,
            root_path=root,
            fps=fps,
            departments_shot=departments,
            shot_ranges=shot_ranges,
        )

    @staticmethod
    def discover_from_prism_config() -> List[Tuple[str, Path]]:
        """
        Read the Prism global config file and return a list of (name, path) tuples
        for each recent/known project. Returns an empty list if the config is missing.
        """
        config_path = Path(PRISM_CONFIG_PATH)
        if not config_path.exists():
            return []

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return []

        projects: List[Tuple[str, Path]] = []

        # Prism stores recent projects under different keys depending on version.
        # Try common locations.
        recent = (
            data.get("recent_projects")
            or data.get("recentProjects")
            or data.get("projects", {}).get("recent", [])
            or []
        )

        # Also check "globals" -> "project_paths" or similar
        if not recent:
            globals_data = data.get("globals", {})
            recent = globals_data.get("recent_projects", [])

        # Sort by date descending if entries carry a timestamp (Prism 2.0.18+)
        def _entry_date(e):
            if isinstance(e, dict):
                return e.get("date", 0) or 0
            return 0

        recent = sorted(recent, key=_entry_date, reverse=True)

        for entry in recent:
            if isinstance(entry, str):
                p = Path(entry)
                if p.exists() and (p / PIPELINE_JSON).exists():
                    projects.append((p.name, p))
            elif isinstance(entry, dict):
                # Prism 2.0.18 uses "configPath" pointing to pipeline.json
                path_val = (
                    entry.get("path")
                    or entry.get("root")
                    or entry.get("projectPath")
                    or entry.get("configPath")
                )
                if path_val:
                    p = Path(path_val)
                    # configPath points to pipeline.json — walk up to project root
                    if p.suffix == ".json" and not p.is_dir():
                        p = p.parent.parent
                    if p.exists() and (p / PIPELINE_JSON).exists():
                        name = entry.get("name") or p.name
                        projects.append((name, p))

        return projects

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_fps(data: dict) -> float:
        """Extract FPS from pipeline.json, falling back to DEFAULT_FPS."""
        # Try common locations in Prism pipeline.json structure
        fps = (
            data.get("globals", {}).get("fps")
            or data.get("settings", {}).get("fps")
            or data.get("fps")
        )
        if fps is not None:
            try:
                return float(fps)
            except (ValueError, TypeError):
                pass
        return DEFAULT_FPS

    @staticmethod
    def _parse_departments(data: dict) -> List[Department]:
        """
        Parse departments from pipeline.json.
        Prism stores them under "departments_shot" (or "globals" -> "departments").
        """
        depts_raw = (
            data.get("departments_shot")
            or data.get("globals", {}).get("departments_shot")
            or data.get("globals", {}).get("departments")
            or []
        )

        departments: List[Department] = []
        for entry in depts_raw:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name", "")
            abbrev = entry.get("abbreviation") or entry.get("abbrev") or name[:3].lower()
            tasks_raw = entry.get("defaultTasks") or entry.get("tasks") or [name]
            tasks = [t for t in tasks_raw if isinstance(t, str) and t]
            color = entry.get("color")
            if name:
                departments.append(Department(
                    name=name,
                    abbreviation=abbrev,
                    default_tasks=tasks,
                    color=color,
                ))

        # Provide sensible defaults if pipeline.json has no department info
        if not departments:
            departments = _default_departments()
        else:
            # Filter out Lighting — replaced by SlapComp
            departments = [d for d in departments if d.name.lower() != "lighting"]

            existing_names = {d.name.lower() for d in departments}

            # Inject missing extra departments (CFX, SetDress, QC, SlapComp)
            for extra in _EXTRA_DEPARTMENTS:
                if extra.name.lower() not in existing_names:
                    departments.append(extra)

            # Remove SlapComp from Compo's task list — it's a standalone dept in the UI
            for dept in departments:
                if dept.name.lower() == "compo":
                    dept.default_tasks = [
                        t for t in dept.default_tasks if t.lower() != "slapcomp"
                    ]

        # Sort departments according to canonical display order
        departments.sort(
            key=lambda d: _DISPLAY_ORDER.index(d.name.lower())
            if d.name.lower() in _DISPLAY_ORDER else len(_DISPLAY_ORDER)
        )

        return departments

    @staticmethod
    def _parse_shot_ranges(shotinfo_path: Path) -> Dict[str, Tuple[int, int]]:
        """
        Parse shot frame ranges from shotInfo.json.
        Expected structure: {"shotRanges": {"seq": {"shot": [frame_in, frame_out]}}}
        or flatter variants.
        Returns dict keyed by "seq/shot".
        """
        data = json.loads(shotinfo_path.read_text(encoding="utf-8"))
        result: Dict[str, Tuple[int, int]] = {}

        shot_ranges = data.get("shotRanges") or data.get("shot_ranges") or {}

        for seq, shots in shot_ranges.items():
            if not isinstance(shots, dict):
                continue
            for shot, rng in shots.items():
                if isinstance(rng, (list, tuple)) and len(rng) >= 2:
                    try:
                        frame_in = int(rng[0])
                        frame_out = int(rng[1])
                        result[f"{seq}/{shot}"] = (frame_in, frame_out)
                    except (ValueError, TypeError):
                        pass

        return result


# ---------------------------------------------------------------------------
# Fallback departments when pipeline.json has no department data
# ---------------------------------------------------------------------------

_DISPLAY_ORDER = [
    "layout", "setdress", "anim", "fx", "cfx", "qc", "slapcomp", "compo",
]

_EXTRA_DEPARTMENTS = [
    Department("SetDress", "std", ["SetDress"]),
    Department("CFX", "cfx", ["CFX"]),
    Department("QC", "qc", ["QC"]),
    Department("SlapComp", "slp", ["SlapComp"]),
]


def _default_departments() -> List[Department]:
    return [
        Department("Layout", "lay", ["Layout"]),
        Department("SetDress", "std", ["SetDress"]),
        Department("Anim", "anm", ["Anim", "Animation"]),
        Department("FX", "fx", ["FX", "Simulation"]),
        Department("CFX", "cfx", ["CFX"]),
        Department("QC", "qc", ["QC"]),
        Department("SlapComp", "slp", ["SlapComp"]),
        Department("Compo", "cmp", ["Compo", "MattePaint"]),
    ]
