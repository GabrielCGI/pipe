"""Loader tab: lists the shot's assets and loads / updates / freezes them."""

import datetime
import os
import traceback

import nuke

from ..core import project
from ..core import status
from ..core.asset_discoverer import AssetDiscoverer
from ..core.asset_item import (DISCOVERY_KEYS, SOURCE_TYPES, AssetItem, colorspace_key,
                               first_layer_path)
from ..core.coverage import FrameCoverage
from ..core.versions import extract_version_from_path, version_int
from .qt import QtCore, QtWidgets
from ..scene import asset_nodes
from ..scene import cameras as camera_files
from ..scene import utils as scene
from ..scene.node_builder import NukeNodeBuilder
from ..scene.stamps import anchor_title, reconnect_postage_stamps
from . import icons
from . import widgets as w

COL_NAME, COL_TYPE, COL_VERSION, COL_COLORSPACE, COL_STATUS, COL_FREEZE, COL_ACTION = range(7)
FILTERS = ["All", "3dRender", "2dRender", "external", "Camera", "From Other Shots", "Loaded"]
_FALLBACK_COLORSPACES = ["default", "linear", "sRGB", "Rec.709"]
_OCIO_FALLBACK = ["scene_linear", "ARRI LogC4", "sRGB", "Rec.709", "linear", "default"]
_NUKE_COLORSPACES = ["default", "linear", "sRGB", "Rec.709", "Cineon", "Gamma1.8", "Gamma2.2"]


_UNSEEN = object()


def _is_precomp_asset(name):
    """Precomp renders are reloaded by the Precomp gizmo, not by the loader."""
    return "precomp" in (name or "").lower()


def _package_key(entry):
    """Row identity of a package entry: rotos have one row per version,
    copies and assets of other shots rows of their own."""
    asset_type = entry.get("type")
    return (asset_type, entry.get("name"), entry.get("foreign_sequence", ""), entry.get("foreign_shot", ""),
            entry.get("copy", 0), entry.get("version") if asset_type == "Roto" else "")


def _row_package_key(item):
    return (item.asset_type, item.asset_name, item.foreign_sequence, item.foreign_shot,
            item.dup_index, item.versions[0] if item.asset_type == "Roto" else "")


def _update_line(item):
    """'v004 → v005' in the update confirmation; a camera out of sync with
    its file is baked again from its own version."""
    target = item.update_target_version or item.versions[-1]
    if item.camera_mismatch and target == item.loaded_version:
        return f"{target} baked again (its knobs aren't the file's camera)"
    return f"{item.loaded_version} → {target}"


def _folder_signature(folder):
    """Hash of the (name, size, mtime) of a folder's entries, None when
    unreadable. On Windows scandir returns the stats with the listing, so
    this costs one directory read."""
    entries = []
    try:
        with os.scandir(folder) as it:
            for entry in it:
                try:
                    st = entry.stat(follow_symlinks=False)
                except OSError:
                    continue
                entries.append((entry.name, st.st_size, st.st_mtime_ns))
    except OSError:
        return None
    return hash(frozenset(entries))


