"""
config.py — Global constants and defaults for the OTIO Review Timeline Generator.
All tunable values live here; nothing is hardcoded in other modules.
"""

import re
import os
import platform

# ---------------------------------------------------------------------------
# Prism Pipeline folder paths (relative to project root)
# ---------------------------------------------------------------------------
PIPELINE_JSON = "00_Pipeline/pipeline.json"
SHOTINFO_JSON = "00_Pipeline/Shotinfo/shotInfo.json"
SHOTS_SUBPATH = "03_Production/Shots"

# Order in which to search for rendered media inside a shot folder.
# First match wins (2dRender preferred over 3dRender, both preferred over Playblasts).
RENDER_ROOTS = [
    "Renders/2dRender",
    "Renders/3dRender",
    "Playblasts",
]

# ---------------------------------------------------------------------------
# Media file extensions
# ---------------------------------------------------------------------------
IMAGE_SEQ_EXTENSIONS = [".exr", ".dpx", ".tiff", ".tif", ".png", ".jpg", ".jpeg"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".mxf", ".avi"]

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches Prism dot-separated frame numbers: "file.1001.exr" or "file.name.0001.exr"
# Groups: (1) base name without frame+ext, (2) frame digits, (3) extension with dot
FRAME_PATTERN = re.compile(r"^(.+)\.(\d{4,})(\.\w+)$")

# Matches version folder names: v001, v002, V010 ...
VERSION_PATTERN = re.compile(r"^v(\d+)$", re.IGNORECASE)

# Natural sort helper: splits string into text/int alternating chunks
NATURAL_SORT_RE = re.compile(r"(\d+)")

# ---------------------------------------------------------------------------
# Timeline / OTIO defaults
# ---------------------------------------------------------------------------
DEFAULT_FPS = 25.0
DEFAULT_FRAME_START = 1001  # Prism default in/out start

# ---------------------------------------------------------------------------
# Prism global config location (for reading recent projects)
# ---------------------------------------------------------------------------
def get_prism_config_path() -> str:
    """Return the OS-appropriate path to the Prism global config file."""
    if platform.system() == "Windows":
        # Prism 2 stores its config in Documents/Prism2, not AppData
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        return os.path.join(docs, "Prism2", "Prism.json")
    else:
        return os.path.expanduser("~/.config/Prism2/Prism.json")

PRISM_CONFIG_PATH = get_prism_config_path()

# ---------------------------------------------------------------------------
# OpenRV executable path
# ---------------------------------------------------------------------------
RV_EXECUTABLE = r"C:\ILLOGIC_APP\OpenRV\bin\rv.exe"

# ---------------------------------------------------------------------------
# Hiero Player executable path (Nuke --player mode)
# Auto-detects the latest Nuke version installed under C:\Program Files\.
# ---------------------------------------------------------------------------
def _find_latest_hiero():
    from pathlib import Path as _Path
    program_files = _Path(r"C:\Program Files")
    _pattern = re.compile(r"^Nuke(\d+)\.(\d+)v(\d+)$")
    candidates = []
    try:
        for folder in program_files.iterdir():
            m = _pattern.match(folder.name)
            if m:
                major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
                exe = folder / f"Nuke{m.group(1)}.{m.group(2)}.exe"
                if exe.exists() and major < 17:
                    candidates.append(((major, minor, patch), exe))
    except OSError:
        pass
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

HIERO_EXECUTABLE = _find_latest_hiero() or r"C:\Program Files\Nuke15.1v5\Nuke15.1.exe"

# ---------------------------------------------------------------------------
# UI constants
# ---------------------------------------------------------------------------
APP_NAME = "OTIO Review Generator"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 650
