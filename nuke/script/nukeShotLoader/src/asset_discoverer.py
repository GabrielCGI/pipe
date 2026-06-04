"""
Asset Discoverer
Discovers all available assets for a shot: plates, 3D renders, cameras, rotos.
Scans filesystem and detects all available versions.

Performance notes:
- Uses os.scandir() instead of listdir+stat to avoid extra syscalls on network drives.
- _contains_*_files helpers return on the first matching file (no full listing).
- discover_all_assets() runs the 5 top-level scans concurrently (I/O-bound).
"""

import os
import re
import concurrent.futures
from typing import Dict, Optional, Tuple
from .config import Config


# Precompiled regexes and tuple constants (built once at import time)
_VERSION_RE = re.compile(Config.VERSION_PATTERN)
_FRAME_RE = re.compile(r'\.(\d{4,})\.(exr|dpx|jpg|jpeg|png|tif|tiff)$', re.IGNORECASE)
_IMAGE_EXTS = tuple(ext.lower() for ext in Config.IMAGE_EXTENSIONS)
_USD_EXTS = tuple(ext.lower() for ext in Config.USD_EXTENSIONS)
_IGNORE_SUFFIXES = frozenset(Config.IGNORE_VERSION_SUFFIXES)


def _iter_subdirs(path: str):
    """Yield (name, full_path) for each subdirectory. Empty on error."""
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_dir():
                        yield entry.name, entry.path
                except OSError:
                    continue
    except (OSError, PermissionError):
        return


def _folder_has_file_with_ext(folder_path: str, extensions: tuple) -> bool:
    """Return True at the first file matching any extension. No full listing."""
    try:
        with os.scandir(folder_path) as it:
            for entry in it:
                try:
                    if entry.is_file() and entry.name.lower().endswith(extensions):
                        return True
                except OSError:
                    continue
    except (OSError, PermissionError):
        pass
    return False


