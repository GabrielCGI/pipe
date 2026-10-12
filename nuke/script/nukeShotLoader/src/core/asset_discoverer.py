"""Disk discovery of shot assets (plates, 3D/2D renders, rotos, cameras).

Uses os.scandir (no extra stat syscalls on network drives), stops at the
first matching file when only existence matters, and runs the five
top-level scans concurrently since they are purely I/O-bound.
"""

import concurrent.futures
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from .config import Config

_VERSION_RE = re.compile(Config.VERSION_PATTERN)
# "<stem>.<frame>.<ext>" — frame is 4+ digits.
FRAME_RE = re.compile(r'\.(\d{4,})\.(exr|dpx|jpg|jpeg|png|tif|tiff)$', re.IGNORECASE)
_IMAGE_EXTS = tuple(ext.lower() for ext in Config.IMAGE_EXTENSIONS)
_USD_EXTS = tuple(ext.lower() for ext in Config.USD_EXTENSIONS)
_IGNORE_SUFFIXES = frozenset(Config.IGNORE_VERSION_SUFFIXES)


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _iter_subdirs(path: str):
    """Yield (name, full_path) for each subdirectory; nothing on error."""
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_dir():
                        yield entry.name, entry.path
                except OSError:
                    continue
    except OSError:
        return


def _has_file_with_ext(folder: str, extensions: tuple) -> bool:
    try:
        with os.scandir(folder) as it:
            for entry in it:
                try:
                    if entry.is_file() and entry.name.lower().endswith(extensions):
                        return True
                except OSError:
                    continue
    except OSError:
        pass
    return False


def list_image_files(folder: str) -> List[str]:
    """Image file names in `folder` (listdir order), [] when unreadable."""
    try:
        return [f for f in os.listdir(folder) if f.lower().endswith(_IMAGE_EXTS)]
    except OSError:
        return []


def is_static_image(filename: str) -> bool:
    """True when the file name carries no frame number."""
    return not FRAME_RE.search(filename)


def to_sequence_pattern(filename: str) -> str:
    """'plate.1001.exr' -> 'plate.####.exr' (one '#' per frame digit)."""
    return FRAME_RE.sub(lambda m: f".{'#' * len(m.group(1))}.{m.group(2)}", filename)


def sequence_path(folder: str) -> Optional[str]:
    """Nuke file path for the images in `folder`: a '####' pattern for a
    sequence, the first file itself for a static image, None if empty."""
    images = sorted(list_image_files(folder))
    if not images:
        return None
    first = images[0]
    if is_static_image(first):
        print(f"[NukeNodeBuilder] Detected static image: {first}")
        return os.path.join(folder, first)
    pattern = to_sequence_pattern(first)
    print(f"[NukeNodeBuilder] Detected sequence: {pattern}")
    return os.path.join(folder, pattern)


_VERSION_TOKEN_RE = re.compile(r"v\d{3,4}", re.IGNORECASE)
_FRAME_PLACEHOLDER_RE = re.compile(r"#+|%0?\d*d")


def _file_identity(name: str) -> str:
    """File name with its version token and frame number / placeholder folded."""
    name = _FRAME_PLACEHOLDER_RE.sub("#", to_sequence_pattern(name))
    return _VERSION_TOKEN_RE.sub("v#", name.lower())


def matching_path(folder: str, current_name: str) -> Optional[str]:
    """Nuke file path in `folder` for the file currently named `current_name`
    (e.g. 'stmap_V.exr' stays the V map, 'x_v001.####.exr' -> 'x_v002.####.exr').
    Falls back to sequence_path() when nothing matches."""
    wanted = _file_identity(current_name)
    for name in sorted(list_image_files(folder)):
        if _file_identity(name) == wanted:
            return os.path.join(folder, name if is_static_image(name) else to_sequence_pattern(name))
    return sequence_path(folder)


def find_usd_file(folder: str) -> Optional[str]:
    try:
        for f in os.listdir(folder):
            if f.lower().endswith(_USD_EXTS):
                return os.path.join(folder, f)
    except OSError:
        pass
    return None


def frame_numbers(folder: str) -> Optional[Set[int]]:
    """Frame numbers present in `folder`, None when unreadable or empty.
    The full set (not just first/last) is needed to detect gaps."""
    frames = set()
    try:
        with os.scandir(folder) as it:
            for entry in it:
                try:
                    if not entry.is_file():
                        continue
                except OSError:
                    continue
                m = FRAME_RE.search(entry.name)
                if m:
                    frames.add(int(m.group(1)))
    except OSError as e:
        print(f"[AssetDiscoverer] Error scanning frames in {folder}: {e}")
        return None
    return frames or None


def frame_range(folder: str) -> Optional[Tuple[int, int]]:
    frames = frame_numbers(folder)
    return (min(frames), max(frames)) if frames else None


def folder_has_image(folder: str) -> bool:
    """Distinguishes a static-image folder (.psd, stMap.png) from an empty
    one — both have no frame numbers."""
    return _has_file_with_ext(folder, _IMAGE_EXTS)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

