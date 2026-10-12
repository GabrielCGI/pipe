"""Creates the Read / Camera3 nodes of loaded assets, their stamps and backdrops.

Layout — one backdrop per asset family, stacked and left-aligned:
    [3D RENDERS]
    [CAMERAS]
    [2D RENDERS]
    [PLATES]  [ROTOS]
Reads inside a backdrop form a grid of Config.READS_PER_ROW columns.
"""

import os
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

import nuke

from ..core.config import Config
from ..core import asset_discoverer as fs
from ..core import project
from ..core.versions import latest_version
from . import cameras as camera_files
from .asset_nodes import tag_as_loader_owned
from .stamps import create_stamp_pair
from .utils import center_under, scene_fps

Bounds = Tuple[int, int, int, int]  # x, y, w, h

# Label TCL evaluating to the version token of the node's current `file`,
# so a version change shows on the node without any resync.
_VERSION_LABEL_TCL = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"

_BACKDROPS = {  # discovery key -> (backdrop label, color key)
    "3d_renders": "3D RENDERS",
    "cameras": "CAMERAS",
    "2d_renders": "2D RENDERS",
    "plates": "PLATES",
    "rotos": "ROTOS",
}


@dataclass
class _ReadSpec:
    path: str                  # folder of a sequence, or a static image file
    node_name: str
    label: str
    stamp_title: str
    colorspace_key: str
    cleanup: str = ""          # "", "always" or "psd"
    static: bool = False
    pattern: Optional[str] = None  # explicit file name for stMap sequences