class LoaderTab(QtWidgets.QWidget):

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.discoverer = AssetDiscoverer(session.project_root)
        self.builder = NukeNodeBuilder(session.project_root)
        self.coverage = FrameCoverage()
        self.assets = {}
        self.items = []
        self._show_hidden = False
        self._colorspaces = None
        self._folder_signatures = {}   # Read folder -> _folder_signature() at the last check
        # Row key -> version picked in its dropdown and not applied yet: kept
        # (status "Rollback: ..." / "Update: ...") through every refresh and
        # rescan for the lifetime of the dialog.
        self._manual_versions = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(w.project_header(self.session))

        self.banner = w.ContextBanner()
        package_label = QtWidgets.QLabel("PACKAGE :")
        package_label.setObjectName("filterLabel")
        self.package_combo = w.PackageComboBox()
        self.package_combo.setMinimumWidth(140)
        self.choose_package_btn = w.button("Choose Package", self._choose_package, "secondaryAction")
        for widget in (package_label, self.package_combo, self.choose_package_btn):
            self.banner.add_widget(widget)
        layout.addWidget(self.banner)

        group = QtWidgets.QGroupBox("AVAILABLE ASSETS")
        group_layout = QtWidgets.QVBoxLayout(group)
        group_layout.setContentsMargins(6, 4, 6, 6)
        group_layout.setSpacing(10)
        group_layout.addLayout(self._build_filter_row())
        self.table = self._build_table()
        group_layout.addWidget(self.table)
        layout.addWidget(group, stretch=1)
        layout.addLayout(self._build_actions())

    def _build_filter_row(self):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(6)
        label = QtWidgets.QLabel("FILTERS :")
        label.setObjectName("filterLabel")
        row.addWidget(label)
        self.filter_buttons = {}
        for source in FILTERS:
            btn = w.button(source, lambda _=False, s=source: self._apply_filter(s), "filterPill")
            btn.setCheckable(True)
            btn.setChecked(source == "All")
            row.addWidget(btn)
            self.filter_buttons[source] = btn
        row.addStretch()
        self.show_hidden_checkbox = QtWidgets.QCheckBox("Show Hidden Assets")
        self.show_hidden_checkbox.setCursor(QtCore.Qt.PointingHandCursor)
        self.show_hidden_checkbox.toggled.connect(self._on_show_hidden_toggled)
        row.addWidget(self.show_hidden_checkbox)
        return row

    def _build_table(self):
        table = QtWidgets.QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["Name", "Type", "Version", "Colorspace", "Status", "", ""])
        for col, width in enumerate((200, 100, 100, 150, 260, 28, 36)):
            table.setColumnWidth(col, width)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(34)
        header = table.horizontalHeader()
        header.setHighlightSections(False)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(COL_STATUS, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(COL_FREEZE, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(COL_ACTION, QtWidgets.QHeaderView.Fixed)
        # Cell widgets only follow a column drag on mouse release otherwise.
        header.sectionResized.connect(self._on_column_resized)
        table.setItemDelegateForColumn(COL_STATUS, w.StatusColorDelegate(table))
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_context_menu)
        return table

    def _build_actions(self):
        rows = QtWidgets.QVBoxLayout()
        rows.setSpacing(8)

        def row(*buttons, right=None):
            """Buttons packed left, optional `right` button at the far right."""
            layout = QtWidgets.QHBoxLayout()
            layout.setSpacing(8)
            for btn in buttons:
                layout.addWidget(btn)
            layout.addStretch()
            if right is not None:
                layout.addWidget(right)
            rows.addLayout(layout)

        row(w.button("Select All", self._select_all),
            w.button("Deselect All", self.table.clearSelection))
        row(w.button("Update Selected", self._update_selected, "updateAction"),
            w.button("Update All Loaded", self._update_all_loaded, "dangerAction"))
        row(w.button("Load Selected", self._load_selected, "primaryAction"),
            w.button("Load All", self._load_all, "secondaryAction"),
            w.button("Duplicate Selected", self._duplicate_selected, "duplicateAction",
                     "Clone every loaded selected asset into an independent copy —\n"
                     "same version at duplication time, then freezable / updatable\n"
                     "separately from its parent. The clone appears as an extra row\n"
                     "right under its parent (suffix '· copy_NN')."),
            right=w.button("Refresh", self._check_for_updates_clicked,
                           tooltip="Rescan the shot folder and check the loaded assets for updates."))
        return rows

    # ------------------------------------------------------------------
    # Public API (used by the main window)
    # ------------------------------------------------------------------

    def scan(self):
        """Re-discover the shot's assets from disk and rebuild the table."""
        session = self.session
        if not session.has_shot:
            return
        self.banner.set_message(f"Scanning assets for {session.sequence}/{session.shot}...")
        QtWidgets.QApplication.processEvents()

        print("\n[ShotAssetLoader] === SCAN START ===")
        print(f"[ShotAssetLoader] Project root: {session.project_root}")
        print(f"[ShotAssetLoader] Sequence: {session.sequence} | Shot: {session.shot}")
        self.assets = self.discoverer.discover_all_assets(session.sequence, session.shot)
        print("[ShotAssetLoader] === SCAN RESULTS ===")
        for key in ("plates", "3d_renders", "2d_renders", "rotos", "cameras"):
            print(f"[ShotAssetLoader]   {key + ':':11} {len(self.assets.get(key, {}))}")

        self._populate_table()
        self._refresh_package_combo()

    def refresh_banner(self):
        self.banner.show_shot(self.session, "ASSETS", len(self.items))

    def height_delta(self):
        visible = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        return w.fit_height_delta(self.table, visible) if self.items and visible else 0

    def refresh_status(self, silent=False):
        """Match every row to its scene nodes, pick up what changed on disk,
        recompute the statuses, then mirror them on the nodes (tile color +
        label) and reload the Reads whose files changed."""
        if not self.session.has_shot:
            if not silent:
                QtWidgets.QMessageBox.warning(self, "Warning", "Please scan a shot first")
            return
        if not self.items:
            if not silent:
                QtWidgets.QMessageBox.warning(self, "Warning", "No assets to check")
            return

        self._match_nodes()
        changed = self._changed_read_folders()
        for folder in changed:  # e.g. frames landing in a loaded version
            self.coverage.forget(folder)
        scene_range = scene.scene_frame_range()
        updates_found = sum(self._evaluate(item, scene_range) for item in self.items if item.loaded_nodes)
        manual = [it for it in self.items
                  if it.loaded_nodes and self._manual_versions.get(_row_package_key(it)) == it.selected_version]
        for item in manual:  # the artist's pick wins over the computed update target
            status.apply_manual_selection(item)
        if manual:
            updates_found = sum(1 for it in self.items if it.loaded_nodes and it.has_update)
        updates_found += sum(self._flag_stale_camera(item) for item in self.items)

        for item in self.items:
            if item.is_frozen and item.loaded_node is not None:
                status.apply_freeze_override(item)
            elif item.has_duplicates:
                status.apply_duplicate_override(item)

        # Scene-derived rows whose node disappeared have nothing left to show.
        for row in range(len(self.items) - 1, -1, -1):
            item = self.items[row]
            if item.is_scene_bound and item.loaded_node is None:
                self.items.pop(row)
                self.table.removeRow(row)

        self._refresh_filter_visibility()
        self._repaint_rows()
        self._sync_nodes(changed)

        if silent:
            print(f"[ShotAssetLoader] Silent check complete: {updates_found} update(s) available")
        elif updates_found:
            QtWidgets.QMessageBox.information(
                self, "Updates Available", f"Found {updates_found} asset(s) with updates available")
        else:
            QtWidgets.QMessageBox.information(self, "All Up to Date", "All loaded assets are up to date")

    # ------------------------------------------------------------------
    # Status evaluation
    # ------------------------------------------------------------------

    def _match_nodes(self):
        """Bind every row to its scene nodes (one per layer / file)."""
        read_nodes = nuke.allNodes("Read")
        camera_nodes = nuke.allNodes("Camera3")
        present = set(read_nodes) | set(camera_nodes)
        loader_reads = asset_nodes.loader_reads_for_shot(read_nodes, self.session.sequence, self.session.shot)
        for item in self.items:
            if item.is_scene_bound:  # bound at populate time
                item.loaded_nodes = [n for n in item.loaded_nodes if self._node_present(n, present)]
                if not item.loaded_nodes:
                    status.mark_not_loaded(item, "Not loaded (removed from scene)")
                continue
            item.loaded_nodes, item.has_duplicates = asset_nodes.find_nodes_for_asset(
                item, loader_reads, camera_nodes, self.session.sequence, self.session.shot)
            if not item.loaded_nodes:
                status.mark_not_loaded(item)

    @staticmethod
    def _node_present(node, present):
        if node is None:
            return False
        try:
            return node in present
        except Exception:  # deleted node
            return False

    def _changed_read_folders(self):
        """Folders of the loaded Reads whose content changed since the last
        check — all of them on the first one. One directory read each."""
        signatures = {}
        for item in self.items:
            for node in item.loaded_nodes:
                if node.Class() == "Read":
                    folder = os.path.dirname(asset_nodes.file_path(node))
                    if folder not in signatures:
                        signatures[folder] = _folder_signature(folder)
        changed = {f for f, sig in signatures.items() if self._folder_signatures.get(f, _UNSEEN) != sig}
        self._folder_signatures.update(signatures)
        return changed

    def _evaluate(self, item, scene_range) -> int:
        """Status of a loaded row. Returns 1 when an update is offered."""
        if not asset_nodes.file_path(item.loaded_node):
            if item.asset_type == "Camera":  # Camera3 without a file: "v000", so an update is offered
                item.loaded_version = "v000"
                return int(status.apply_update_target(item, self.coverage, scene_range))
            item.update_target_version = None
            status.set_status(item, "File path not found", None)
            return 0
        return self._evaluate_loaded(item, scene_range)

    def _evaluate_loaded(self, item, scene_range) -> int:
        versions = {extract_version_from_path(asset_nodes.file_path(n)) for n in item.loaded_nodes} - {None}
        if not versions:
            item.update_target_version = None
            status.set_status(item, "Version not found in path", None)
            return 0
        item.loaded_version = min(versions, key=version_int)
        found = int(status.apply_update_target(item, self.coverage, scene_range))
        if len(versions) > 1:  # layers of the asset on different versions
            item.has_update = True
            status.set_status(item, f"Mixed versions ({', '.join(sorted(versions, key=version_int))})",
                              status.StatusColor.UPDATE_PARTIAL)
            return 1
        return found

    @staticmethod
    def _flag_stale_camera(item) -> int:
        """An up-to-date camera whose knobs hold another camera than its file
        (Nuke loads the file only once the panel exists, see scene/cameras.py):
        offered as an update to the same version, which bakes the file.
        Returns 1 when flagged."""
        previous, item.camera_mismatch = item.camera_mismatch, None
        if (item.asset_type != "Camera" or item.has_update or len(item.loaded_nodes) != 1
                or item.loaded_version in (None, "v000")):
            return 0
        try:
            report = camera_files.out_of_sync(item.loaded_node)
        except Exception as e:   # never break the status refresh
            print(f"[ShotAssetLoader] {item.label()}: camera not compared with its file ({e})")
            return 0
        if report is None:
            return 0
        item.camera_mismatch = str(report)
        item.has_update = True
        item.update_target_version = item.loaded_version
        status.set_status(item, f"Out of sync with {item.loaded_version} (holds {report.held or 'another camera'})",
                          status.StatusColor.UPDATE_PARTIAL)
        if item.camera_mismatch != previous:
            print(f"[ShotAssetLoader] {item.label()}: {report} — Update bakes the file's camera")
        return 1

    def _sync_nodes(self, changed_folders):
        """Mirror each row's status onto its nodes (outside the undo history)
        and reload the Reads of `changed_folders` so renders landing on disk
        show up. Reloading flushes a Read's cache: unchanged ones are left
        alone."""
        with scene.no_undo():
            for item in self.items:
                if not item.loaded_nodes or item.has_duplicates:
                    continue
                key = "frozen" if item.is_frozen else status.node_status_key(item)
                if key:
                    for node in item.loaded_nodes:
                        asset_nodes.set_status_marker(node, key)
            for item in self.items:
                for node in item.loaded_nodes:
                    if node.Class() == "Read" and os.path.dirname(asset_nodes.file_path(node)) in changed_folders:
                        asset_nodes.reload_read(node)

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------

    def _populate_table(self):
        """Disk assets, then assets loaded from other shots, each followed
        by its "Duplicate Selected" clones."""
        self.items = []
        self.table.setRowCount(0)
        shot_key = self.session.shot_key
        prefs = self.session.prefs
        hidden = prefs.hidden(shot_key) if self.session.has_shot else set()
        frozen = prefs.frozen(shot_key) if self.session.has_shot else set()
        scene_range = scene.scene_frame_range()

        def visible(asset_type, name):
            is_hidden = (asset_type, name) in hidden
            return (not is_hidden or self._show_hidden), is_hidden

        collected = []
        for asset_type in ("Plate", "3D Render", "2D Render"):
            for name, versions_dict in self.assets.get(DISCOVERY_KEYS[asset_type], {}).items():
                show, is_hidden = visible(asset_type, name)
                if _is_precomp_asset(name) or not show or not versions_dict:
                    continue
                item = AssetItem(asset_type, name, sorted(versions_dict), versions_dict, SOURCE_TYPES[asset_type])
                item.is_hidden = is_hidden
                # Default to the highest version covering the scene range.
                target, _ = self.coverage.pick_update_target(item, scene_range)
                if target:
                    item.selected_version = target
                collected.append(item)

        # Every roto version is its own row; they hide together as "roto".
        show, is_hidden = visible("Roto", "roto")
        if show:
            for version, layers in sorted(self.assets.get("rotos", {}).items()):
                item = AssetItem("Roto", "roto", [version], {version: layers}, "external")
                item.is_hidden = is_hidden
                collected.append(item)

        for name, versions_dict in self.assets.get("cameras", {}).items():
            show, is_hidden = visible("Camera", name)
            if _is_precomp_asset(name) or not show or not versions_dict:
                continue
            item = AssetItem("Camera", name, sorted(versions_dict), versions_dict, "Camera")
            item.is_hidden = is_hidden
            collected.append(item)

        for item in self._discover_foreign_assets():
            show, item.is_hidden = visible(item.asset_type, item.asset_name)
            if show and not _is_precomp_asset(item.asset_name):
                collected.append(item)

        duplicates = self._discover_scene_duplicates(collected)
        for parent in collected:
            self.items.append(parent)
            self.items.extend(sorted(duplicates.get((parent.asset_type, parent.asset_name), []),
                                     key=lambda d: d.dup_index))
        for item in self.items:
            item.is_frozen = (item.asset_type, item.asset_name, item.dup_index) in frozen
            manual = self._manual_versions.get(_row_package_key(item))
            if manual in item.versions:  # a rescan keeps the artist's pick
                item.selected_version = manual

        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            self._fill_row(row, item)

        self._refresh_filter_visibility()
        active = next((s for s, b in self.filter_buttons.items() if b.isChecked()), "All")
        if active != "All":
            self._apply_filter(active)
        self.refresh_banner()

    def _discover_foreign_assets(self):
        """Rows for Reads pointing at another shot's assets. These Reads are
        usually dragged in by hand, so the loader tag isn't required — the
        strict Prism path pattern keeps unrelated Reads out."""
        if not self.session.has_shot:
            return []
        found = {}
        for read in nuke.allNodes("Read"):
            info = asset_nodes.parse_asset_path(asset_nodes.file_path(read))
            if not info:
                continue
            if info["sequence"] == self.session.sequence and info["shot"] == self.session.shot:
                continue
            key = (info["sequence"], info["shot"], info["asset_type"], info["asset_name"])
            found.setdefault(key, ([], info))[0].append(read)  # one Read per layer

        items = []
        for (seq, shot, asset_type, asset_name), (reads, info) in found.items():
            folder = self.discoverer.asset_folder(seq, shot, asset_type, asset_name)
            if not folder or not os.path.isdir(folder):
                print(f"[ShotAssetLoader] Foreign asset path missing — skipping: {folder}")
                continue
            versions_dict = self.discoverer.discover_versions(folder)
            if not versions_dict:
                print(f"[ShotAssetLoader] No versions found for foreign asset {folder}")
                continue
            item = AssetItem(asset_type, asset_name, sorted(versions_dict), versions_dict, info["source_type"])
            item.is_foreign = True
            item.foreign_sequence, item.foreign_shot = seq, shot
            item.loaded_nodes = reads
            items.append(item)
            print(f"[ShotAssetLoader] Foreign {asset_type} '{asset_name}' from {seq}/{shot} "
                  f"({len(versions_dict)} version(s))")
        return items

    @staticmethod
    def _discover_scene_duplicates(parents):
        """{(type, name): [AssetItem]}: one row per clone of each parent row,
        holding the cloned node of every layer."""
        by_key = {(p.asset_type, p.asset_name): p for p in parents if p.dup_index == 0}
        rows, result = {}, {}
        for node, index, parent_type, parent_name in asset_nodes.iter_duplicates():
            parent = by_key.get((parent_type, parent_name))
            if parent is None:
                print(f"[ShotAssetLoader] Duplicate node {node.name()} points at unknown parent "
                      f"{parent_type}/{parent_name} — skipping")
                continue
            dup = rows.get((parent_type, parent_name, index))
            if dup is None:
                dup = AssetItem(parent.asset_type, parent.asset_name, parent.versions,
                                parent.versions_dict, parent.source_type)
                dup.dup_index = index
                version = extract_version_from_path(asset_nodes.file_path(node))
                if version in parent.versions:
                    dup.selected_version = version
                rows[(parent_type, parent_name, index)] = dup
                result.setdefault((parent_type, parent_name), []).append(dup)
            dup.loaded_nodes.append(node)
        return result

    def _fill_row(self, row, item):
        table = self.table
        table.setItem(row, COL_NAME, w.read_only_item(item.display_name(), bold=True))
        table.setItem(row, COL_TYPE, w.read_only_item(item.asset_type))

        versions = QtWidgets.QComboBox()
        versions.addItems(item.versions)
        versions.setCurrentText(item.selected_version)
        versions.currentTextChanged.connect(lambda v, it=item: self._on_version_changed(it, v))
        table.setCellWidget(row, COL_VERSION, versions)

        colorspaces = QtWidgets.QComboBox()
        colorspaces.addItems(self._ocio_colorspaces())
        colorspaces.setCurrentText(item.selected_colorspace)
        colorspaces.currentTextChanged.connect(lambda cs, it=item: self._on_colorspace_changed(it, cs))
        table.setCellWidget(row, COL_COLORSPACE, colorspaces)

        status_cell = w.read_only_item(item.status_text)
        if item.status_color:
            w.set_background(status_cell, item.status_color)
        status_cell.setToolTip(item.camera_mismatch or "")
        table.setItem(row, COL_STATUS, status_cell)

        freeze = w.icon_button("freezeButton", (22, 22), lambda _=False, it=item: self._toggle_freeze(it))
        self._paint_freeze_button(freeze, item)
        table.setCellWidget(row, COL_FREEZE, w.centered(freeze))

        if item.is_hidden:
            action = w.icon_button("recoverButton", (24, 22), lambda _=False, it=item: self._recover(it))
            action.setIcon(icons.recover_icon())
            action.setToolTip("Recover this asset — removes it from the hidden list in "
                              "the prefs JSON so it appears normally again." + _SELECTION_TIP)
        else:
            action = w.icon_button("hideButton", (24, 22), lambda _=False, it=item: self._hide(it))
            action.setIcon(icons.trash_icon())
            action.setToolTip("Hide this asset from the loader for the current shot.\n"
                              "Tick 'Show Hidden Assets' to see and recover it later." + _SELECTION_TIP)
        table.setCellWidget(row, COL_ACTION, w.centered(action))

    def _repaint_rows(self):
        for row, item in enumerate(self.items):
            self._paint_status(row, item)
            self._paint_freeze_cell(row, item)

    def _paint_status(self, row, item):
        cell = self.table.item(row, COL_STATUS)
        if cell is not None:
            cell.setText(item.status_text)
            w.set_background(cell, item.status_color)
            cell.setToolTip(item.camera_mismatch or "")

    def _paint_freeze_cell(self, row, item):
        cell = self.table.cellWidget(row, COL_FREEZE)
        btn = cell.findChild(QtWidgets.QPushButton) if cell is not None else None
        if btn is not None:
            self._paint_freeze_button(btn, item)

    @staticmethod
    def _paint_freeze_button(btn, item):
        loaded = item.loaded_node is not None
        btn.setEnabled(loaded)
        btn.setProperty("frozen", "true" if item.is_frozen else "false")
        btn.style().unpolish(btn)  # re-evaluate the [frozen="true"] rule
        btn.style().polish(btn)
        if not loaded:
            btn.setIcon(icons.snowflake_icon("#4a4a4a", False))
            btn.setToolTip("Freeze is only available on loaded assets")
        elif item.is_frozen:
            btn.setIcon(icons.snowflake_icon("#6ac3e0", True))
            btn.setToolTip("Frozen — this asset will be skipped by every update path.\nClick to unfreeze."
                           + _SELECTION_TIP)
        else:
            btn.setIcon(icons.snowflake_icon("#8ac8e0", False))
            btn.setToolTip("Freeze this asset to its currently-loaded version.\n"
                           "Frozen rows are ignored by Update Selected / Update All Loaded." + _SELECTION_TIP)

    def _row_of(self, item):
        for row, candidate in enumerate(self.items):
            if candidate is item:
                return row
        return None

    def _ocio_colorspaces(self):
        """["Auto", ...] from the OCIO config (or Nuke's native list), cached
        for the lifetime of the tab."""
        if self._colorspaces is None:
            self._colorspaces = ["Auto"] + _read_colorspaces()
        return self._colorspaces

    # ------------------------------------------------------------------
    # Row interactions
    # ------------------------------------------------------------------

    def _on_version_changed(self, item, version):
        item.selected_version = version
        self._manual_versions[_row_package_key(item)] = version
        status.apply_manual_selection(item)
        row = self._row_of(item)
        if row is not None:
            self._paint_status(row, item)

    def _on_colorspace_changed(self, item, colorspace):
        item.selected_colorspace = colorspace
        print(f"[ShotAssetLoader] Set colorspace for {item.asset_name} to {colorspace}")

    def _on_column_resized(self, logical_index, _old, _new):
        # Every column right of the dragged one moves too.
        model = self.table.model()
        for col in range(logical_index, self.table.columnCount()):
            for row in range(self.table.rowCount()):
                widget = self.table.cellWidget(row, col)
                if widget is not None:
                    widget.setGeometry(self.table.visualRect(model.index(row, col)))

    def _selected_items(self):
        """Items of the highlighted rows, excluding rows hidden by the filter."""
        rows = {idx.row() for idx in self.table.selectionModel().selectedRows()}
        return [self.items[r] for r in sorted(rows)
                if not self.table.isRowHidden(r) and r < len(self.items)]

    def _acted_on(self, item):
        """Rows a per-row button acts on: the whole selection when the
        clicked row is part of it, that row alone otherwise."""
        selected = self._selected_items()
        if len(selected) > 1 and any(it is item for it in selected):
            return selected
        return [item]

    def _select_all(self):
        w.select_rows(self.table, [r for r in range(self.table.rowCount()) if not self.table.isRowHidden(r)])

    def _apply_filter(self, source):
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == source)
        if source == "Loaded":
            self.refresh_status(silent=True)
        for row, item in enumerate(self.items):
            if source == "All":
                match = True
            elif source == "Loaded":
                match = item.loaded_node is not None
            elif source == "From Other Shots":
                match = item.is_foreign
            else:
                match = item.source_type == source
            self.table.setRowHidden(row, not match)
        # Load/Update Selected must only act on visible rows.
        selection = self.table.selectionModel()
        for index in list(selection.selectedRows()):
            if self.table.isRowHidden(index.row()):
                selection.select(index, QtCore.QItemSelectionModel.Deselect | QtCore.QItemSelectionModel.Rows)

    def _refresh_filter_visibility(self):
        """Hide source pills without matching rows ('All'/'Loaded' always
        shown); fall back to 'All' if the active pill disappears."""
        sources = {item.source_type for item in self.items}
        has_foreign = any(item.is_foreign for item in self.items)
        for source, btn in self.filter_buttons.items():
            if source in ("All", "Loaded"):
                btn.setVisible(True)
            elif source == "From Other Shots":
                btn.setVisible(has_foreign)
            else:
                btn.setVisible(source in sources)
        if any(b.isChecked() and not b.isVisible() for b in self.filter_buttons.values()):
            self._apply_filter("All")

    def _on_show_hidden_toggled(self, checked):
        self._show_hidden = bool(checked)
        self._rebuild()

    def _rebuild(self):
        """Repopulate, then re-bind the fresh rows to their scene nodes."""
        self._populate_table()
        self.refresh_status(silent=True)

    # ------------------------------------------------------------------
    # Hide / recover / freeze
    # ------------------------------------------------------------------

    def _hide(self, item):
        if not self.session.prefs.available:
            QtWidgets.QMessageBox.warning(
                self, "Cannot Hide Asset",
                "No prefs file available for this project.\n"
                "Save your script inside a detected project so the loader can persist hidden-asset choices.")
            return
        if not self.session.has_shot:
            return
        for it in self._acted_on(item):
            if it.is_hidden:
                continue
            self.session.prefs.hide(self.session.shot_key, it.asset_type, it.asset_name)
            print(f"[ShotAssetLoader] Hidden '{it.asset_type}/{it.asset_name}' from "
                  f"{self.session.shot_key} — restore by editing {self.session.prefs.path}")
        self._rebuild()

    def _recover(self, item):
        if not self.session.has_shot:
            return
        recovered = False
        for it in self._acted_on(item):
            if it.is_hidden and self.session.prefs.unhide(self.session.shot_key, it.asset_type, it.asset_name):
                print(f"[ShotAssetLoader] Recovered '{it.asset_type}/{it.asset_name}' in {self.session.shot_key}")
                recovered = True
        if recovered:
            self._rebuild()

    def _toggle_freeze(self, item):
        """Freeze pins the loaded version: only meaningful on a loaded row.
        The clicked row gives the direction, the selection follows it."""
        if item.loaded_node is None:
            return
        frozen = not item.is_frozen
        items = [it for it in self._acted_on(item) if it.loaded_node is not None]
        self._set_frozen(items, frozen)
        print(f"[ShotAssetLoader] {'Froze' if frozen else 'Unfroze'} {', '.join(it.label() for it in items)}")

    def _set_frozen(self, items, frozen):
        for item in items:
            if item.loaded_node is None or item.is_frozen == frozen:
                continue
            item.is_frozen = frozen
            if self.session.has_shot:
                self.session.prefs.set_frozen(self.session.shot_key, item.asset_type,
                                              item.asset_name, item.dup_index, frozen)
        self.refresh_status(silent=True)

    # ------------------------------------------------------------------
    # Packages
    # ------------------------------------------------------------------

    def _refresh_package_combo(self):
        """List the shot's packages, pre-selecting the pinned current one."""
        combo = self.package_combo
        packages = self.session.prefs.packages(self.session.shot_key) if self.session.has_shot else []
        combo.blockSignals(True)
        combo.clear()
        if packages:
            for pkg in packages:
                name = pkg.get("name", "?")
                combo.addItem(f"{name}    ({pkg.get('compo_version') or '?'} / {pkg.get('date') or '?'})", name)
            current = self.session.prefs.current_package(self.session.shot_key)
            index = combo.findData(current) if current else -1
            combo.setCurrentIndex(index if index >= 0 else combo.count() - 1)
        else:
            combo.addItem("(no packages yet)")
        combo.setEnabled(bool(packages))
        self.choose_package_btn.setEnabled(bool(packages))
        combo.blockSignals(False)

    def _save_package(self):
        """Snapshot the scene's asset versions after a successful Load/Update."""
        if not self.session.prefs.available or not self.session.has_shot or not self.items:
            return
        snapshot = []
        for item in self.items:
            # What the scene holds; the dropdown for rows not loaded yet.
            loaded = item.loaded_node is not None and item.loaded_version not in (None, "v000")
            version = item.loaded_version if loaded else item.selected_version
            if not version:
                continue
            entry = {"type": item.asset_type, "name": item.asset_name, "version": version}
            if item.is_foreign:
                entry["foreign_sequence"] = item.foreign_sequence
                entry["foreign_shot"] = item.foreign_shot
            if item.dup_index:
                entry["copy"] = item.dup_index
            snapshot.append(entry)
        if not snapshot:
            return
        compo_version = project.script_version(scene.script_path()) or ""
        date = datetime.date.today().strftime("%d/%m/%y")
        name = self.session.prefs.add_package(self.session.shot_key, snapshot, compo_version, date)
        if name:
            print(f"[ShotAssetLoader] Saved snapshot {name} ({compo_version or '?'} / {date}) for "
                  f"{self.session.shot_key} — {len(snapshot)} asset(s)")
        self._refresh_package_combo()

    def _choose_package(self):
        """Apply a package: set every row's dropdown to its recorded version
        and update the loaded nodes that differ."""
        packages = self.session.prefs.packages(self.session.shot_key) if self.session.has_shot else []
        index = self.package_combo.currentIndex()
        if not 0 <= index < len(packages):
            return
        pkg = packages[index]
        pkg_name = pkg.get("name", "package")
        entries = pkg.get("assets", [])
        if not entries:
            QtWidgets.QMessageBox.information(self, "Empty Package", f"{pkg_name} has no assets recorded.")
            return

        wanted = {_package_key(e): e["version"] for e in entries if e.get("version")}
        adjusted, missing_on_disk = [], []
        for row, item in enumerate(self.items):
            target = wanted.pop(_row_package_key(item), None)
            if not target:
                continue
            if target not in item.versions:
                missing_on_disk.append(f"{item.asset_type} / {item.asset_name} ({target})")
                continue
            item.selected_version = target
            combo = self.table.cellWidget(row, COL_VERSION)
            if isinstance(combo, QtWidgets.QComboBox):
                combo.blockSignals(True)
                combo.setCurrentText(target)
                combo.blockSignals(False)
            adjusted.append(item)
        not_in_table = [f"{key[0]} / {key[1]} ({version})" for key, version in wanted.items()]

        to_update = [it for it in adjusted if it.loaded_node and it.loaded_version != it.selected_version]
        if to_update:
            for item in to_update:
                item.update_target_version = item.selected_version
                item.has_update = True
            if not self._perform_updates(to_update, "package",
                                         f"Apply {pkg_name} to {len(to_update)} loaded asset(s)?",
                                         save_snapshot=False):
                return
        else:
            for item in adjusted:
                if not item.is_frozen:  # frozen rows keep their "Freeze" status
                    status.apply_manual_selection(item)
            self._repaint_rows()

        self.session.prefs.set_current_package(self.session.shot_key, pkg_name)
        self._refresh_package_combo()

        warnings = []
        if missing_on_disk:
            warnings.append("Versions from the package no longer available on disk:\n  - "
                            + "\n  - ".join(missing_on_disk[:10]))
        if not_in_table:
            warnings.append("Assets recorded in the package but not in the current table "
                            "(hidden or removed):\n  - " + "\n  - ".join(not_in_table[:10]))
        if warnings:
            QtWidgets.QMessageBox.warning(self, f"{pkg_name} — Partial Apply", "\n\n".join(warnings))

    # ------------------------------------------------------------------
    # Load / update
    # ------------------------------------------------------------------

    def _load_selected(self):
        selected = self._selected_items()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets selected")
            return
        self._load(selected)

    def _load_all(self):
        if not self.items:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets to load")
            return
        self._load(self.items)

    def _script_matches(self) -> bool:
        """Load / update / duplicate write into the current script: refuse
        when it isn't the shot this dialog was opened on (possible while the
        auto-refresh, which reopens the dialog, is paused)."""
        if self.session.follows(scene.script_path()):
            return True
        QtWidgets.QMessageBox.warning(
            self, "Script changed",
            f"The open script is not {self.session.shot_key} any more.\n"
            "Resume the auto-refresh or reopen the Shot Loader.")
        return False

    def _load(self, items):
        if not self._script_matches():
            return
        self.refresh_status(silent=True)  # accurate "already loaded" detection

        # A v000 camera (Camera3 without file) is filled in by Load.
        cameras = [it for it in items if it.asset_type == "Camera" and it.loaded_node is not None
                   and it.loaded_version == "v000" and it.has_update]
        already_loaded = [it for it in items if it.loaded_node is not None and it not in cameras]
        to_load = [it for it in items if it.loaded_node is None]

        if not to_load and not cameras:
            names = ", ".join(f"{it.asset_type} '{it.asset_name}'" for it in already_loaded[:5])
            more = f" (+{len(already_loaded) - 5} more)" if len(already_loaded) > 5 else ""
            QtWidgets.QMessageBox.information(
                self, "Nothing to Load",
                f"All {len(items)} selected asset(s) are already in the script:\n{names}{more}")
            return

        updated_cameras, error = [], None
        with scene.undo_group("Load shot assets"):
            for camera in cameras:
                try:
                    if self._apply_update(camera, frame_range=None):
                        updated_cameras.append(camera)
                except Exception as e:
                    print(f"[ShotAssetLoader] Error updating camera {camera.asset_name} from v000: {e}")
            if to_load:
                assets, colorspaces = _load_request(to_load)
                try:
                    self.builder.load_assets(self.session.sequence, self.session.shot, assets,
                                             asset_colorspaces=colorspaces, project_root=self.session.project_root)
                    # Existing wired stamps re-latch onto the anchors just created.
                    try:
                        reconnect_postage_stamps(silent=True)
                    except Exception as e:
                        print(f"[ShotAssetLoader] reconnect_stamps failed (non-fatal): {e}")
                except Exception as e:
                    error = e
                    print(f"[ShotAssetLoader] Error: {e}")
                    traceback.print_exc()
        self.refresh_status(silent=True)

        camera_note = f"\n\nUpdated {len(updated_cameras)} camera(s) from v000 to latest." if updated_cameras else ""
        skipped_note = f"\n\nSkipped {len(already_loaded)} already-loaded asset(s)." if already_loaded else ""
        if error is not None:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error loading assets:\n{error}")
        elif not to_load:
            QtWidgets.QMessageBox.information(
                self, "Success", f"Updated {len(updated_cameras)} camera(s) from v000 to latest.{skipped_note}")
        else:
            QtWidgets.QMessageBox.information(
                self, "Success",
                f"Successfully loaded {len(self.builder.created_nodes)} node(s) for "
                f"{self.session.sequence}/{self.session.shot}{camera_note}{skipped_note}")
            self._save_package()

    def _apply_update(self, item, frame_range) -> bool:
        """Point every node of the item (one per layer / file) at the same
        layer of the update target version. The dropdown pick is applied:
        from now on the status reflects what is loaded."""
        self._manual_versions.pop(_row_package_key(item), None)
        target = item.update_target_version or item.versions[-1]
        version_data = item.versions_dict[target]
        ok = True
        for node in item.loaded_nodes:
            folder = version_data  # cameras: the version folder itself
            if isinstance(version_data, dict):
                folder = asset_nodes.layer_folder(node, version_data)
                if folder is None and len(version_data) == 1 and len(item.loaded_nodes) == 1:
                    folder = first_layer_path(version_data)  # single layer, folder layout changed
                if folder is None:
                    print(f"[ShotAssetLoader] {item.label()}: {target} has no layer for "
                          f"{node.name()} — left on its current version")
                    ok = False
                    continue
            if self.builder.update_node_version(node, folder, frame_range):
                asset_nodes.reload_read(node)
            else:
                ok = False
        if ok:
            status.mark_up_to_date(item, target)
        return ok

    def _check_for_updates_clicked(self):
        """Manual check: rescan disk (new versions / passes) then report."""
        self.coverage.clear()
        self.scan()
        self.refresh_status(silent=False)

    def _update_selected(self):
        selected = self._selected_items()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets selected")
            return
        self._perform_updates(selected, "selected")

    def _update_all_loaded(self):
        if not self.items:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets to update")
            return
        self.refresh_status(silent=True)
        self._perform_updates(self.items, "loaded")

    def _perform_updates(self, items, scope, confirm_message=None, save_snapshot=True) -> bool:
        """Update the loaded, non-frozen items flagged with an update.
        Returns False when there was nothing to do or the user cancelled."""
        if not self._script_matches():
            return False
        updatable = [it for it in items if it.has_update and it.loaded_node and not it.is_frozen]
        if not updatable:
            QtWidgets.QMessageBox.information(self, "No Updates", f"No {scope} assets have updates available")
            return False
        changes = [f"  {it.label()}: {_update_line(it)}" for it in updatable[:12]]
        if len(updatable) > 12:
            changes.append(f"  ... and {len(updatable) - 12} more")
        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Update",
            (confirm_message or f"Update {len(updatable)} asset(s)?") + "\n\n" + "\n".join(changes),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply != QtWidgets.QMessageBox.Yes:
            return False

        scene_range = scene.scene_frame_range()
        updated, failed = 0, []
        with scene.undo_group("Update shot assets"):
            for item in updatable:
                try:
                    # Foreign Reads keep their own (possibly retimed) range.
                    if self._apply_update(item, None if item.is_foreign else scene_range):
                        updated += 1
                    else:
                        failed.append(f"{item.asset_type} - {item.asset_name}")
                except Exception as e:
                    failed.append(f"{item.asset_type} - {item.asset_name}: {e}")
                    print(f"[ShotAssetLoader] Error updating {item.asset_name}: {e}")

        self.refresh_status(silent=True)
        message = f"Successfully updated {updated} asset(s)"
        if failed:
            message += f"\n\nFailed to update {len(failed)} asset(s):\n" + "\n".join(failed[:5])
            if len(failed) > 5:
                message += f"\n... and {len(failed) - 5} more"
        QtWidgets.QMessageBox.information(self, "Update Complete", message)
        if save_snapshot and updated:
            self._save_package()
        return True

    # ------------------------------------------------------------------
    # Duplicate
    # ------------------------------------------------------------------

    def _duplicate_selected(self):
        selected = self._selected_items()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets selected")
            return
        loaded = [it for it in selected if it.loaded_node is not None]
        if not loaded:
            QtWidgets.QMessageBox.information(
                self, "Nothing to Duplicate", "Selected assets aren't loaded in the scene — nothing to clone.")
            return
        if not self._script_matches():
            return
        with scene.undo_group("Duplicate shot assets"):
            created = sum(1 for it in loaded if self._duplicate(it))
        self._populate_table()
        self.refresh_status(silent=True)
        print(f"[ShotAssetLoader] Duplicated {created} asset(s)")

    def _duplicate(self, item):
        """Clone the item's nodes (one per layer / file) with their
        ILGC_ReadCleanup, add fresh stamps titled '<anchor title>_copy_NN'
        and tag the clones so the next populate lists them as one row under
        the parent. Returns the cloned nodes."""
        # Copies of a copy keep numbering within the parent's family.
        index = asset_nodes.next_dup_index(item.asset_type, item.asset_name)
        suffix = f"_copy_{index:02d}"
        default_title = {"Roto": f"Roto_{item.selected_version}", "Camera": "cam"}.get(
            item.asset_type, item.asset_name)
        clones = []
        for source in item.loaded_nodes:
            clone = asset_nodes.clone_node(source)
            if clone is None:
                continue
            clone.setName(f"{source.name()}{suffix}", uncollide=True)
            clone.setXYpos(source.xpos() + 200, source.ypos())
            asset_nodes.tag_as_loader_owned(clone)
            asset_nodes.write_dup_metadata(clone, index, item.asset_type, item.asset_name)

            stamp_source, original = clone, source
            cleanup = asset_nodes.find_downstream_cleanup(source)
            if cleanup is not None:
                cleanup_clone = asset_nodes.clone_node(cleanup)
                if cleanup_clone is not None:
                    cleanup_clone.setName(f"{cleanup.name()}{suffix}", uncollide=True)
                    cleanup_clone.setXYpos(cleanup.xpos() + clone.xpos() - source.xpos(),
                                           cleanup.ypos() + clone.ypos() - source.ypos())
                    cleanup_clone.setInput(0, clone)
                    asset_nodes.tag_as_loader_owned(cleanup_clone)
                    stamp_source, original = cleanup_clone, cleanup

            title = anchor_title(original) or default_title
            self.builder.create_stamps(stamp_source, f"{title}{suffix}", stamp_source is not clone)
            print(f"[ShotAssetLoader] Duplicated {item.label()} → {clone.name()} (copy_{index:02d})")
            clones.append(clone)
        return clones

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if not 0 <= row < len(self.items):
            return
        w.ensure_row_selected(self.table, row)
        items = self._selected_items() or [self.items[row]]
        loaded = [it for it in items if it.loaded_node is not None]

        menu = QtWidgets.QMenu(self)
        menu.addAction("Open in Explorer" if len(items) <= 1 else "Open Selected in Explorer").triggered.connect(
            lambda _=False, its=list(items): w.open_in_explorer(
                self, [(f"{it.asset_type} / {it.asset_name}", it.folder(it.selected_version)) for it in its]))
        menu.addSeparator()
        menu.addAction("Load Selected").triggered.connect(self._load_selected)
        menu.addAction("Update Selected").triggered.connect(self._update_selected)
        menu.addSeparator()
        if loaded:
            all_frozen = all(it.is_frozen for it in loaded)
            menu.addAction("Unfreeze Selected" if all_frozen else "Freeze Selected").triggered.connect(
                lambda _=False, its=list(loaded), target=not all_frozen: self._set_frozen(its, target))
            menu.addAction("Duplicate Selected").triggered.connect(self._duplicate_selected)
        else:
            menu.addAction("Freeze (no loaded asset in selection)").setEnabled(False)
            menu.addAction("Duplicate (no loaded asset in selection)").setEnabled(False)
        menu.exec_(self.table.viewport().mapToGlobal(position))


