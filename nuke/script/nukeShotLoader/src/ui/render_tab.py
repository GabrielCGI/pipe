"""Render Manager tab: PrecompWrite / Compo Write overview and farm submission."""

import os

import nuke

from ..core.versions import extract_version_from_path
from ..precomp import engine
from ..precomp import nodes as precomp_nodes
from ..precomp.engine import Status
from .qt import QtCore, QtGui, QtWidgets
from ..scene import render_ops
from ..scene.utils import knob_value, script_path
from .render_flow import NOT_RENDERABLE as _NOT_RENDERABLE, RenderFlow
from . import styles
from . import widgets as w

COL_NAME, COL_IDENTIFIER, COL_VERSION, COL_ORDER, COL_STATUS, COL_FORCE = range(6)
_SHARED_WIDTHS = (220, 220, 80, 110)   # Name, Identifier, Version, Render Order
IDENTIFIER_PREFIX = "precomp_"

_STATUS_COLORS = {
    Status.CACHED: "#3a5a3a",
    Status.LIVE: "#aa2c2c",
    Status.RENDERING: "#8a6a2a",
    Status.LEGACY: "#6a5a2a",
    Status.ERROR: "#aa2c2c",
    Status.NO_INPUT: "#3a3a3a",
}
_OUT_OF_STREAM_COLOR = "#3a3a3a"
# Write knobs the table cells are built from (name / identifier / version / order).
_SHOWN_KNOBS = ("identifier", "versions", "fileName", "file", "render_order")
_DUPLICATE_BG = "#7a3a3a"
_DUPLICATE_FG = "#f5d6d6"
_FORCE_TIP = ("Force Live: move to the next version and ignore the existing renders, so this\n"
              "precomp (and the precomps downstream) go live even when nothing changed in the\n"
              "graph — e.g. a source file re-rendered in place. The next render goes to that version.\n"
              "Click again before rendering to cancel: previous version and cache come back.\n"
              "On a selected row: applies to every selected row.")
_FORCE_ON_TIP = ("Forced live — click to cancel (back to the previous version and its cache).\n"
                 "On a selected row: applies to every selected row.")
# Cell widgets get the row height minus the 2 x 6px item padding of the
# stylesheet: 34px rows fit the 22px Force Live button (as in the Loader).
_PRECOMP_ROW_HEIGHT = 34


