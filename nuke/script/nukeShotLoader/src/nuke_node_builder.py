"""
Nuke Node Builder
Creates and manages Nuke nodes for shot assets.
Handles Read nodes, Camera nodes, backdrops, and Stamps integration.
"""

import os
import re
import nuke
from typing import Dict, List, Optional, Tuple
from .config import Config
from .positioning_manager import PositioningManager
from .stamps_integration import get_stamps_integration
from .version_utils import latest_version as _latest


class NukeNodeBuilder:
    """Builds Nuke nodes for shot assets."""

    def __init__(self):
        """Initialize node builder."""
        self.positioning = PositioningManager()
        self.stamps = get_stamps_integration()
        self.created_nodes = []
        self.created_backdrops = []
        self.asset_colorspaces = {}
        self.camera_configs = {}
        self.project_root = Config.DEFAULT_PROJECT_ROOT

        # Set by _create_backdrop, read by load_assets to chain slot positions.
        self._last_backdrop_bounds = None

    def load_assets(
        self,
        sequence: str,
        shot: str,
        assets: Dict,
        asset_colorspaces: Optional[Dict] = None,
        project_root: Optional[str] = None,
        camera_configs: Optional[Dict] = None,
    ):
        """
        Load all selected assets into Nuke.

        Args:
            sequence (str): Sequence name
            shot (str): Shot name
            assets (Dict): Assets dict from AssetDiscoverer
            asset_colorspaces (Optional[Dict]): Colorspace overrides per asset
            project_root (Optional[str]): Prism project root path
            camera_configs (Optional[Dict]): Per-camera config, keyed by cam_name:
                {"node_name": <str>, "prim_path": <str>}
        """
        print(f"\n[NukeNodeBuilder] Loading assets for {sequence}/{shot}")

        self.positioning.reset()
        self.created_nodes.clear()
        self.created_backdrops.clear()

        # Store colorspaces and project root for access by loading methods
        self.asset_colorspaces = asset_colorspaces or {}
        self.camera_configs = camera_configs or {}
        if project_root:
            self.project_root = project_root

        # Layout:
        #   [3D Renders]
        #   [Cameras]
        #   [2D Renders]
        #   [Plates]   [Rotos]
        origin_x = self.positioning.start_x
        origin_y = self.positioning.start_y

        x_gap = Config.BACKDROP_PADDING * 2
        y_gap = 50  # tight vertical spacing between stacked backdrops

        # Seed slot bounds from any pre-existing backdrops so layout chaining
        # works even when a slot has no new items to load this run.
        bounds_3d = self._get_existing_backdrop_bounds("3D RENDERS")
        bounds_cam = self._get_existing_backdrop_bounds("CAMERAS")
        bounds_2d = self._get_existing_backdrop_bounds("2D RENDERS")
        bounds_plates = self._get_existing_backdrop_bounds("PLATES")
        bounds_rotos = self._get_existing_backdrop_bounds("ROTOS")

        # Vertical stack: 3D → Camera → 2D → Plates, all left-aligned with 3D.
        # Rotos sits to the right of Plates.
        # Slot 1: 3D Renders — top-left
        if assets.get("3d_renders"):
            self.positioning.set_anchor(origin_x, origin_y)
            self._load_3d_renders(sequence, shot, assets["3d_renders"])
            if self._last_backdrop_bounds:
                bounds_3d = self._last_backdrop_bounds

        # Slot 2: Camera — below 3D, left-aligned (or origin if no 3D)
        if assets.get("cameras"):
            if bounds_3d:
                cam_x = bounds_3d[0]
                cam_y = bounds_3d[1] + bounds_3d[3] + y_gap
            else:
                cam_x, cam_y = origin_x, origin_y
            self.positioning.set_anchor(cam_x, cam_y)
            self._load_cameras(sequence, shot, assets["cameras"])
            if self._last_backdrop_bounds:
                bounds_cam = self._last_backdrop_bounds

        # Slot 3: 2D Renders — below Camera (or below 3D, or origin)
        if assets.get("2d_renders"):
            prev = bounds_cam or bounds_3d
            if prev:
                twod_x = bounds_3d[0] if bounds_3d else prev[0]
                twod_y = prev[1] + prev[3] + y_gap
            else:
                twod_x, twod_y = origin_x, origin_y
            self.positioning.set_anchor(twod_x, twod_y)
            self._load_2d_renders(sequence, shot, assets["2d_renders"])
            if self._last_backdrop_bounds:
                bounds_2d = self._last_backdrop_bounds

        # Slot 4: External (plates + rotos) — below 2D, fallback below Cam / 3D.
        ref = bounds_2d or bounds_cam or bounds_3d
        if ref:
            ext_x = bounds_3d[0] if bounds_3d else ref[0]
            ext_y = ref[1] + ref[3] + y_gap
        else:
            ext_x, ext_y = origin_x, origin_y

        if assets.get("plates"):
            self.positioning.set_anchor(ext_x, ext_y)
            self._load_plates(sequence, shot, assets["plates"])
            if self._last_backdrop_bounds:
                bounds_plates = self._last_backdrop_bounds
            if bounds_plates:
                # Place rotos to the right of plates in the same row
                ext_x = bounds_plates[0] + bounds_plates[2] + x_gap

        if assets.get("rotos"):
            self.positioning.set_anchor(ext_x, ext_y)
            self._load_rotos(sequence, shot, assets["rotos"])
            if self._last_backdrop_bounds:
                bounds_rotos = self._last_backdrop_bounds

        # Reconcile layout: enforce Camera/2D/External alignment with 3D.
        self._normalize_layout()

        print(f"[NukeNodeBuilder] Loaded {len(self.created_nodes)} nodes")

    def _load_plates(self, sequence: str, shot: str, plates: Dict):
        """Load plate assets."""
        if not plates:
            return

        print(f"[NukeNodeBuilder] Loading {len(plates)} plate(s)")

        backdrop_label = "PLATES"
        base_x, base_y, existing_backdrop, existing_nodes, read_count = self._resolve_slot_anchor(backdrop_label)
        nodes_in_group = []
        self._read_count = read_count

        for plate_type, versions in plates.items():
            # Special handling for stMaps: load all files
            if plate_type == "stMaps":
                self._load_stmaps(sequence, shot, versions, base_x, base_y, nodes_in_group)
                continue

            # Get latest version
            latest_version = _latest(versions.keys())
            if not latest_version:
                continue

            layers = versions[latest_version]

            # Create Read node for each layer
            for layer_name, layer_path in layers.items():
                node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

                # Get colorspace for this asset
                colorspace_key = f"Plate_{plate_type}"
                colorspace = self.asset_colorspaces.get(colorspace_key)

                read_node = self._create_read_node_for_sequence(
                    file_path=layer_path,
                    node_name=f"{sequence}_{shot}_{plate_type}_{layer_name}",
                    position=(node_x, node_y),
                    colorspace=colorspace
                )

                if read_node:
                    version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                    label_text = f"{plate_type}\n" + version_tcl
                    read_node['label'].setValue(label_text)
                    nodes_in_group.append(read_node)
                    self.created_nodes.append(read_node)

                    # Create stamp with short name
                    stamp_name = plate_type  # Simple name: "plate", "plateDenoised", etc.
                    stamps = self._create_stamp_for_node(read_node, stamp_name)
                    # Add stamps to nodes_in_group so they're included in backdrop bounds
                    nodes_in_group.extend(stamps)
                    self._read_count += 1

        self._finalize_backdrop(
            existing_backdrop,
            existing_nodes,
            nodes_in_group,
            backdrop_label,
            Config.BACKDROP_COLORS["plates"],
        )

    def _load_3d_renders(self, sequence: str, shot: str, renders: Dict):
        """Load 3D render assets."""
        if not renders:
            return

        print(f"[NukeNodeBuilder] Loading {len(renders)} 3D render(s)")

        backdrop_label = "3D RENDERS"
        base_x, base_y, existing_backdrop, existing_nodes, read_count = self._resolve_slot_anchor(backdrop_label)
        nodes_in_group = []
        self._read_count = read_count

        for render_pass, versions in renders.items():
            # Get latest version
            latest_version = _latest(versions.keys())
            if not latest_version:
                continue

            layers = versions[latest_version]

            # Create Read node for each layer
            for layer_name, layer_path in layers.items():
                node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

                # Get colorspace for this asset
                colorspace_key = f"3D Render_{render_pass}"
                colorspace = self.asset_colorspaces.get(colorspace_key)

                read_node = self._create_read_node_for_sequence(
                    file_path=layer_path,
                    node_name=f"{sequence}_{shot}_{render_pass}_{layer_name}",
                    position=(node_x, node_y),
                    colorspace=colorspace
                )

                if read_node:
                    version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                    label_text = f"{render_pass}\n" + version_tcl
                    read_node['label'].setValue(label_text)
                    nodes_in_group.append(read_node)
                    self.created_nodes.append(read_node)

                    # Insert pipeline cleanup gizmo between the Read and the
                    # anchor stamp. Falls back to the Read if the gizmo isn't
                    # installed in this Nuke session. Not added to created_nodes
                    # so the load summary counts assets, not helper nodes.
                    cleanup = self._insert_read_cleanup(read_node)
                    if cleanup:
                        nodes_in_group.append(cleanup)
                        stamp_source = cleanup
                    else:
                        stamp_source = read_node

                    # Create stamp with short name (render pass name).
                    # When a cleanup gizmo sits between Read and anchor, shrink
                    # the anchor offset by 25 so the chain stays compact.
                    stamp_name = render_pass  # Simple name: "CHAR", "BG", etc.
                    anchor_offset = 50 if cleanup else 150
                    stamps = self._create_stamp_for_node(stamp_source, stamp_name, anchor_y_offset=anchor_offset)
                    # Add stamps to nodes_in_group so they're included in backdrop bounds
                    nodes_in_group.extend(stamps)
                    self._read_count += 1

        self._finalize_backdrop(
            existing_backdrop,
            existing_nodes,
            nodes_in_group,
            backdrop_label,
            Config.BACKDROP_COLORS["3d_renders"],
        )

    def _load_2d_renders(self, sequence: str, shot: str, renders: Dict):
        """Load 2D render assets."""
        if not renders:
            return

        print(f"[NukeNodeBuilder] Loading {len(renders)} 2D render(s)")

        backdrop_label = "2D RENDERS"
        base_x, base_y, existing_backdrop, existing_nodes, read_count = self._resolve_slot_anchor(backdrop_label)
        nodes_in_group = []
        self._read_count = read_count

        for render_pass, versions in renders.items():
            # Get latest version
            latest_version = _latest(versions.keys())
            if not latest_version:
                continue

            layers = versions[latest_version]

            # Create Read node for each layer
            for layer_name, layer_path in layers.items():
                node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

                # Get colorspace for this asset
                colorspace_key = f"2D Render_{render_pass}"
                colorspace = self.asset_colorspaces.get(colorspace_key)

                read_node = self._create_read_node_for_sequence(
                    file_path=layer_path,
                    node_name=f"{sequence}_{shot}_{render_pass}_{layer_name}",
                    position=(node_x, node_y),
                    colorspace=colorspace
                )

                if read_node:
                    version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                    label_text = f"{render_pass}\n" + version_tcl
                    read_node['label'].setValue(label_text)
                    nodes_in_group.append(read_node)
                    self.created_nodes.append(read_node)

                    # Create stamp with short name (render pass name)
                    stamp_name = render_pass
                    stamps = self._create_stamp_for_node(read_node, stamp_name)
                    nodes_in_group.extend(stamps)
                    self._read_count += 1

        self._finalize_backdrop(
            existing_backdrop,
            existing_nodes,
            nodes_in_group,
            backdrop_label,
            Config.BACKDROP_COLORS["2d_renders"],
        )

    def _load_rotos(self, sequence: str, shot: str, rotos: Dict):
        """Load roto assets - ALL VERSIONS."""
        if not rotos:
            return

        print(f"[NukeNodeBuilder] Loading roto (all {len(rotos)} version(s))")

        backdrop_label = "ROTOS"
        base_x, base_y, existing_backdrop, existing_nodes, read_count = self._resolve_slot_anchor(backdrop_label)
        nodes_in_group = []
        self._read_count = read_count

        # Load ALL versions, not just the latest
        for version, layers in rotos.items():
            # Create Read node for each layer in this version
            for layer_name, layer_path in layers.items():
                node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

                # Get colorspace for this asset
                colorspace_key = f"Roto_{version}"  # Rotos are keyed by version
                colorspace = self.asset_colorspaces.get(colorspace_key)

                read_node = self._create_read_node_for_sequence(
                    file_path=layer_path,
                    node_name=f"{sequence}_{shot}_roto_{version}_{layer_name}",
                    position=(node_x, node_y),
                    colorspace=colorspace
                )

                if read_node:
                    version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                    label_text = f"roto\n" + version_tcl
                    read_node['label'].setValue(label_text)
                    nodes_in_group.append(read_node)
                    self.created_nodes.append(read_node)

                    # Create stamp with short name
                    stamp_name = f"Roto_{version}"  # e.g., "Roto_v001", "Roto_v002"
                    stamps = self._create_stamp_for_node(read_node, stamp_name)
                    # Add stamps to nodes_in_group so they're included in backdrop bounds
                    nodes_in_group.extend(stamps)
                    self._read_count += 1

        self._finalize_backdrop(
            existing_backdrop,
            existing_nodes,
            nodes_in_group,
            backdrop_label,
            Config.BACKDROP_COLORS["rotos"],
        )

    def _load_cameras(self, sequence: str, shot: str, cameras: Dict):
        """Load camera USD assets."""
        if not cameras:
            return

        print(f"[NukeNodeBuilder] Loading {len(cameras)} camera(s)")

        # Set FPS from Prism project before importing cameras
        self._set_project_fps()

        backdrop_label = "CAMERAS"
        base_x, base_y, existing_backdrop, existing_nodes, read_count = self._resolve_slot_anchor(backdrop_label)
        nodes_in_group = []
        self._read_count = read_count

        for cam_name, versions in cameras.items():
            # Get latest version
            latest_version = _latest(versions.keys())
            if not latest_version:
                continue

            cam_path = versions[latest_version]

            # Find USD file in the version folder
            usd_file = self._find_usd_file(cam_path)
            if not usd_file:
                print(f"[NukeNodeBuilder] No USD file found in {cam_path}")
                continue

            node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

            cam_cfg = self.camera_configs.get(cam_name, {})
            custom_node_name = cam_cfg.get("node_name") or f"{sequence}_{shot}_{cam_name}"
            prim_path = cam_cfg.get("prim_path") or None

            # Create Camera4 node with USD import
            camera_node = self._create_camera_node(
                usd_file=usd_file,
                node_name=custom_node_name,
                position=(node_x, node_y),
                prim_path=prim_path,
            )

            if camera_node:
                version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                label_text = f"{cam_name}\n" + version_tcl
                camera_node['label'].setValue(label_text)
                nodes_in_group.append(camera_node)
                self.created_nodes.append(camera_node)

                # Same anchor+wired flow as Reads — Stamps now types Camera4
                # natively, and passing the title at creation skips the
                # "update linked stamps?" prompt entirely.
                stamps = self._create_stamp_for_node(camera_node, stamp_name="cam")
                nodes_in_group.extend(stamps)
                self._read_count += 1

        self._finalize_backdrop(
            existing_backdrop,
            existing_nodes,
            nodes_in_group,
            backdrop_label,
            Config.BACKDROP_COLORS["cameras"],
        )

    def _create_read_node_for_sequence(
        self,
        file_path: str,
        node_name: str,
        position: Tuple[int, int],
        colorspace: Optional[str] = None
    ):
        """
        Create a Read node for an image sequence.
        Frame range is automatically detected from files.
        Colorspace is left to Nuke's default detection unless specified.

        Args:
            file_path (str): Path to sequence folder
            node_name (str): Name for the node
            position (Tuple[int, int]): Node position
            colorspace (Optional[str]): Colorspace override (None = auto-detect)

        Returns:
            Read node or None
        """
        try:
            # Find image files and construct path with ####
            sequence_path = self._construct_sequence_path(file_path)
            if not sequence_path:
                print(f"[NukeNodeBuilder] No image sequence found in {file_path}")
                return None

            # Detect frame range from files
            from .asset_discoverer import AssetDiscoverer
            discoverer = AssetDiscoverer()
            frame_range = discoverer.get_frame_range_from_files(file_path)

            # Create Read node
            read_node = nuke.createNode("Read", inpanel=False)
            read_node.setName(node_name, uncollide=True)
            read_node['file'].setValue(sequence_path.replace("\\", "/"))
            if 'on_error' in read_node.knobs():
                read_node['on_error'].setValue('black')

            # Set frame range from detected files
            if frame_range:
                read_node['first'].setValue(frame_range[0])
                read_node['last'].setValue(frame_range[1])
                read_node['origfirst'].setValue(frame_range[0])
                read_node['origlast'].setValue(frame_range[1])
                print(f"[NukeNodeBuilder] Frame range: {frame_range[0]}-{frame_range[1]}")
            else:
                print(f"[NukeNodeBuilder] Warning: Could not detect frame range")

            # Apply colorspace if specified
            if colorspace:
                read_node['colorspace'].setValue(colorspace)
                print(f"[NukeNodeBuilder] Applied colorspace: {colorspace}")

            # Set position
            read_node.setXYpos(position[0], position[1])

            self._tag_as_loader_owned(read_node)

            print(f"[NukeNodeBuilder] Created Read node: {node_name}")
            return read_node

        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating Read node: {e}")
            return None

    def _create_read_node_for_static_image(
        self,
        file_path: str,
        node_name: str,
        position: Tuple[int, int],
        colorspace: Optional[str] = None
    ):
        """
        Create a Read node for a static image (single frame, no sequence).

        Args:
            file_path (str): Full path to the static image file
            node_name (str): Name for the node
            position (Tuple[int, int]): Node position
            colorspace (Optional[str]): Colorspace override (None = auto-detect)

        Returns:
            Read node or None
        """
        try:
            if not os.path.exists(file_path):
                print(f"[NukeNodeBuilder] Static image not found: {file_path}")
                return None

            # Create Read node
            read_node = nuke.createNode("Read", inpanel=False)
            read_node.setName(node_name, uncollide=True)
            read_node['file'].setValue(file_path.replace("\\", "/"))
            if 'on_error' in read_node.knobs():
                read_node['on_error'].setValue('black')

            # For static images, no frame range to set
            # Nuke will handle it as a single-frame image

            # Apply colorspace if specified
            if colorspace:
                read_node['colorspace'].setValue(colorspace)
                print(f"[NukeNodeBuilder] Applied colorspace: {colorspace}")

            # Set position
            read_node.setXYpos(position[0], position[1])

            self._tag_as_loader_owned(read_node)

            print(f"[NukeNodeBuilder] Created Read node for static image: {node_name}")
            return read_node

        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating Read node for static image: {e}")
            return None

    def _resolve_scene_fps(self) -> float:
        """Return the current Nuke scene FPS, falling back to the project
        default from pipeline.json if the scene knob is unreadable."""
        try:
            return float(nuke.root()['fps'].value())
        except Exception as fps_err:
            print(f"[NukeNodeBuilder] Could not read scene FPS: {fps_err}")
        from .prism_scanner import PrismScanner
        scanner = PrismScanner(self.project_root)
        return float(scanner.get_project_info().get("fps", 25.0))

    def _tag_as_loader_owned(self, node):
        """Add a `fromShotLoader` checkbox knob (True) to mark this node as
        created by the Shot Loader. Used downstream by the loader's duplicate
        detection to distinguish its own Reads from manually-imported ones
        that happen to share a file path.

        The knob is disabled in the UI so the artist can't uncheck it by
        accident — the value can still be flipped from Python if needed.
        """
        try:
            if 'fromShotLoader' in node.knobs():
                node['fromShotLoader'].setValue(True)
                node['fromShotLoader'].setEnabled(False)
                return
            tag = nuke.Boolean_Knob('fromShotLoader', 'fromShotLoader')
            tag.setValue(True)
            node.addKnob(tag)
            tag.setEnabled(False)
        except Exception as e:
            print(f"[NukeNodeBuilder] Could not tag node {node.name()} as loader-owned: {e}")

    def _create_camera_node(
        self,
        usd_file: str,
        node_name: str,
        position: Tuple[int, int],
        prim_path: Optional[str] = None,
    ):
        """
        Create a Camera4 node from USD file.

        Args:
            usd_file (str): Path to USD file
            node_name (str): Name for the node
            position (Tuple[int, int]): Node position
            prim_path (Optional[str]): USD prim to import (sets import_prim_path knob)

        Returns:
            Camera4 node or None
        """
        try:
            # Create Camera4 node
            camera_node = nuke.createNode("Camera4", inpanel=False)
            camera_node.setName(node_name, uncollide=True)

            if 'file' in camera_node.knobs():
                camera_node['file'].setValue(usd_file.replace("\\", "/"))

            # Enable USD import
            if 'import_enabled' in camera_node.knobs():
                camera_node['import_enabled'].setValue(True)

            # Enable read from file
            if 'read_from_file' in camera_node.knobs():
                camera_node['read_from_file'].setValue(True)

            if prim_path and 'import_prim_path' in camera_node.knobs():
                camera_node['import_prim_path'].setValue(prim_path)
                print(f"[NukeNodeBuilder] Set import_prim_path: {prim_path}")

            if 'frame_rate' in camera_node.knobs():
                fps = self._resolve_scene_fps()
                camera_node['frame_rate'].setValue(fps)
                print(f"[NukeNodeBuilder] Set camera frame_rate to {fps}")

            # Set position
            camera_node.setXYpos(position[0], position[1])

            print(f"[NukeNodeBuilder] Created Camera4 node: {node_name}")
            return camera_node

        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating Camera4 node: {e}")
            return None

    def _create_backdrop(
        self,
        nodes: List,
        label: str,
        color: int
    ):
        """
        Create a backdrop encompassing given nodes.

        Args:
            nodes (List): List of nodes
            label (str): Backdrop label
            color (int): Backdrop color (hex)

        Returns:
            Backdrop node or None
        """
        if not nodes:
            self._last_backdrop_bounds = None
            return None

        try:
            # Calculate bounds
            bounds = self.positioning.calculate_backdrop_bounds(nodes)

            # Create backdrop
            backdrop = nuke.createNode("BackdropNode", inpanel=False)
            backdrop['xpos'].setValue(bounds[0])
            backdrop['ypos'].setValue(bounds[1])
            backdrop['bdwidth'].setValue(bounds[2])
            backdrop['bdheight'].setValue(bounds[3])
            backdrop['tile_color'].setValue(color)
            backdrop['label'].setValue(label)
            backdrop['note_font_size'].setValue(24)

            # Record bounds so load_assets can chain slot positions
            self._last_backdrop_bounds = bounds

            print(f"[NukeNodeBuilder] Created backdrop: {label}")
            return backdrop

        except Exception as e:
            print(f"[NukeNodeBuilder] Error creating backdrop: {e}")
            self._last_backdrop_bounds = None
            return None

    def _find_backdrop_by_label(self, label: str):
        """Return the first BackdropNode whose label matches, else None."""
        try:
            for n in nuke.allNodes("BackdropNode"):
                try:
                    if n['label'].value() == label:
                        return n
                except Exception:
                    pass
        except Exception as e:
            print(f"[NukeNodeBuilder] Error searching backdrop '{label}': {e}")
        return None

    def _get_existing_backdrop_bounds(self, label: str):
        """Return (x, y, w, h) for an existing backdrop matching label, else None."""
        bd = self._find_backdrop_by_label(label)
        if not bd:
            return None
        return (
            int(bd['xpos'].value()),
            int(bd['ypos'].value()),
            int(bd['bdwidth'].value()),
            int(bd['bdheight'].value()),
        )

    def _nodes_inside_backdrop(self, backdrop) -> List:
        """
        Return non-backdrop nodes whose top-left lies within the backdrop's
        rectangle. Prefer Nuke's native BackdropNode.getNodes() when available.
        """
        try:
            if hasattr(backdrop, "getNodes"):
                nodes = [n for n in backdrop.getNodes() if n.Class() != "BackdropNode"]
                if nodes:
                    return nodes
        except Exception:
            pass

        try:
            bd_x = int(backdrop['xpos'].value())
            bd_y = int(backdrop['ypos'].value())
            bd_w = int(backdrop['bdwidth'].value())
            bd_h = int(backdrop['bdheight'].value())
        except Exception:
            return []

        inside = []
        for n in nuke.allNodes():
            if n.Class() == "BackdropNode":
                continue
            nx, ny = n.xpos(), n.ypos()
            if bd_x <= nx <= bd_x + bd_w and bd_y <= ny <= bd_y + bd_h:
                inside.append(n)
        return inside

    def _resolve_slot_anchor(self, backdrop_label: str):
        """
        Returns where the read-grid for `backdrop_label` should be anchored.

        With the grid layout, the anchor is the top-left of slot (0, 0). If the
        backdrop already exists, we resume the grid from its top-leftmost
        existing read; the `existing_count` tells the caller which slot index
        the next new read should fill.

        Returns:
            (base_x, base_y, existing_backdrop, existing_nodes, existing_count)
        """
        existing = self._find_backdrop_by_label(backdrop_label)
        if existing:
            existing_nodes = self._nodes_inside_backdrop(existing)
            grid_nodes = [n for n in existing_nodes if n.Class() in ("Read", "Camera4")]
            if grid_nodes:
                base_x = min(n.xpos() for n in grid_nodes)
                base_y = min(n.ypos() for n in grid_nodes)
                existing_count = len(grid_nodes)
            else:
                base_x = int(existing['xpos'].value()) + 50
                base_y = int(existing['ypos'].value()) + 80
                existing_count = 0
            return base_x, base_y, existing, existing_nodes, existing_count

        base_x, base_y = self.positioning.get_next_asset_type_position()
        return base_x, base_y, None, [], 0

    def _get_grid_position(self, base_x: int, base_y: int, read_index: int) -> Tuple[int, int]:
        """
        Wrap the read at `read_index` into a Config.READS_PER_ROW grid anchored
        at (base_x, base_y).
        """
        col = read_index % Config.READS_PER_ROW
        row = read_index // Config.READS_PER_ROW
        x = base_x + col * Config.READ_COL_SPACING
        y = base_y + row * Config.READ_ROW_HEIGHT
        return (x, y)

    def _bd_bounds(self, backdrop):
        """Return (x, y, w, h) for a backdrop or None."""
        if not backdrop:
            return None
        return (
            int(backdrop['xpos'].value()),
            int(backdrop['ypos'].value()),
            int(backdrop['bdwidth'].value()),
            int(backdrop['bdheight'].value()),
        )

    def _reposition_backdrop(self, backdrop, new_x: int, new_y: int, new_height: int = None):
        """
        Move a backdrop AND every node it currently contains to (new_x, new_y).
        Optionally force a new height (useful when matching another backdrop's
        vertical extent). Width is preserved.
        """
        if not backdrop:
            return

        cur_x = int(backdrop['xpos'].value())
        cur_y = int(backdrop['ypos'].value())
        dx = new_x - cur_x
        dy = new_y - cur_y

        if dx or dy:
            inside = self._nodes_inside_backdrop(backdrop)
            for n in inside:
                n.setXYpos(n.xpos() + dx, n.ypos() + dy)
            backdrop['xpos'].setValue(new_x)
            backdrop['ypos'].setValue(new_y)

        if new_height is not None:
            backdrop['bdheight'].setValue(new_height)

    def _normalize_layout(self):
        """
        Re-apply the layout invariants after all loaders have run:
          * 3D, Camera, 2D, Plates form a vertical stack, all left-aligned with
            the topmost slot (preferably 3D Renders).
          * Rotos sits to the right of Plates with matching y and height.
        Each backdrop's contents are translated together so connections survive.

        Returns the fresh bounds list (post-normalization) for the parent resize.
        """
        x_gap = Config.BACKDROP_PADDING * 2
        y_gap = 50

        labels = {
            '3d': "3D RENDERS",
            'cam': "CAMERAS",
            '2d': "2D RENDERS",
            'plates': "PLATES",
            'rotos': "ROTOS",
        }
        bds = {k: self._find_backdrop_by_label(v) for k, v in labels.items()}

        # Vertical chain in declared order. Backdrops that already exist in
        # the scene stay put — only newly-created backdrops are repositioned
        # to honour the layout.
        chain = [(k, bds[k]) for k in ('3d', 'cam', '2d', 'plates') if bds[k]]
        if chain:
            first_bd = chain[0][1]
            left_x = int(first_bd['xpos'].value())
            prev_bounds = self._bd_bounds(first_bd)

            for _, bd in chain[1:]:
                if bd in self.created_backdrops:
                    new_y = prev_bounds[1] + prev_bounds[3] + y_gap
                    self._reposition_backdrop(bd, new_x=left_x, new_y=new_y)
                prev_bounds = self._bd_bounds(bd)

        # Rotos — right of Plates, same y, same height. Only reposition if Rotos
        # was created this run.
        bounds_plates = self._bd_bounds(bds['plates'])
        if bds['rotos'] and bounds_plates and bds['rotos'] in self.created_backdrops:
            self._reposition_backdrop(
                bds['rotos'],
                new_x=bounds_plates[0] + bounds_plates[2] + x_gap,
                new_y=bounds_plates[1],
                new_height=bounds_plates[3],
            )

        return [
            self._bd_bounds(bds['3d']),
            self._bd_bounds(bds['cam']),
            self._bd_bounds(bds['2d']),
            self._bd_bounds(bds['plates']),
            self._bd_bounds(bds['rotos']),
        ]

    def _finalize_backdrop(
        self,
        existing,
        existing_nodes: List,
        new_nodes: List,
        label: str,
        color: int,
    ):
        """
        If `existing` is provided, grow it ONLY for the edges where new nodes
        actually stick out of its current rectangle. If every new node fits
        inside the existing backdrop as-is, the backdrop is left untouched —
        no re-snap to a freshly-padded bbox.

        Otherwise create a fresh backdrop sized to the new nodes.
        Records last_backdrop_bounds either way.
        """
        if not new_nodes:
            return

        if existing:
            cur_x = int(existing['xpos'].value())
            cur_y = int(existing['ypos'].value())
            cur_right = cur_x + int(existing['bdwidth'].value())
            cur_bottom = cur_y + int(existing['bdheight'].value())

            # Raw bbox of just the new nodes (no padding). Existing nodes are
            # by definition already inside the backdrop, so they don't need
            # to be re-checked.
            new_min_x = min(n.xpos() for n in new_nodes)
            new_min_y = min(n.ypos() for n in new_nodes)
            new_max_x = max(n.xpos() + n.screenWidth() for n in new_nodes)
            new_max_y = max(n.ypos() + n.screenHeight() for n in new_nodes)

            fits = (
                cur_x <= new_min_x and new_max_x <= cur_right
                and cur_y <= new_min_y and new_max_y <= cur_bottom
            )

            if fits:
                print(f"[NukeNodeBuilder] Backdrop already fits new content: {label}")
                self._last_backdrop_bounds = (cur_x, cur_y, cur_right - cur_x, cur_bottom - cur_y)
                return

            # Grow only the edges that need to grow, with padding added only
            # on those sides — sides that already fit keep their current edge.
            pad = Config.BACKDROP_PADDING
            new_x = min(cur_x, new_min_x - pad)
            new_y = min(cur_y, new_min_y - pad)
            new_right = max(cur_right, new_max_x + pad)
            new_bottom = max(cur_bottom, new_max_y + pad)

            existing['xpos'].setValue(new_x)
            existing['ypos'].setValue(new_y)
            existing['bdwidth'].setValue(new_right - new_x)
            existing['bdheight'].setValue(new_bottom - new_y)
            print(f"[NukeNodeBuilder] Grew backdrop: {label}")
            self._last_backdrop_bounds = (new_x, new_y, new_right - new_x, new_bottom - new_y)
            return

        backdrop = self._create_backdrop(new_nodes, label, color)
        if backdrop:
            self.created_backdrops.append(backdrop)

    def _construct_sequence_path(self, folder_path: str) -> Optional[str]:
        """
        Construct a sequence path with #### from folder containing images.
        For static images (without frame numbers), returns the path to the first image.

        Args:
            folder_path (str): Path to folder containing image sequence or static image

        Returns:
            Optional[str]: Path with #### (e.g., "path/file.####.exr") or static path, or None
        """
        if not os.path.exists(folder_path):
            return None

        try:
            files = os.listdir(folder_path)
            image_files = [
                f for f in files
                if any(f.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS)
            ]

            if not image_files:
                return None

            # Get first image file
            first_file = sorted(image_files)[0]

            # Check if it's a static image or a sequence
            if self._is_static_image(first_file):
                # Static image - return path to the file as-is
                print(f"[NukeNodeBuilder] Detected static image: {first_file}")
                return os.path.join(folder_path, first_file)
            else:
                # Sequence - replace frame number with ####
                # Pattern: filename.1001.exr -> filename.####.exr
                sequence_file = re.sub(r'\.(\d{4})\.(exr|dpx|jpg|png)$', r'.####.\2', first_file)
                print(f"[NukeNodeBuilder] Detected sequence: {sequence_file}")
                return os.path.join(folder_path, sequence_file)

        except Exception as e:
            print(f"[NukeNodeBuilder] Error constructing sequence path: {e}")
            return None

    def _find_usd_file(self, folder_path: str) -> Optional[str]:
        """
        Find USD file in a folder.

        Args:
            folder_path (str): Path to folder

        Returns:
            Optional[str]: Path to USD file or None
        """
        if not os.path.exists(folder_path):
            return None

        try:
            files = os.listdir(folder_path)
            usd_files = [
                f for f in files
                if any(f.lower().endswith(ext) for ext in Config.USD_EXTENSIONS)
            ]

            if usd_files:
                return os.path.join(folder_path, usd_files[0])

        except Exception as e:
            print(f"[NukeNodeBuilder] Error finding USD file: {e}")

        return None

    def _is_static_image(self, filename: str) -> bool:
        """
        Check if a file is a static image (no frame number).

        Args:
            filename (str): Filename to check

        Returns:
            bool: True if static image (no frame number), False if sequence
        """
        # Pattern for frame-numbered sequences: filename.1001.exr
        frame_pattern = re.compile(r'\.(\d{4})\.(exr|dpx|jpg|jpeg|png|tif|tiff)$', re.IGNORECASE)
        return not frame_pattern.search(filename)

    def _set_project_fps(self):
        """
        Set Nuke project FPS from Prism project settings.
        Must be called before importing USD cameras.
        """
        try:
            from .prism_scanner import PrismScanner
            scanner = PrismScanner(self.project_root)
            project_info = scanner.get_project_info()
            fps = float(project_info.get("fps", 25.0))

            # Set Nuke's root FPS
            root = nuke.root()
            root['fps'].setValue(fps)

            print(f"[NukeNodeBuilder] Set project FPS to {fps}")

        except Exception as e:
            print(f"[NukeNodeBuilder] Error setting project FPS: {e}")

    def _insert_read_cleanup(self, read_node):
        """Create an ILGC_ReadCleanup gizmo wired to read_node and positioned
        just below it. Returns the cleanup node, or None if the gizmo isn't
        registered in this Nuke session (e.g. pipeline tools not loaded).
        """
        try:
            cleanup = nuke.createNode("ILGC_ReadCleanup", inpanel=False)
        except Exception as e:
            print(f"[NukeNodeBuilder] ILGC_ReadCleanup gizmo not available: {e}")
            return None
        if cleanup is None:
            return None

        cleanup.setInput(0, read_node)
        read_center_x = read_node.xpos() + read_node.screenWidth() / 2
        cleanup_x = int(read_center_x - cleanup.screenWidth() / 2)
        # Place the cleanup just below the Read's actual bottom edge so it
        # clears the postage-stamp thumbnail regardless of how tall the Read
        # is laid out. Falls back to a safe constant if screenHeight is 0
        # (node not yet drawn in the DAG).
        read_height = read_node.screenHeight() or 80
        cleanup.setXYpos(cleanup_x, read_node.ypos() + read_height + 25)
        self._tag_as_loader_owned(cleanup)
        print(f"[NukeNodeBuilder] Inserted ILGC_ReadCleanup under {read_node.name()}")
        return cleanup

    def _create_stamp_for_node(self, node, stamp_name: str, anchor_y_offset: int = 150):
        """
        Create an Anchor Stamp and a Wired Stamp for a node.

        Args:
            node: Nuke node to create stamp from
            stamp_name (str): Short name for the stamp
            anchor_y_offset (int): Vertical gap between node and its anchor.
                Default 150 matches Reads/Cameras; pass a smaller value when
                the source is a small utility node (e.g. ILGC_ReadCleanup)
                to keep the chain compact.

        Returns:
            List: [anchor, wired] if successful, empty list otherwise
        """
        if self.stamps.is_available():
            try:
                # Create the anchor stamp (will be positioned anchor_y_offset px below the source in stamps_integration)
                anchor = self.stamps.create_anchor_stamp(node, name=stamp_name, y_offset=anchor_y_offset)

                if anchor:
                    # Create a wired stamp connected to this anchor
                    # Position it 50px below the anchor
                    anchor_x = anchor.xpos()
                    anchor_y = anchor.ypos()
                    wired_position = (anchor_x, anchor_y + 50)

                    wired = self.stamps.create_wired_stamp(
                        anchor_node=anchor,
                        position=wired_position,
                    )

                    if wired:
                        print(f"[NukeNodeBuilder] Created anchor + wired stamp: {stamp_name}")
                        return [anchor, wired]
                    else:
                        print(f"[NukeNodeBuilder] Created anchor stamp only: {stamp_name}")
                        return [anchor]
                else:
                    print(f"[NukeNodeBuilder] Failed to create anchor stamp: {stamp_name}")
                    return []

            except Exception as e:
                print(f"[NukeNodeBuilder] Error creating stamp: {e}")
                return []
        else:
            print(f"[NukeNodeBuilder] Stamps not available, skipping stamp creation")
            return []

    def _load_stmaps(
        self,
        sequence: str,
        shot: str,
        versions: Dict,
        base_x: int,
        base_y: int,
        nodes_in_group: List
    ):
        """
        Special loader for stMaps - loads ALL static image files found (U and V maps).
        stMaps are typically single-frame images without frame numbers.

        Args:
            sequence (str): Sequence name
            shot (str): Shot name
            versions (Dict): Versions dict for stMaps
            base_x (int): Base X position
            base_y (int): Base Y position
            nodes_in_group (List): List to append created nodes to
        """
        print(f"[NukeNodeBuilder] Loading stMaps (static images)")

        # Get latest version
        latest_version = _latest(versions.keys())
        if not latest_version:
            return

        layers = versions[latest_version]

        # For stMaps, scan all files in each layer folder
        for layer_name, layer_path in layers.items():
            if not os.path.exists(layer_path):
                continue

            try:
                files = os.listdir(layer_path)

                # Filter to get only image files
                image_files = [
                    f for f in files
                    if any(f.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS)
                ]

                if not image_files:
                    print(f"[NukeNodeBuilder] No image files found in {layer_path}")
                    continue

                # Separate static images from sequences
                static_images = []
                sequence_files = []

                for f in image_files:
                    if self._is_static_image(f):
                        static_images.append(f)
                    else:
                        sequence_files.append(f)

                print(f"[NukeNodeBuilder] Found {len(static_images)} static image(s) and {len(sequence_files)} sequence file(s)")

                # Create a Read node for each static image
                for image_file in sorted(static_images):
                    node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

                    # Get full path to the static image
                    full_path = os.path.join(layer_path, image_file)

                    # Extract a clean name (remove extension)
                    clean_name = os.path.splitext(image_file)[0]

                    # Get colorspace for this asset (stMaps are keyed as "Plate_stMaps")
                    colorspace_key = "Plate_stMaps"
                    colorspace = self.asset_colorspaces.get(colorspace_key)

                    # Create Read node for static image
                    read_node = self._create_read_node_for_static_image(
                        file_path=full_path,
                        node_name=f"{sequence}_{shot}_stMap_{clean_name}",
                        position=(node_x, node_y),
                        colorspace=colorspace
                    )

                    if read_node:
                        version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                        label_text = f"stMap\n{clean_name}\n" + version_tcl
                        read_node['label'].setValue(label_text)
                        nodes_in_group.append(read_node)
                        self.created_nodes.append(read_node)

                        # Create stamp
                        stamp_name = f"stMap_{clean_name}"
                        stamps = self._create_stamp_for_node(read_node, stamp_name)
                        # Add stamps to nodes_in_group so they're included in backdrop bounds
                        nodes_in_group.extend(stamps)
                        self._read_count += 1

                # Handle sequence files if any exist (rare for stmaps but possible)
                if sequence_files:
                    print(f"[NukeNodeBuilder] Warning: Found sequence files in stMaps folder, loading as sequences")
                    # Group sequence files by base name
                    file_groups = {}
                    frame_pattern = re.compile(r'^(.+)\.(\d{4})\.(exr|dpx|jpg|jpeg|png)$', re.IGNORECASE)

                    for f in sequence_files:
                        match = frame_pattern.match(f)
                        if match:
                            base_name = match.group(1)
                            if base_name not in file_groups:
                                file_groups[base_name] = []
                            file_groups[base_name].append(f)

                    # Create a Read node for each sequence
                    for base_name, file_list in file_groups.items():
                        if not file_list:
                            continue

                        node_x, node_y = self._get_grid_position(base_x, base_y, self._read_count)

                        # Get colorspace for this asset (stMaps are keyed as "Plate_stMaps")
                        colorspace_key = "Plate_stMaps"
                        colorspace = self.asset_colorspaces.get(colorspace_key)

                        read_node = self._create_read_node_for_sequence(
                            file_path=layer_path,
                            node_name=f"{sequence}_{shot}_stMap_{base_name}",
                            position=(node_x, node_y),
                            colorspace=colorspace
                        )

                        if read_node:
                            version_tcl = r"[lindex [regexp -inline -all {v\d+} [value file]] end]"
                            label_text = f"stMap\n{base_name}\n" + version_tcl
                            read_node['label'].setValue(label_text)
                            nodes_in_group.append(read_node)
                            self.created_nodes.append(read_node)

                            stamp_name = f"stMap_{base_name}"
                            stamps = self._create_stamp_for_node(read_node, stamp_name)
                            nodes_in_group.extend(stamps)
                            self._read_count += 1

            except Exception as e:
                print(f"[NukeNodeBuilder] Error loading stMaps from {layer_path}: {e}")

    def update_node_version(
        self,
        node,
        new_version_path: str,
        frame_range: Optional[Tuple[int, int]] = None
    ) -> bool:
        """
        Update a node to a new version. Handles Read (image sequence) and
        Camera4 (USD file) nodes — they look up files differently.

        Args:
            node: Nuke node (Read or Camera4)
            new_version_path (str): Path to new version folder
            frame_range (Optional[Tuple[int, int]]): New frame range (Read only)

        Returns:
            bool: Success status
        """
        try:
            # Camera4: find a USD file in the folder, set the file knob, ensure
            # import is enabled. Don't touch first/last — Camera4 has no such knobs.
            if node.Class() == "Camera4":
                usd_file = self._find_usd_file(new_version_path)
                if not usd_file:
                    print(f"[NukeNodeBuilder] No USD file found in {new_version_path}")
                    return False

                if 'file' in node.knobs():
                    node['file'].setValue(usd_file.replace("\\", "/"))
                if 'read_from_file' in node.knobs():
                    node['read_from_file'].setValue(True)
                if 'import_enabled' in node.knobs():
                    node['import_enabled'].setValue(True)

                # Re-apply scene FPS on update too — the artist may have
                # changed the scene framerate since the camera was first loaded.
                if 'frame_rate' in node.knobs():
                    fps = self._resolve_scene_fps()
                    node['frame_rate'].setValue(fps)
                    print(f"[NukeNodeBuilder] Updated camera frame_rate to {fps}")

                print(f"[NukeNodeBuilder] Updated camera {node.name()} to {usd_file}")
                return True

            # Read (and any other image-sequence node)
            sequence_path = self._construct_sequence_path(new_version_path)
            if not sequence_path:
                print(f"[NukeNodeBuilder] Cannot construct path for {new_version_path}")
                return False

            node['file'].setValue(sequence_path.replace("\\", "/"))

            if frame_range:
                node['first'].setValue(frame_range[0])
                node['last'].setValue(frame_range[1])

            print(f"[NukeNodeBuilder] Updated node {node.name()} to new version")
            return True

        except Exception as e:
            print(f"[NukeNodeBuilder] Error updating node version: {e}")
            return False