_SELECTION_TIP = "\nOn a selected row: applies to every selected row."


def _load_request(items):
    """(assets in AssetDiscoverer layout, colorspace overrides) for the
    builder: the selected version of each item."""
    assets = {key: {} for key in DISCOVERY_KEYS.values()}
    colorspaces = {}
    for item in items:
        version = item.selected_version
        if item.selected_colorspace and item.selected_colorspace != "Auto":
            colorspaces[colorspace_key(item.asset_type, item.asset_name, version)] = item.selected_colorspace
        key = DISCOVERY_KEYS.get(item.asset_type)
        if key == "rotos":
            assets[key][version] = item.versions_dict[version]
        elif key:
            assets[key][item.asset_name] = {version: item.versions_dict[version]}
    return assets, colorspaces


def _read_colorspaces():
    """Colorspace names of the active color management (without "Auto")."""
    try:
        root = nuke.root()
        if root.knob('colorManagement') is None:
            print("[ShotAssetLoader] Warning: colorManagement knob not found in root node")
            return list(_FALLBACK_COLORSPACES)
        mode = root['colorManagement'].value()
        if mode != "OCIO":
            print(f"[ShotAssetLoader] Using Nuke native colorspaces (mode: {mode})")
            return list(_NUKE_COLORSPACES)
        try:
            import PyOpenColorIO as OCIO  # type: ignore
            config = OCIO.GetCurrentConfig()
            if hasattr(config, 'getColorSpaces'):          # OCIO v2
                names = [cs.getName() for cs in config.getColorSpaces()]
            elif hasattr(config, 'getNumColorSpaces'):     # OCIO v1
                names = [config.getColorSpaceNameByIndex(i) for i in range(config.getNumColorSpaces())]
            else:
                raise AttributeError("Unknown OCIO API version")
            print(f"[ShotAssetLoader] Loaded {len(names)} colorspaces from OCIO config")
            return names
        except ImportError:
            print("[ShotAssetLoader] PyOpenColorIO not available, using fallback OCIO colorspace list")
        except Exception as e:
            print(f"[ShotAssetLoader] Error loading OCIO config: {e}")
        return list(_OCIO_FALLBACK)
    except Exception as e:
        print(f"[ShotAssetLoader] Unexpected error getting colorspaces: {e}")
        return list(_FALLBACK_COLORSPACES)