class AssetDiscoverer:
    """Discovers assets and their versions for a given shot"""

    def __init__(self, project_root: str = None):
        """
        Initialize asset discoverer.

        Args:
            project_root (str): Path to Prism project root
        """
        self.project_root = project_root or Config.DEFAULT_PROJECT_ROOT

    def discover_all_assets(self, sequence: str, shot: str) -> Dict:
        """
        Discover all assets for a shot (5 scans run concurrently).

        Args:
            sequence (str): Sequence name
            shot (str): Shot name

        Returns:
            Dict: {
                "plates": {...},
                "3d_renders": {...},
                "2d_renders": {...},
                "rotos": {...},
                "cameras": {...}
            }
        """
        print(f"\n[AssetDiscoverer] Discovering assets for {sequence}/{shot}")

        tasks = {
            "plates": self.discover_plates,
            "3d_renders": self.discover_3d_renders,
            "2d_renders": self.discover_2d_renders,
            "rotos": self.discover_rotos,
            "cameras": self.discover_cameras,
        }

        result = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {key: executor.submit(fn, sequence, shot) for key, fn in tasks.items()}
            for key, future in futures.items():
                try:
                    result[key] = future.result()
                except Exception as e:
                    print(f"[AssetDiscoverer] {key} scan failed: {e}")
                    result[key] = {}

        total_assets = sum(len(result[k]) for k in result)
        print(f"[AssetDiscoverer] Total assets discovered: {total_assets}")

        return result

    def discover_plates(self, sequence: str, shot: str) -> Dict:
        """
        Discover all plate types and versions.

        Returns:
            Dict: {"plate": {"v001": {"rgb": "path"}}, "plateDenoised": {...}, ...}
        """
        plates_base = os.path.join(self._get_shot_path(sequence, shot), Config.PLATES_PATH)

        if not os.path.isdir(plates_base):
            print(f"[AssetDiscoverer] Plates path not found: {plates_base}")
            return {}

        plates = {}
        try:
            for plate_type, plate_path in _iter_subdirs(plates_base):
                # Skip known non-plate folders and roto (handled separately)
                if plate_type in _IGNORE_SUFFIXES or plate_type == "roto":
                    continue

                versions = self._discover_versions_with_layers(plate_path)
                if versions:
                    plates[plate_type] = versions
                    print(f"[AssetDiscoverer]   Found plate: {plate_type} with {len(versions)} version(s)")
        except Exception as e:
            print(f"[AssetDiscoverer] Error discovering plates: {e}")

        return plates

    def discover_3d_renders(self, sequence: str, shot: str) -> Dict:
        """
        Discover all 3D render passes and versions.

        Returns:
            Dict: {"CHAR": {"v001": {"beauty": "path"}}, ...}
        """
        renders_base = os.path.join(self._get_shot_path(sequence, shot), Config.RENDERS_3D_PATH)

        if not os.path.isdir(renders_base):
            print(f"[AssetDiscoverer] 3D renders path not found: {renders_base}")
            return {}

        return self._discover_render_passes(renders_base, label="3D render")

    def discover_2d_renders(self, sequence: str, shot: str) -> Dict:
        """
        Discover all 2D render passes and versions.

        Returns:
            Dict: {"comp": {"v001": {"rgb": "path"}}, ...}
        """
        renders_base = os.path.join(self._get_shot_path(sequence, shot), Config.RENDERS_2D_PATH)

        if not os.path.isdir(renders_base):
            print(f"[AssetDiscoverer] 2D renders path not found: {renders_base}")
            return {}

        return self._discover_render_passes(renders_base, label="2D render")

    def _discover_render_passes(self, renders_base: str, label: str) -> Dict:
        """Shared implementation for 3D / 2D render pass discovery."""
        renders = {}
        try:
            for render_pass, render_path in _iter_subdirs(renders_base):
                if render_pass.endswith(".json"):
                    continue

                versions = self._discover_versions_with_layers(render_path)
                if versions:
                    renders[render_pass] = versions
                    print(f"[AssetDiscoverer]   Found {label}: {render_pass} with {len(versions)} version(s)")
        except Exception as e:
            print(f"[AssetDiscoverer] Error discovering {label}s: {e}")
        return renders

    def discover_rotos(self, sequence: str, shot: str) -> Dict:
        """
        Discover roto assets.

        Returns:
            Dict: {"v001": {"rgb": "path/to/files"}, ...}
        """
        roto_base = os.path.join(self._get_shot_path(sequence, shot), Config.PLATES_PATH, "roto")

        if not os.path.isdir(roto_base):
            print(f"[AssetDiscoverer] Roto path not found: {roto_base}")
            return {}

        versions = self._discover_versions_with_layers(roto_base)
        if versions:
            print(f"[AssetDiscoverer]   Found roto with {len(versions)} version(s)")
        return versions

    def discover_cameras(self, sequence: str, shot: str) -> Dict:
        """
        Discover camera USD files.

        Returns:
            Dict: {"lay_camera": {"v001": "path/to/v001", ...}}
        """
        camera_base = os.path.join(self._get_shot_path(sequence, shot), Config.CAMERA_PATH)

        if not os.path.isdir(camera_base):
            print(f"[AssetDiscoverer] Camera path not found: {camera_base}")
            return {}

        cameras = {}
        try:
            for cam_folder, cam_path in _iter_subdirs(camera_base):
                # Only load layout camera (_layer_lay_camera)
                if cam_folder != "_layer_lay_camera":
                    continue

                cam_name = cam_folder.lstrip("_")
                versions = self._discover_camera_versions(cam_path)
                if versions:
                    cameras[cam_name] = versions
                    print(f"[AssetDiscoverer]   Found camera: {cam_name} with {len(versions)} version(s)")
        except Exception as e:
            print(f"[AssetDiscoverer] Error discovering cameras: {e}")

        return cameras

    def _discover_versions_with_layers(self, asset_path: str) -> Dict:
        """
        Discover all versions and their layers for an asset.

        Returns:
            Dict: {"v001": {"rgb": "path", "beauty": "path"}, ...}
        """
        versions = {}
        try:
            for name, item_path in _iter_subdirs(asset_path):
                # Skip ignored suffixes
                if any(suffix in name for suffix in _IGNORE_SUFFIXES):
                    continue

                # Must match version pattern (e.g. v001)
                if not _VERSION_RE.match(name):
                    continue

                layers = self._discover_layers(item_path)
                if layers:
                    versions[name] = layers
        except Exception as e:
            print(f"[AssetDiscoverer] Error discovering versions in {asset_path}: {e}")

        return versions

    def _discover_layers(self, version_path: str) -> Dict:
        """
        Discover layers in a version folder (single-pass).

        Supports two structures:
        - With layers:    v001/rgb/files.exr, v001/beauty/files.exr
        - Without layers: v001/files.exr (auto-creates "rgb" layer pointing to v001)

        Returns:
            Dict: {"rgb": "path/to/sequence", ...}
        """
        candidate_subdirs = []  # [(name, path), ...] — potential layer folders
        has_image_at_root = False

        try:
            with os.scandir(version_path) as it:
                for entry in it:
                    try:
                        name = entry.name
                        if entry.is_dir():
                            if name in _IGNORE_SUFFIXES or name.startswith("_"):
                                continue
                            candidate_subdirs.append((name, entry.path))
                        elif entry.is_file():
                            if name.lower().endswith(_IMAGE_EXTS):
                                has_image_at_root = True
                    except OSError:
                        continue
        except (OSError, PermissionError) as e:
            print(f"[AssetDiscoverer] Error discovering layers in {version_path}: {e}")
            return {}

        layers = {}

        # Case 1: layer subfolders take priority
        if candidate_subdirs:
            for name, sub_path in candidate_subdirs:
                if _folder_has_file_with_ext(sub_path, _IMAGE_EXTS):
                    layers[name] = sub_path
        # Case 2: image files directly at version root
        elif has_image_at_root:
            layers["rgb"] = version_path

        return layers

    def _discover_camera_versions(self, camera_path: str) -> Dict:
        """
        Discover camera USD file versions.

        Returns:
            Dict: {"v001": "path/to/v001", ...}
        """
        versions = {}
        try:
            for name, item_path in _iter_subdirs(camera_path):
                if not _VERSION_RE.match(name):
                    continue
                if _folder_has_file_with_ext(item_path, _USD_EXTS):
                    versions[name] = item_path
        except Exception as e:
            print(f"[AssetDiscoverer] Error discovering camera versions: {e}")

        return versions

    def _get_shot_path(self, sequence: str, shot: str) -> str:
        """Get full path to shot folder."""
        return os.path.join(
            self.project_root,
            Config.SHOTS_PATH,
            sequence,
            shot
        )

    def get_frame_numbers_from_files(self, folder_path: str) -> Optional[set]:
        """
        Return the set of frame numbers present in `folder_path`, or None if
        the folder can't be read. Callers needing only (first, last) should
        use `get_frame_range_from_files`; the full set is needed to detect
        gaps (e.g. first/middle/last preview renders that look contiguous
        from the endpoints alone).
        """
        frames = set()
        try:
            with os.scandir(folder_path) as it:
                for entry in it:
                    try:
                        if not entry.is_file():
                            continue
                    except OSError:
                        continue
                    match = _FRAME_RE.search(entry.name)
                    if match:
                        frames.add(int(match.group(1)))
        except (OSError, PermissionError) as e:
            print(f"[AssetDiscoverer] Error scanning frames in {folder_path}: {e}")
            return None

        return frames if frames else None

    def get_frame_range_from_files(self, folder_path: str) -> Optional[Tuple[int, int]]:
        """
        Detect (first, last) frame range by scanning image files in a folder.
        Returns None when no frame-numbered files are present.
        """
        frames = self.get_frame_numbers_from_files(folder_path)
        if not frames:
            return None
        return (min(frames), max(frames))