class RenderManagerTab(QtWidgets.QWidget):

    def __init__(self, session, console, parent=None):
        super().__init__(parent)
        self.session = session
        self._console = console
        self._states = {}           # write fullName -> PrecompState
        self._out_of_stream = set()
        self._last_view = None      # what the tables show (see _view)
        self._flow = RenderFlow(session, self, on_submitted=self.request_refresh, on_upgrade=self._upgrade)
        self._edit_busy = False     # guards itemChanged against our own writes
        self._column_link_busy = False
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
        layout.addWidget(self.banner)

        self.precomp_table = self._make_table(["Name", "Identifier", "Version", "Render Order", "Status", "Force Live"])
        self.precomp_table.verticalHeader().setDefaultSectionSize(_PRECOMP_ROW_HEIGHT)
        header = self.precomp_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(COL_STATUS, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(COL_FORCE, QtWidgets.QHeaderView.Fixed)
        self.precomp_table.setColumnWidth(COL_FORCE, 112)
        self.precomp_table.setItemDelegateForColumn(COL_STATUS, w.StatusColorDelegate(self.precomp_table))
        self.precomp_table.setItemDelegateForColumn(COL_IDENTIFIER, w.IdentifierDelegate(parent=self.precomp_table))
        self.precomp_table.setItemDelegateForColumn(COL_NAME, w.TallEditorDelegate(parent=self.precomp_table))
        self.precomp_table.itemChanged.connect(self._on_item_changed)
        self.precomp_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.precomp_table.customContextMenuRequested.connect(self._show_context_menu)

        # Shown only while some precomps don't feed the Compo Write.
        self.out_of_stream_row = QtWidgets.QWidget()
        out_layout = QtWidgets.QHBoxLayout(self.out_of_stream_row)
        out_layout.setContentsMargins(0, 4, 0, 0)
        out_layout.setSpacing(8)
        self.render_all_out_btn = w.button(
            "Render All Out of Stream", self._render_all_out_of_stream, "updateAction",
            "Render the Live out-of-stream precomps (not feeding the Compo Write),\n"
            "in the order of their dependencies on each other.")
        self.render_selected_out_btn = w.button(
            "Render Selected Out of Stream", self._render_selected_out_of_stream, "selectedAction",
            "Render the selected out-of-stream precomps, even when cached.")
        out_layout.addWidget(self.render_all_out_btn)
        out_layout.addWidget(self.render_selected_out_btn)
        out_layout.addStretch()
        self.out_of_stream_row.setVisible(False)
        layout.addWidget(self._group("WRITES PRECOMP", self.precomp_table, self.out_of_stream_row), stretch=1)

        # Same 5 columns as the precomp table so both align; there is a
        # single compo Write, hence no selection.
        self.compo_table = self._make_table(["Name", "Identifier", "Version", "Render Order", ""])
        self.compo_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.compo_table.setFocusPolicy(QtCore.Qt.NoFocus)
        layout.addWidget(self._group("WRITES COMPO", self.compo_table), stretch=0)
        self._link_column_widths(self.precomp_table, self.compo_table)

        actions = QtWidgets.QHBoxLayout()
        actions.addWidget(w.button("Render Compo", self._render_compo, "secondaryAction"))
        self.render_all_btn = w.button("Render Compo and Precomps", self._render_all, "primaryAction")
        self.render_precomps_btn = w.button("Render Precomps", self._render_precomps, "updateAction")
        self.render_selected_btn = w.button("Render Selected", self._render_selected, "selectedAction")
        for btn in (self.render_all_btn, self.render_precomps_btn, self.render_selected_btn):
            actions.addWidget(btn)
        actions.addStretch()
        self.upgrade_btn = w.button(
            "Upgrade Precomps", self._upgrade, "warningAction",
            "This script uses the v1 precomp setup (Python expression switches and render\n"
            "hooks). Upgrade it to v2 before rendering.")
        self.upgrade_btn.setVisible(False)
        actions.addWidget(self.upgrade_btn)
        actions.addWidget(w.button("Refresh", self.request_refresh))
        layout.addLayout(actions)

    @staticmethod
    def _make_table(columns):
        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(28)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setStretchLastSection(True)
        for col, width in enumerate(_SHARED_WIDTHS):
            table.setColumnWidth(col, width)
        return table

    @staticmethod
    def _group(title, *widgets):
        group = QtWidgets.QGroupBox(title)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(6, 4, 6, 6)
        for widget in widgets:
            layout.addWidget(widget)
        return group

    def _link_column_widths(self, table_a, table_b):
        """Dragging a shared column header in one table resizes the other."""
        def mirror(target):
            def sync(column, _old, new):
                if column >= len(_SHARED_WIDTHS) or self._column_link_busy or target.columnWidth(column) == new:
                    return
                self._column_link_busy = True
                try:
                    target.setColumnWidth(column, new)
                finally:
                    self._column_link_busy = False
            return sync

        table_a.horizontalHeader().sectionResized.connect(mirror(table_b))
        table_b.horizontalHeader().sectionResized.connect(mirror(table_a))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_refresh(self):
        """Refresh with de-duplicated logs: an unchanged graph prints nothing."""
        self._console.run_deduped(self._refresh, "render_manager")

    def refresh_banner(self, precomp_count=None):
        if precomp_count is None:
            precomp_count = sum(1 for _ in precomp_nodes.iter_precomp_writes())
        self.banner.show_shot(self.session, "PRECOMPS", precomp_count)

    def height_delta(self):
        rows = self.precomp_table.rowCount()
        return w.fit_height_delta(self.precomp_table, rows) if rows else 0

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def _refresh(self):
        if self.precomp_table.state() == QtWidgets.QAbstractItemView.EditingState:
            return  # a name / identifier being typed would be lost: next refresh
        precomps, compos = render_ops.scan_writes()
        compo = compos[0] if compos else None

        states = engine.sync()  # also routes every switch to what is valid on disk
        self._states = {s.name: s for s in states}
        for state in states:
            print(f"[precomp] {state.name}: {state.label}" + (f" — {state.reason}" if state.reason else ""))
        render_ops.distribute_render_orders(compo)
        self._out_of_stream = render_ops.order_out_of_stream(precomps, compo)
        self.upgrade_btn.setVisible(any(s.status == Status.LEGACY for s in states))

        precomps.sort(key=_ypos)  # top of the DAG first
        view = self._view(precomps, compos)
        if view != self._last_view:  # rebuilt only when something shown changed
            self._last_view = view
            precomp_selection = self._selected_fullnames(self.precomp_table)
            compo_selection = self._selected_fullnames(self.compo_table)
            self._populate_precomps(precomps)
            self._populate_compos(compos)
            self._restore_selection(self.precomp_table, precomp_selection)
            self._restore_selection(self.compo_table, compo_selection)
            self._fit_compo_table()
            self._refresh_warnings()
        self.refresh_banner(len(precomps))
        self._refresh_out_of_stream_row()

    def _view(self, precomps, compos):
        """Everything the two tables display. The 15s refresh rebuilds them
        only when this changes: no flicker, no row widgets recreated."""
        def write_view(node):
            return (node.fullName(),) + tuple(knob_value(node, k) for k in _SHOWN_KNOBS)

        def state_view(node):
            state = self._states.get(node.fullName())
            return None if state is None else (state.status, state.label, state.reason, state.forced)

        return (tuple(write_view(n) + (state_view(n), n.fullName() in self._out_of_stream) for n in precomps),
                tuple(write_view(n) for n in compos))

    def _populate_precomps(self, nodes):
        table = self.precomp_table
        self._edit_busy = True
        try:
            table.setRowCount(0)
            table.setRowCount(len(nodes))
            for row, node in enumerate(nodes):
                is_out = node.fullName() in self._out_of_stream
                state = self._states.get(node.fullName())
                table.setItem(row, COL_NAME, _name_cell(node, editable=True))
                table.setItem(row, COL_IDENTIFIER, _identifier_cell(node, IDENTIFIER_PREFIX, editable=True))
                table.setItem(row, COL_VERSION, _version_cell(node))
                table.setItem(row, COL_ORDER, _render_order_cell(node))
                label = state.label if state is not None else "?"
                color = _STATUS_COLORS.get(state.status) if state is not None else None
                if is_out:  # same status colour, pulled toward grey
                    label, color = f"Out of stream ({label})", _toward_grey(color or _OUT_OF_STREAM_COLOR)
                status_cell = w.read_only_item(label)
                status_cell.setToolTip(state.reason if state is not None else "")
                if color:
                    status_cell.setBackground(QtGui.QColor(color))
                table.setItem(row, COL_STATUS, status_cell)
                table.setCellWidget(row, COL_FORCE, w.centered(self._force_button(node, state)))
                if is_out:  # inert write: greyed out (foreground only)
                    grey = QtGui.QBrush(QtGui.QColor(styles.GREY_TEXT))
                    for col in range(COL_STATUS):
                        table.item(row, col).setForeground(grey)
        finally:
            self._edit_busy = False

    def _populate_compos(self, nodes):
        table = self.compo_table
        table.setRowCount(0)
        table.setRowCount(len(nodes))
        for row, node in enumerate(nodes):
            table.setItem(row, COL_NAME, _name_cell(node))
            table.setItem(row, COL_IDENTIFIER, _identifier_cell(node))
            table.setItem(row, COL_VERSION, _version_cell(node))
            table.setItem(row, COL_ORDER, _render_order_cell(node))

    def _fit_compo_table(self):
        """Height for 1 to 4 rows: a single compo Write shouldn't take half the tab."""
        table = self.compo_table
        rows = max(1, min(4, table.rowCount()))
        height = ((table.horizontalHeader().height() or 30) + table.verticalHeader().defaultSectionSize() * rows
                  + table.frameWidth() * 2 + 6)
        table.setMinimumHeight(height)
        table.setMaximumHeight(height)

    def _refresh_warnings(self):
        """Flag in-stream precomps sharing an identifier (red cell + icon)
        and block the precomp render buttons until it's resolved. Empty
        identifiers and out-of-stream writes never conflict."""
        table = self.precomp_table
        groups = {}
        for row in range(table.rowCount()):
            cell = table.item(row, COL_IDENTIFIER)
            if cell is None or self._row_fullname(table, row) in self._out_of_stream:
                continue
            raw = cell.data(w.RAW_ROLE) or ""
            if raw:
                groups.setdefault(raw, []).append(row)
        duplicates = {row for rows in groups.values() if len(rows) > 1 for row in rows}

        self._edit_busy = True
        try:
            for row in range(table.rowCount()):
                cell = table.item(row, COL_IDENTIFIER)
                if cell is None:
                    continue
                is_duplicate = row in duplicates
                cell.setData(w.WARNING_ROLE, is_duplicate)
                if is_duplicate:
                    cell.setBackground(QtGui.QBrush(QtGui.QColor(_DUPLICATE_BG)))
                    cell.setForeground(QtGui.QBrush(QtGui.QColor(_DUPLICATE_FG)))
                    cell.setToolTip("Duplicate identifier — another Precomp Write in the scene shares "
                                    "this name. Rename one of them before rendering.")
                else:
                    cell.setBackground(QtGui.QBrush())
                    out = self._row_fullname(table, row) in self._out_of_stream
                    cell.setForeground(QtGui.QBrush(QtGui.QColor(styles.GREY_TEXT)) if out else QtGui.QBrush())
                    cell.setToolTip("")
        finally:
            self._edit_busy = False

        # v1 precomps don't block: rendering offers to upgrade them first.
        if duplicates:
            reason = ("Two or more Precomp writes share the same identifier — "
                      "rename one of the duplicated rows to unlock rendering.")
        else:
            reason = ""
        for btn in (self.render_all_btn, self.render_precomps_btn, self.render_selected_btn):
            btn.setEnabled(not reason)
            btn.setToolTip(reason)

    def _refresh_out_of_stream_row(self):
        """The out-of-stream buttons exist only while some precomps don't
        feed the Compo Write."""
        self.out_of_stream_row.setVisible(bool(self._out_of_stream))

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_fullname(table, row):
        item = table.item(row, COL_NAME)
        return item.data(w.NODE_ROLE) if item is not None else None

    def _selected_fullnames(self, table):
        rows = sorted({idx.row() for idx in table.selectionModel().selectedRows()})
        return [name for name in (self._row_fullname(table, r) for r in rows) if name]

    def _restore_selection(self, table, fullnames):
        wanted = set(fullnames)
        rows = [r for r in range(table.rowCount()) if self._row_fullname(table, r) in wanted]
        if rows:
            w.select_rows(table, rows, clear=False)

    def _selected_nodes(self, table):
        """Nodes of the selected rows, resolved by fullName at call time so
        a renamed/deleted node is dropped instead of crashing."""
        return [n for n in (nuke.toNode(name) for name in self._selected_fullnames(table)) if n is not None]

    # ------------------------------------------------------------------
    # Inline edits (Name / Identifier)
    # ------------------------------------------------------------------

    def _on_item_changed(self, item):
        if self._edit_busy:
            return
        if item.column() == COL_NAME:
            self._rename_node(item)
        elif item.column() == COL_IDENTIFIER:
            self._set_identifier(item)

    def _set_text(self, item, text):
        self._edit_busy = True
        try:
            item.setText(text)
        finally:
            self._edit_busy = False

    def _rename_node(self, item):
        """Rename the node; a name already used in the same group is refused
        (Nuke would silently add a numeric suffix otherwise)."""
        old_full = item.data(w.NODE_ROLE) or ""
        old_name = item.data(w.RAW_ROLE) or ""
        new_name = (item.text() or "").strip()
        if new_name == old_name and new_name:
            return
        node = nuke.toNode(old_full)
        if not new_name or node is None:
            self._set_text(item, old_name)
            return

        parent_prefix = old_full.rsplit('.', 1)[0] + '.' if '.' in old_full else ''
        existing = nuke.toNode(f"{parent_prefix}{new_name}")
        if existing is not None and existing.fullName() != old_full:
            self._refuse_name(item, old_name)
            return
        try:
            node.setName(new_name)
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to rename {old_full} -> {new_name}: {e}")
            self._set_text(item, old_name)
            return
        if node.name() != new_name:  # Nuke auto-suffixed anyway
            try:
                node.setName(old_name)
            except Exception:
                pass
            self._refuse_name(item, old_name)
            return

        new_full = node.fullName()
        print(f"[ShotAssetLoader] Renamed {old_full} -> {new_full}")
        self._edit_busy = True
        try:
            item.setData(w.NODE_ROLE, new_full)
            item.setData(w.RAW_ROLE, new_name)
            identifier = self.precomp_table.item(item.row(), COL_IDENTIFIER)
            if identifier is not None:
                identifier.setData(w.NODE_ROLE, new_full)
        finally:
            self._edit_busy = False

    def _refuse_name(self, item, old_name):
        QtWidgets.QMessageBox.warning(self, "Name already used", "this name is already used")
        self._set_text(item, old_name)

    def _set_identifier(self, item):
        """Write the edited identifier (without the UI prefix) to the node's
        `identifier` knob; the cell always shows the prefixed form."""
        full_name = item.data(w.NODE_ROLE) or ""
        prefix = item.data(w.PREFIX_ROLE) or ""
        old_raw = item.data(w.RAW_ROLE) or ""
        text = (item.text() or "").strip()
        new_raw = text[len(prefix):] if prefix and text.startswith(prefix) else text
        canonical = f"{prefix}{new_raw}" if new_raw else ""
        previous = f"{prefix}{old_raw}" if old_raw else ""

        if new_raw == old_raw:
            if text != canonical:
                self._set_text(item, canonical)
            return
        node = nuke.toNode(full_name)
        if node is None or node.knob('identifier') is None:
            self._set_text(item, previous)
            return
        try:
            node['identifier'].setValue(new_raw)
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to set identifier on {full_name}: {e}")
            self._set_text(item, previous)
            return
        print(f"[ShotAssetLoader] {full_name}.identifier: '{old_raw}' -> '{new_raw}'")
        item.setData(w.RAW_ROLE, new_raw)
        if text != canonical:
            self._set_text(item, canonical)
        self._refresh_warnings()

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def _submit(self, states, compos, source, retry):
        if not self.session.follows(script_path()):  # the auto-refresh (reopening the dialog) is paused
            QtWidgets.QMessageBox.warning(
                self, "Script changed",
                "The open script belongs to another shot than this dialog.\n"
                "Resume the auto-refresh or reopen the Shot Loader.")
            return
        self._flow.submit(states, compos, source, retry)

    def _current_states(self, writes=None):
        """Fresh states (the table may be up to one refresh old), renderable only."""
        states = engine.sync()
        if writes is not None:
            wanted = {id(n) for n in writes}
            states = [s for s in states if id(s.write) in wanted]
        for state in states:
            if state.status in _NOT_RENDERABLE:
                print(f"[precomp] {state.name}: {state.label} — skipped ({state.reason})")
        return [s for s in states if s.status not in _NOT_RENDERABLE]

    @staticmethod
    def _keep_in_stream(states, compo, action, keep_without_compo=False):
        kept = {id(n) for n in render_ops.in_stream([s.write for s in states], compo, action, keep_without_compo)}
        return [s for s in states if id(s.write) in kept]

    def _upgrade_before_render(self, roots, source) -> bool:
        return self._flow.upgrade_before_render(roots, source)

    def _render_all(self):
        compo = render_ops.find_compo_write()
        if not self._upgrade_before_render([compo], "Render Compo and Precomps"):
            return
        todo = [s for s in self._current_states() if s.needs_render]
        todo = self._keep_in_stream(todo, compo, "Render Compo and Precomps")
        if not (todo or compo):
            print("[ShotAssetLoader] Nothing to render (no Live precomps and no Compo write) "
                  "— aborting Deadline submit")
            return
        self._submit(todo, [compo], "Render Compo and Precomps", self._render_all)

    def _render_compo(self):
        compo = render_ops.find_compo_write()
        if compo is None:
            print("[ShotAssetLoader] No Compo write found — aborting Deadline submit")
            return
        if not self._upgrade_before_render([compo], "Render Compo"):
            return
        self._submit([], [compo], "Render Compo", self._render_compo)

    def _render_precomps(self):
        compo = render_ops.find_compo_write()
        if not self._upgrade_before_render([compo], "Render Precomps"):
            return
        todo = [s for s in self._current_states() if s.needs_render]
        todo = self._keep_in_stream(todo, compo, "Render Precomps")
        if not todo:
            print("[ShotAssetLoader] No Live precomps to render — aborting Deadline submit")
            return
        self._submit(todo, [], "Render Precomps", self._render_precomps)

    def _render_selected(self):
        """Selected rows are rendered even when cached (explicit request);
        out-of-stream precomps are dropped."""
        selected, compos = self._selected_nodes(self.precomp_table), self._selected_nodes(self.compo_table)
        if not self._upgrade_before_render(selected + compos, "Render Selected"):
            return
        states = self._current_states(selected)
        if states:
            states = self._keep_in_stream(states, render_ops.find_compo_write(), "Render Selected")
        if not (states or compos):
            print("[ShotAssetLoader] No Write selected in the Render Manager — aborting Deadline submit")
            return
        self._submit(states, compos, "Render Selected", self._render_selected)

    def _render_selected_and_compo(self):
        """Selected precomps + the Compo Write (the compo table has no selection)."""
        compo = render_ops.find_compo_write()
        selected = self._selected_nodes(self.precomp_table)
        if not self._upgrade_before_render(selected + [compo], "Render Selected and Compo"):
            return
        states = self._current_states(selected)
        if states:
            states = self._keep_in_stream(states, compo, "Render Selected and Compo", keep_without_compo=True)
        if not states and compo is None:
            print("[ShotAssetLoader] Nothing to render (no precomp selected and no Compo write) "
                  "— aborting Deadline submit")
            return
        self._submit(states, [compo], "Render Selected and Compo", self._render_selected_and_compo)

    # ---- out of stream ----------------------------------------------------

    def _render_all_out_of_stream(self):
        out = [n for n in (nuke.toNode(name) for name in sorted(self._out_of_stream)) if n is not None]
        if not self._upgrade_before_render(out, "Render All Out of Stream"):
            return
        todo = [s for s in self._current_states() if s.needs_render]
        todo = self._only_out_of_stream(todo, "Render All Out of Stream")
        if not todo:
            QtWidgets.QMessageBox.information(
                self, "Render All Out of Stream",
                "No out-of-stream precomp needs rendering: they are all cached.\n"
                "Select rows and use 'Render Selected Out of Stream' to render them again.")
            return
        self._submit_out_of_stream(todo, "Render All Out of Stream", self._render_all_out_of_stream)

    def _render_selected_out_of_stream(self):
        """Selected out-of-stream rows, rendered even when cached."""
        selected = self._selected_nodes(self.precomp_table)
        if not self._upgrade_before_render(selected, "Render Selected Out of Stream"):
            return
        states = self._current_states(selected)
        states = self._only_out_of_stream(states, "Render Selected Out of Stream")
        if not states:
            QtWidgets.QMessageBox.information(
                self, "Render Selected Out of Stream", "Select out-of-stream precomps first.")
            return
        self._submit_out_of_stream(states, "Render Selected Out of Stream", self._render_selected_out_of_stream)

    @staticmethod
    def _only_out_of_stream(states, action):
        out = {id(n) for n in render_ops.out_of_stream([s.write for s in states], render_ops.find_compo_write())}
        for state in states:
            if id(state.write) not in out:
                print(f"[ShotAssetLoader]   {state.name}: feeds the Compo Write (skipped from {action})")
        return [s for s in states if id(s.write) in out]

    def _submit_out_of_stream(self, states, source, retry):
        """Submitted without the compo; render_ops orders them among
        themselves. The identifier check of the table ignores out-of-stream
        rows, so a clash with any other precomp (same render folder) is
        refused here."""
        identifiers = [(knob_value(n, "identifier", "") or "").strip() for n in precomp_nodes.iter_precomp_writes()]
        clashing = [s for s in states
                    if identifiers.count((knob_value(s.write, "identifier", "") or "").strip()) > 1]
        if clashing:
            QtWidgets.QMessageBox.warning(
                self, "Duplicate identifier",
                "Another precomp uses the same identifier (same render folder), rename first:\n  "
                + "\n  ".join(s.name for s in clashing))
            states = [s for s in states if s not in clashing]
            if not states:
                return
        self._submit(states, [], source, retry)

    # ---- force live ------------------------------------------------------

    def _force_button(self, node, state):
        """Toggle of the Force Live column: pressed while the force is
        pending (its version not rendered nor submitted yet)."""
        btn = w.button("Force Live", object_name="forceLiveButton")
        btn.setCheckable(True)
        btn.setFixedSize(96, 22)
        forced = state is not None and state.forced
        forceable = state is not None and engine.can_force(state)
        btn.setChecked(forced)
        btn.setEnabled(forced or forceable)
        if forced:
            btn.setToolTip(_FORCE_ON_TIP)
        elif forceable:
            btn.setToolTip(_FORCE_TIP)
        else:
            btn.setToolTip("Already live: no render to ignore." if state is not None and state.status == Status.LIVE
                           else "Not renderable (see the status).")
        btn.clicked.connect(lambda _=False, name=node.fullName(): self._toggle_force(name))
        return btn

    def _toggle_force(self, full_name):
        """Acts on the node's current state, not on the (possibly stale)
        button — and on the whole selection when the clicked row is part of
        it (the clicked row gives the direction)."""
        write = nuke.toNode(full_name)
        if write is None:
            self.request_refresh()
            return
        selected = self._selected_nodes(self.precomp_table)
        if len(selected) > 1 and full_name in {node.fullName() for node in selected}:
            writes = selected
        else:
            writes = [write]
        self._set_force(writes, not engine.is_force_pending(write))

    def _set_force(self, writes, on):
        if on:
            engine.force_live(writes)
        else:
            engine.cancel_force_live(writes)
        # Deferred: the refresh rebuilds the rows, including a clicked button.
        QtCore.QTimer.singleShot(0, self.request_refresh)

    def _upgrade(self):
        for line in precomp_nodes.upgrade_scene():
            print(f"[precomp] upgraded {line}")
        self.request_refresh()

    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------

    def _show_context_menu(self, position):
        table = self.precomp_table
        row = table.rowAt(position.y())
        if row < 0:
            return
        w.ensure_row_selected(table, row)
        menu = self._context_menu(self._selected_nodes(table))
        if menu is not None:
            menu.exec_(table.viewport().mapToGlobal(position))

    def _context_menu(self, selected):
        """Menu for the selected precomp nodes, None without selection. Render
        actions follow the rows: in-stream ones render with the compo flow,
        out-of-stream ones on their own."""
        if not selected:
            return None
        menu = QtWidgets.QMenu(self)
        menu.addAction("Open in Explorer" if len(selected) <= 1 else "Open Selected in Explorer").triggered.connect(
            lambda _=False, nodes=list(selected): w.open_in_explorer(self, [(n.name(), _output_folder(n)) for n in nodes]))
        caches = [(n.name(), s.cache.folder) for n in selected
                  for s in [self._states.get(n.fullName())] if s is not None and s.cache is not None]
        if caches:
            menu.addAction("Open Cache Folder").triggered.connect(
                lambda _=False, entries=caches: w.open_in_explorer(self, entries))

        menu.addSeparator()
        streamed = [n for n in selected if n.fullName() not in self._out_of_stream]
        out = [n for n in selected if n.fullName() in self._out_of_stream]
        if streamed:
            menu.addAction("Render Selected" if len(streamed) > 1 else "Render This Precomp").triggered.connect(
                self._render_selected)
            menu.addAction("Render Selected and Compo").triggered.connect(self._render_selected_and_compo)
        if out:
            menu.addAction("Render Selected Out of Stream" if len(out) > 1 else "Render Out of Stream")\
                .triggered.connect(self._render_selected_out_of_stream)

        menu.addSeparator()
        states = [s for s in (self._states.get(n.fullName()) for n in selected) if s is not None]
        forced = [s.write for s in states if s.forced]
        forceable = [s.write for s in states if not s.forced and engine.can_force(s)]
        if forced and not forceable:
            menu.addAction("Cancel Force Live").triggered.connect(
                lambda _=False, writes=forced: self._set_force(writes, False))
        else:
            action = menu.addAction("Force Live")
            action.setEnabled(bool(forceable))
            action.triggered.connect(lambda _=False, writes=forceable: self._set_force(writes, True))
        return menu


# ---------------------------------------------------------------------------
# Cell builders
# ---------------------------------------------------------------------------

def _toward_grey(hex_color, amount=0.55):
    """Status colour of an out-of-stream row: still recognisable, clearly muted."""
    color, grey = QtGui.QColor(hex_color), QtGui.QColor(_OUT_OF_STREAM_COLOR)
    mix = lambda a, b: round(a * (1 - amount) + b * amount)  # noqa: E731
    return QtGui.QColor(mix(color.red(), grey.red()), mix(color.green(), grey.green()),
                        mix(color.blue(), grey.blue())).name()


def _ypos(node):
    try:
        return int(node.ypos())
    except Exception:
        return 0


def _name_cell(node, editable=False):
    """Bold node name; NODE_ROLE resolves the row back to its node at
    submit time, RAW_ROLE allows rolling back a refused rename."""
    item = QtWidgets.QTableWidgetItem(node.name())
    if not editable:
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
    item.setData(w.NODE_ROLE, node.fullName())
    item.setData(w.RAW_ROLE, node.name())
    font = item.font()
    font.setBold(True)
    item.setFont(font)
    return item


def _identifier_cell(node, prefix="", editable=False):
    raw = knob_value(node, 'identifier', "") or ""
    item = QtWidgets.QTableWidgetItem(f"{prefix}{raw}" if raw else "")
    if not editable:
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
    item.setData(w.NODE_ROLE, node.fullName())
    item.setData(w.PREFIX_ROLE, prefix)
    item.setData(w.RAW_ROLE, raw)
    return item


def _version_cell(node):
    """vNNN from the gizmo's integer `versions` knob, else parsed from the
    output path (`fileName` on the Compo Write, `file` on a plain Write)."""
    text = ""
    raw = knob_value(node, 'versions')
    if raw is not None:
        try:
            text = f"v{int(raw):03d}"
        except (TypeError, ValueError):
            text = str(raw)
    if not text:
        for knob_name in ("fileName", "file"):
            parsed = extract_version_from_path(knob_value(node, knob_name, "") or "")
            if parsed:
                text = parsed
                break
    return w.read_only_item(text)


def _render_order_cell(node):
    value = knob_value(node, 'render_order')
    try:
        text = str(int(value)) if value is not None else ""
    except (TypeError, ValueError):
        text = ""
    return w.read_only_item(text)


def _output_folder(node):
    for knob_name in ("renderpath", "fileName", "file"):
        value = knob_value(node, knob_name, "") or ""
        if value and os.path.dirname(value):
            return os.path.dirname(value)
    return None