class NukeNodeBuilder:
    """Builds Nuke nodes for shot assets."""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or Config.DEFAULT_PROJECT_ROOT
        self.created_nodes: List = []
        self.created_backdrops: List = []
        self._colorspaces: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def load_assets(self, sequence: str, shot: str, assets: Dict,
                    asset_colorspaces: Optional[Dict] = None, project_root: Optional[str] = None):
        """Load every asset of `assets` (AssetDiscoverer layout) into the script."""
        print(f"\n[NukeNodeBuilder] Loading assets for {sequence}/{shot}")
        self.created_nodes.clear()
        self.created_backdrops.clear()
        self._colorspaces = asset_colorspaces or {}
        if project_root:
            self.project_root = project_root

        origin = (Config.START_X, Config.START_Y)
        x_gap = Config.BACKDROP_PADDING * 2
        y_gap = Config.BACKDROP_Y_GAP
        # Seed from existing backdrops so chaining works even for families
        # with nothing new to load.
        bounds = {key: self._existing_bounds(label) for key, label in _BACKDROPS.items()}

        def below(*refs):
            ref = next((b for b in refs if b), None)
            if not ref:
                return origin
            x = bounds["3d_renders"][0] if bounds["3d_renders"] else ref[0]
            return x, ref[1] + ref[3] + y_gap

        if assets.get("3d_renders"):
            self._load_family("3d_renders", self._render_specs(sequence, shot, assets["3d_renders"], "3D Render", "always"),
                              origin, bounds)
        if assets.get("cameras"):
            self._load_cameras(assets["cameras"], below(bounds["3d_renders"]), bounds)
        if assets.get("2d_renders"):
            self._load_family("2d_renders", self._render_specs(sequence, shot, assets["2d_renders"], "2D Render", "psd"),
                              below(bounds["cameras"], bounds["3d_renders"]), bounds)

        external = below(bounds["2d_renders"], bounds["cameras"], bounds["3d_renders"])
        if assets.get("plates"):
            self._load_family("plates", self._plate_specs(sequence, shot, assets["plates"]), external, bounds)
            if bounds["plates"]:
                plates = bounds["plates"]
                external = (plates[0] + plates[2] + x_gap, external[1])
        if assets.get("rotos"):
            self._load_family("rotos", self._roto_specs(sequence, shot, assets["rotos"]), external, bounds)

        self._normalize_layout()
        print(f"[NukeNodeBuilder] Loaded {len(self.created_nodes)} nodes")

    def update_node_version(self, node, version_folder: str,
                            frame_range: Optional[Tuple[int, int]] = None) -> bool:
        """Point a Read (image sequence) or Camera3 (USD) at another version folder."""
        try:
            if node.Class() == "Camera3":
                usd_file = fs.find_usd_file(version_folder)
                if not usd_file:
                    print(f"[NukeNodeBuilder] No USD file found in {version_folder}")
                    return False
                self._read_camera_file(node, usd_file)
                print(f"[NukeNodeBuilder] Updated camera {node.name()} to {usd_file}")
                return True

            current = os.path.basename((node['file'].value() or "").replace("\\", "/"))
            path = fs.matching_path(version_folder, current)
            if not path:
                print(f"[NukeNodeBuilder] Cannot construct path for {version_folder}")
                return False
            node['file'].setValue(path.replace("\\", "/"))
            if frame_range:
                node['first'].setValue(frame_range[0])
                node['last'].setValue(frame_range[1])
            print(f"[NukeNodeBuilder] Updated node {node.name()} to new version")
            return True
        except Exception as e:
            print(f"[NukeNodeBuilder] Error updating node version: {e}")
            return False

    def create_stamps(self, source, title: str, cleanup_in_chain: bool = False) -> list:
        offset = Config.ANCHOR_OFFSET_CLEANUP if cleanup_in_chain else Config.ANCHOR_OFFSET
        return create_stamp_pair(source, title, offset)

    # ------------------------------------------------------------------
    # Read specs per family
    # ------------------------------------------------------------------

    @staticmethod
    def _render_specs(sequence, shot, renders, asset_type, cleanup) -> Iterator[_ReadSpec]:
        """Latest version of each 3D/2D pass, one Read per layer. 3D renders
        always get an ILGC_ReadCleanup; 2D only for .psd paintovers."""
        for render_pass, versions in renders.items():
            version = latest_version(versions.keys())
            if not version:
                continue
            for layer, folder in versions[version].items():
                yield _ReadSpec(folder, f"{sequence}_{shot}_{render_pass}_{layer}", render_pass,
                                render_pass, f"{asset_type}_{render_pass}", cleanup)

    @classmethod
    def _plate_specs(cls, sequence, shot, plates) -> Iterator[_ReadSpec]:
        for plate_type, versions in plates.items():
            if plate_type == Config.STMAPS_FOLDER:
                yield from cls._stmap_specs(sequence, shot, versions)
                continue
            version = latest_version(versions.keys())
            if not version:
                continue
            for layer, folder in versions[version].items():
                yield _ReadSpec(folder, f"{sequence}_{shot}_{plate_type}_{layer}", plate_type,
                                plate_type, f"Plate_{plate_type}")

    @staticmethod
    def _stmap_specs(sequence, shot, versions) -> Iterator[_ReadSpec]:
        """stMaps are usually static U/V images: one Read per file of the
        latest version, then one per frame sequence if any."""
        print("[NukeNodeBuilder] Loading stMaps (static images)")
        version = latest_version(versions.keys())
        if not version:
            return
        for folder in versions[version].values():
            if not os.path.exists(folder):
                continue
            images = fs.list_image_files(folder)
            if not images:
                print(f"[NukeNodeBuilder] No image files found in {folder}")
                continue
            statics = [f for f in images if fs.is_static_image(f)]
            sequences = {}
            for f in images:
                m = fs.FRAME_RE.search(f)
                if m:
                    sequences.setdefault(f[:m.start()], f)
            print(f"[NukeNodeBuilder] Found {len(statics)} static image(s) and "
                  f"{len(images) - len(statics)} sequence file(s)")

            for image in sorted(statics):
                name = os.path.splitext(image)[0]
                yield _ReadSpec(os.path.join(folder, image), f"{sequence}_{shot}_stMap_{name}",
                                f"stMap\n{name}", f"stMap_{name}", "Plate_stMaps", static=True)
            for base, first_file in sequences.items():
                yield _ReadSpec(folder, f"{sequence}_{shot}_stMap_{base}", f"stMap\n{base}",
                                f"stMap_{base}", "Plate_stMaps", pattern=fs.to_sequence_pattern(first_file))

    @staticmethod
    def _roto_specs(sequence, shot, rotos) -> Iterator[_ReadSpec]:
        """Every roto version is loaded, not just the latest."""
        for version, layers in rotos.items():
            for layer, folder in layers.items():
                yield _ReadSpec(folder, f"{sequence}_{shot}_roto_{version}_{layer}", "roto",
                                f"Roto_{version}", f"Roto_{version}")

    # ------------------------------------------------------------------
    # Family loaders
    # ------------------------------------------------------------------

    def _load_family(self, key: str, specs, anchor, bounds):
        label = _BACKDROPS[key]
        print(f"[NukeNodeBuilder] Loading {label.lower()}")
        base_x, base_y, backdrop, count = self._resolve_slot(label, anchor)
        new_nodes = []
        for spec in specs:
            read = self._create_read(spec, self._grid_position(base_x, base_y, count))
            if read is None:
                continue
            self._apply_version_label(read, spec.label)
            new_nodes.append(read)
            self.created_nodes.append(read)

            wants_cleanup = spec.cleanup == "always" or (
                spec.cleanup == "psd" and (read['file'].value() or "").lower().endswith('.psd'))
            cleanup = self._insert_read_cleanup(read) if wants_cleanup else None
            if cleanup:
                new_nodes.append(cleanup)
            new_nodes.extend(self.create_stamps(cleanup or read, spec.stamp_title, bool(cleanup)))
            count += 1
        self._finalize_backdrop(key, backdrop, new_nodes, bounds)

    def _load_cameras(self, cameras: Dict, anchor, bounds):
        print(f"[NukeNodeBuilder] Loading {len(cameras)} camera(s)")
        self._set_project_fps()  # USD camera import depends on the scene FPS
        base_x, base_y, backdrop, count = self._resolve_slot(_BACKDROPS["cameras"], anchor)
        new_nodes = []
        for cam_name, versions in cameras.items():
            version = latest_version(versions.keys())
            if not version:
                continue
            usd_file = fs.find_usd_file(versions[version])
            if not usd_file:
                print(f"[NukeNodeBuilder] No USD file found in {versions[version]}")
                continue
            camera = self._create_camera(usd_file, self._grid_position(base_x, base_y, count))
            if camera is None:
                continue
            self._apply_version_label(camera, cam_name)
            new_nodes.append(camera)
            self.created_nodes.append(camera)
            new_nodes.extend(self.create_stamps(camera, "cam"))
            count += 1
        self._finalize_backdrop("cameras", backdrop, new_nodes, bounds)

    # ------------------------------------------------------------------
    # Node creation
    # ------------------------------------------------------------------

    def _create_read(self, spec: _ReadSpec, position: Tuple[int, int]):
        try:
            if spec.static:
                if not os.path.exists(spec.path):
                    print(f"[NukeNodeBuilder] Static image not found: {spec.path}")
                    return None
                file_value, frames = spec.path, None
            else:
                if spec.pattern:
                    file_value = os.path.join(spec.path, spec.pattern)
                else:
                    file_value = fs.sequence_path(spec.path)
                if not file_value:
                    print(f"[NukeNodeBuilder] No image sequence found in {spec.path}")
                    return None
                frames = fs.frame_range(spec.path)

            read = nuke.createNode("Read", inpanel=False)
            read.setName(spec.node_name, uncollide=True)
            read['file'].setValue(file_value.replace("\\", "/"))
            if read.knob('on_error') is not None:
                read['on_error'].setValue('black')
            # PSD paintovers are authored in Photoshop's working space: skip
            # the input transform instead of double-converting.
            if not spec.static and file_value.lower().endswith('.psd') and read.knob('raw') is not None:
                read['raw'].setValue(True)
            if frames:
                for knob, value in (("first", frames[0]), ("last", frames[1]),
                                    ("origfirst", frames[0]), ("origlast", frames[1])):
                    read[knob].setValue(value)
                print(f"[NukeNodeBuilder] Frame range: {frames[0]}-{frames[1]}")
            elif not spec.static:
                print("[NukeNodeBuilder] Warning: Could not detect frame range")
            colorspace = self._colorspaces.get(spec.colorspace_key)
            if colorspace:
                read['colorspace'].setValue(colorspace)
                print(f"[NukeNodeBuilder] Applied colorspace: {colorspace}")
            read.setXYpos(*position)
            tag_as_loader_owned(read)
            print(f"[NukeNodeBuilder] Created Read node: {spec.node_name}")
            return read
        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating Read node {spec.node_name}: {e}")
            return None

    def _create_camera(self, usd_file: str, position: Tuple[int, int]):
        try:
            camera = nuke.createNode("Camera3", inpanel=False)
            camera.setName(Config.CAMERA_NODE_NAME, uncollide=True)
            camera.setXYpos(*position)
            self._read_camera_file(camera, usd_file)
            print(f"[NukeNodeBuilder] Created Camera3 node: {Config.CAMERA_NODE_NAME}")
            return camera
        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating Camera3 node: {e}")
            return None

    def _read_camera_file(self, camera, usd_file: str):
        """Put the camera of `usd_file` into a Camera3: baked into its knobs
        by the Shot Loader itself, or by Nuke's import for a file the bake
        declines (see scene/cameras.py)."""
        try:
            camera_files.bake_file(camera, usd_file)
        except camera_files.NotBakeable as reason:
            print(f"[NukeNodeBuilder] {camera.name()}: {reason} — left to Nuke's own import")
            fps = scene_fps()
            if fps is None:
                fps = project.project_fps(self.project_root)
            camera_files.load_file(camera, usd_file, frame_rate=fps)

    def _set_project_fps(self):
        try:
            fps = project.project_fps(self.project_root)
            nuke.root()['fps'].setValue(fps)
            print(f"[NukeNodeBuilder] Set project FPS to {fps}")
        except Exception as e:
            print(f"[NukeNodeBuilder] Error setting project FPS: {e}")

    @staticmethod
    def _apply_version_label(node, prefix: str):
        if node.knob('label') is not None:
            node['label'].setValue(f"{prefix}\n{_VERSION_LABEL_TCL}")

    @staticmethod
    def _insert_read_cleanup(read):
        """ILGC_ReadCleanup wired under `read`, None when the gizmo isn't
        installed in this session."""
        try:
            cleanup = nuke.createNode(Config.READ_CLEANUP_GIZMO, inpanel=False)
        except Exception as e:
            print(f"[NukeNodeBuilder] {Config.READ_CLEANUP_GIZMO} gizmo not available: {e}")
            return None
        if cleanup is None:
            return None
        cleanup.setInput(0, read)
        # Clear the Read's postage-stamp thumbnail whatever its drawn height.
        center_under(cleanup, read, read.ypos() + (read.screenHeight() or 80) + 25)
        tag_as_loader_owned(cleanup)
        print(f"[NukeNodeBuilder] Inserted {Config.READ_CLEANUP_GIZMO} under {read.name()}")
        return cleanup

    # ------------------------------------------------------------------
    # Grid + backdrops
    # ------------------------------------------------------------------

    @staticmethod
    def _grid_position(base_x: int, base_y: int, index: int) -> Tuple[int, int]:
        col, row = index % Config.READS_PER_ROW, index // Config.READS_PER_ROW
        return base_x + col * Config.READ_COL_SPACING, base_y + row * Config.READ_ROW_HEIGHT

    def _resolve_slot(self, label: str, anchor):
        """(base_x, base_y, existing_backdrop, existing_grid_count). An
        existing backdrop resumes its grid after the nodes already in it."""
        backdrop = self._find_backdrop(label)
        if backdrop is None:
            return anchor[0], anchor[1], None, 0
        grid = [n for n in self._nodes_inside(backdrop) if n.Class() in ("Read", "Camera3")]
        if grid:
            return min(n.xpos() for n in grid), min(n.ypos() for n in grid), backdrop, len(grid)
        x, y, _, _ = _bounds(backdrop)
        return x + 50, y + 80, backdrop, 0

    def _finalize_backdrop(self, key: str, backdrop, new_nodes: List, bounds: Dict):
        """Grow an existing backdrop only on the edges new nodes stick out
        of, or create a fresh one around them. Updates bounds[key]."""
        if not new_nodes:
            return
        label = _BACKDROPS[key]
        min_x = min(n.xpos() for n in new_nodes)
        min_y = min(n.ypos() for n in new_nodes)
        max_x = max(n.xpos() + n.screenWidth() for n in new_nodes)
        max_y = max(n.ypos() + n.screenHeight() for n in new_nodes)

        if backdrop is not None:
            x, y, w, h = _bounds(backdrop)
            right, bottom = x + w, y + h
            if x <= min_x and max_x <= right and y <= min_y and max_y <= bottom:
                print(f"[NukeNodeBuilder] Backdrop already fits new content: {label}")
                bounds[key] = (x, y, w, h)
                return
            pad = Config.BACKDROP_PADDING
            x, y = min(x, min_x - pad), min(y, min_y - pad)
            right, bottom = max(right, max_x + pad), max(bottom, max_y + pad)
            _set_bounds(backdrop, x, y, right - x, bottom - y)
            print(f"[NukeNodeBuilder] Grew backdrop: {label}")
            bounds[key] = (x, y, right - x, bottom - y)
            return

        pad = Config.BACKDROP_PADDING
        rect = (min_x - pad, min_y - pad, (max_x - min_x) + 2 * pad, (max_y - min_y) + 2 * pad)
        try:
            backdrop = nuke.createNode("BackdropNode", inpanel=False)
            _set_bounds(backdrop, *rect)
            backdrop['tile_color'].setValue(Config.BACKDROP_COLORS[key])
            backdrop['label'].setValue(label)
            backdrop['note_font_size'].setValue(24)
            self.created_backdrops.append(backdrop)
            bounds[key] = rect
            print(f"[NukeNodeBuilder] Created backdrop: {label}")
        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating backdrop: {e}")

    @staticmethod
    def _find_backdrop(label: str):
        for node in nuke.allNodes("BackdropNode"):
            try:
                if node['label'].value() == label:
                    return node
            except Exception:
                pass
        return None

    def _existing_bounds(self, label: str) -> Optional[Bounds]:
        backdrop = self._find_backdrop(label)
        return _bounds(backdrop) if backdrop is not None else None

    @staticmethod
    def _nodes_inside(backdrop) -> List:
        """Non-backdrop nodes inside the backdrop (native getNodes when it
        returns something, else a top-left-corner hit test)."""
        try:
            nodes = [n for n in backdrop.getNodes() if n.Class() != "BackdropNode"]
            if nodes:
                return nodes
        except Exception:
            pass
        try:
            x, y, w, h = _bounds(backdrop)
        except Exception:
            return []
        return [n for n in nuke.allNodes()
                if n.Class() != "BackdropNode" and x <= n.xpos() <= x + w and y <= n.ypos() <= y + h]

    def _move_backdrop(self, backdrop, new_x: int, new_y: int, new_height: Optional[int] = None):
        """Move a backdrop and its content together (connections survive)."""
        x, y, _, _ = _bounds(backdrop)
        dx, dy = new_x - x, new_y - y
        if dx or dy:
            for node in self._nodes_inside(backdrop):
                node.setXYpos(node.xpos() + dx, node.ypos() + dy)
            backdrop['xpos'].setValue(new_x)
            backdrop['ypos'].setValue(new_y)
        if new_height is not None:
            backdrop['bdheight'].setValue(new_height)

    def _normalize_layout(self):
        """Re-stack the backdrops created by this load under the topmost
        one; ROTOS sits right of PLATES with the same y and height.
        Backdrops that already existed never move."""
        backdrops = {key: self._find_backdrop(label) for key, label in _BACKDROPS.items()}
        chain = [backdrops[k] for k in ("3d_renders", "cameras", "2d_renders", "plates") if backdrops[k]]
        if chain:
            left_x = _bounds(chain[0])[0]
            previous = _bounds(chain[0])
            for backdrop in chain[1:]:
                if backdrop in self.created_backdrops:
                    self._move_backdrop(backdrop, left_x, previous[1] + previous[3] + Config.BACKDROP_Y_GAP)
                previous = _bounds(backdrop)

        rotos, plates = backdrops["rotos"], backdrops["plates"]
        if rotos and plates and rotos in self.created_backdrops:
            px, py, pw, ph = _bounds(plates)
            self._move_backdrop(rotos, px + pw + Config.BACKDROP_PADDING * 2, py, new_height=ph)


def _bounds(backdrop) -> Bounds:
    return (int(backdrop['xpos'].value()), int(backdrop['ypos'].value()),
            int(backdrop['bdwidth'].value()), int(backdrop['bdheight'].value()))


def _set_bounds(backdrop, x, y, w, h):
    backdrop['xpos'].setValue(x)
    backdrop['ypos'].setValue(y)
    backdrop['bdwidth'].setValue(w)
    backdrop['bdheight'].setValue(h)