class AssetDiscoverer:
    """Discovers assets and their versions for a shot of a Prism project."""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or Config.DEFAULT_PROJECT_ROOT

    def shot_path(self, sequence: str, shot: str) -> str:
        return os.path.join(self.project_root, Config.SHOTS_PATH, sequence, shot)

    def discover_all_assets(self, sequence: str, shot: str) -> Dict[str, Dict]:
        """{"plates", "3d_renders", "2d_renders", "rotos", "cameras"} -> assets."""
        print(f"\n[AssetDiscoverer] Discovering assets for {sequence}/{shot}")
        tasks = {
            "plates": self.discover_plates,
            "3d_renders": self.discover_3d_renders,
            "2d_renders": self.discover_2d_renders,
            "rotos": self.discover_rotos,
            "cameras": self.discover_cameras,
        }
        result = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            futures = {key: pool.submit(fn, sequence, shot) for key, fn in tasks.items()}
            for key, future in futures.items():
                try:
                    result[key] = future.result()
                except Exception as e:
                    print(f"[AssetDiscoverer] {key} scan failed: {e}")
                    result[key] = {}
        print(f"[AssetDiscoverer] Total assets discovered: {sum(len(v) for v in result.values())}")
        return result

    def discover_plates(self, sequence: str, shot: str) -> Dict:
        """{"plate": {"v001": {"rgb": path}}, ...} — rotos are excluded."""
        base = os.path.join(self.shot_path(sequence, shot), Config.PLATES_PATH)
        if not os.path.isdir(base):
            print(f"[AssetDiscoverer] Plates path not found: {base}")
            return {}
        plates = {}
        for name, path in _iter_subdirs(base):
            if name in _IGNORE_SUFFIXES or name == Config.ROTO_FOLDER:
                continue
            versions = self.discover_versions(path)
            if versions:
                plates[name] = versions
                print(f"[AssetDiscoverer]   Found plate: {name} with {len(versions)} version(s)")
        return plates

    def discover_3d_renders(self, sequence: str, shot: str) -> Dict:
        return self._discover_render_passes(sequence, shot, Config.RENDERS_3D_PATH, "3D render")

    def discover_2d_renders(self, sequence: str, shot: str) -> Dict:
        return self._discover_render_passes(sequence, shot, Config.RENDERS_2D_PATH, "2D render")

    def _discover_render_passes(self, sequence, shot, rel_path, label) -> Dict:
        base = os.path.join(self.shot_path(sequence, shot), rel_path)
        if not os.path.isdir(base):
            print(f"[AssetDiscoverer] {label} path not found: {base}")
            return {}
        renders = {}
        for name, path in _iter_subdirs(base):
            if name.endswith(".json"):
                continue
            versions = self.discover_versions(path)
            if versions:
                renders[name] = versions
                print(f"[AssetDiscoverer]   Found {label}: {name} with {len(versions)} version(s)")
        return renders

    def discover_rotos(self, sequence: str, shot: str) -> Dict:
        """{"v001": {"rgb": path}, ...}"""
        base = os.path.join(self.shot_path(sequence, shot), Config.PLATES_PATH, Config.ROTO_FOLDER)
        if not os.path.isdir(base):
            print(f"[AssetDiscoverer] Roto path not found: {base}")
            return {}
        versions = self.discover_versions(base)
        if versions:
            print(f"[AssetDiscoverer]   Found roto with {len(versions)} version(s)")
        return versions

    def discover_cameras(self, sequence: str, shot: str) -> Dict:
        """{"layer_cam_camera": {"v001": folder}} — only the per-shot export."""
        base = os.path.join(self.shot_path(sequence, shot), Config.CAMERA_PATH)
        if not os.path.isdir(base):
            print(f"[AssetDiscoverer] Camera path not found: {base}")
            return {}
        cameras = {}
        for name, path in _iter_subdirs(base):
            if name != Config.CAMERA_FOLDER:
                continue
            versions = {
                v: v_path for v, v_path in _iter_subdirs(path)
                if _VERSION_RE.match(v) and _has_file_with_ext(v_path, _USD_EXTS)
            }
            if versions:
                cam_name = name.lstrip("_")
                cameras[cam_name] = versions
                print(f"[AssetDiscoverer]   Found camera: {cam_name} with {len(versions)} version(s)")
        return cameras

    def discover_versions(self, asset_path: str) -> Dict:
        """{"v001": {"rgb": path, "beauty": path}, ...} for an asset folder."""
        versions = {}
        for name, path in _iter_subdirs(asset_path):
            if any(suffix in name for suffix in _IGNORE_SUFFIXES):
                continue
            if not _VERSION_RE.match(name):
                continue
            layers = self._discover_layers(path)
            if layers:
                versions[name] = layers
        return versions

    @staticmethod
    def _discover_layers(version_path: str) -> Dict:
        """Layer folders (v001/beauty/*.exr) take priority; images directly
        in the version folder become a single "rgb" layer."""
        subdirs = []
        has_root_image = False
        try:
            with os.scandir(version_path) as it:
                for entry in it:
                    try:
                        if entry.is_dir():
                            if entry.name not in _IGNORE_SUFFIXES and not entry.name.startswith("_"):
                                subdirs.append((entry.name, entry.path))
                        elif entry.is_file() and entry.name.lower().endswith(_IMAGE_EXTS):
                            has_root_image = True
                    except OSError:
                        continue
        except OSError as e:
            print(f"[AssetDiscoverer] Error discovering layers in {version_path}: {e}")
            return {}

        if subdirs:
            return {name: path for name, path in subdirs if _has_file_with_ext(path, _IMAGE_EXTS)}
        if has_root_image:
            return {"rgb": version_path}
        return {}

    def asset_folder(self, sequence: str, shot: str, asset_type: str, asset_name: str) -> Optional[str]:
        """Folder holding the version folders of an asset (used for assets
        loaded from another shot)."""
        layout = {
            "Plate": (Config.PLATES_PATH, asset_name),
            "Roto": (Config.PLATES_PATH, Config.ROTO_FOLDER),
            "3D Render": (Config.RENDERS_3D_PATH, asset_name),
            "2D Render": (Config.RENDERS_2D_PATH, asset_name),
        }.get(asset_type)
        if layout is None:
            return None
        return os.path.join(self.shot_path(sequence, shot), *layout)
