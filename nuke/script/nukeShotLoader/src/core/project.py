"""Project / shot context derived from the Nuke script path and pipeline.json."""

import json
import os
import re
from typing import Optional, Tuple

from .config import Config

_PROJECT_ROOT_RE = re.compile(r'^([A-Za-z]:/[^/]+)')
# <sequence>-<shot>_<task>_v###.nk — the shot may contain underscores
# (e.g. LINEUP-CHAR_ALL_Compo_v001.nk), the task is a single token.
_SCRIPT_NAME_RE = re.compile(r'^([^-]+)-(.+)_[^_]+_v\d{3,4}\.nk$')
_SHOT_PATH_RE = re.compile(r'/Shots/(SEQ_[^/]+)/(SH\d+)/')
_SCRIPT_VERSION_RE = re.compile(r'_v(\d{3,4})\.nk$')

_DEFAULT_FPS = 25.0


def detect_project_root(script_path: Optional[str]) -> Optional[str]:
    """'<drive>:/<project>/...' -> '<drive>:\\<project>', else None."""
    if not script_path:
        print("[ShotAssetLoader] No saved script, using default project root")
        return None
    m = _PROJECT_ROOT_RE.match(script_path.replace('\\', '/'))
    if not m:
        print(f"[ShotAssetLoader] Script path doesn't match <drive>:/<project>/... : {script_path}")
        return None
    root = m.group(1).replace('/', os.sep)
    print(f"[ShotAssetLoader] Detected project root from script: {root}")
    return root


def detect_shot_context(script_path: str) -> Optional[Tuple[str, str]]:
    """(sequence, shot) from the script filename, falling back to the
    /Shots/SEQ_xxx/SHxxx/ folder layout."""
    normalized = script_path.replace('\\', '/')

    m = _SCRIPT_NAME_RE.match(normalized.rsplit('/', 1)[-1])
    if m:
        print(f"[ShotAssetLoader] Detected from filename: {m.group(1)}/{m.group(2)}")
        return m.group(1), m.group(2)

    m = _SHOT_PATH_RE.search(normalized)
    if m:
        print(f"[ShotAssetLoader] Detected from path: {m.group(1)}/{m.group(2)}")
        return m.group(1), m.group(2)
    return None


def script_version(script_path: Optional[str]) -> Optional[str]:
    """'.../SEQ-SH_comp_v053.nk' -> 'v053'."""
    if not script_path:
        return None
    m = _SCRIPT_VERSION_RE.search(os.path.basename(script_path))
    return f"v{m.group(1)}" if m else None


def project_name(project_root: str) -> str:
    return os.path.basename(project_root.rstrip(os.sep))


def _read_pipeline_json(project_root: str) -> dict:
    path = os.path.join(project_root, Config.PIPELINE_PATH, Config.PIPELINE_JSON)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def project_fps(project_root: str) -> float:
    """FPS declared in pipeline.json ('globals.fps'), 25 when unreadable."""
    try:
        return float(_read_pipeline_json(project_root).get("globals", {}).get("fps", _DEFAULT_FPS))
    except Exception as e:
        print(f"[ShotAssetLoader] Could not read project FPS from pipeline.json: {e}")
        return _DEFAULT_FPS


def deadline_pool(project_root: str) -> Tuple[Optional[str], Optional[str]]:
    """(pool, group) of the 'Nuke' entry of deadline.poolPresets."""
    try:
        presets = _read_pipeline_json(project_root).get("deadline", {}).get("poolPresets", [])
    except Exception as e:
        print(f"[ShotAssetLoader] Could not read pipeline.json: {e} — pool/group left untouched")
        return None, None
    for preset in presets:
        if preset.get("name") == "Nuke":
            return preset.get("pool"), preset.get("group")
    print("[ShotAssetLoader] pipeline.json has no poolPresets 'Nuke' entry — pool/group left untouched")
    return None, None
