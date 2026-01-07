from qtpy import QtWidgets, QtCore, QtGui
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union
from datetime import datetime
import json

STATUS_COLORS: Dict[str, str] = {
    "up-to-date": "#28A745",
    "outdated": "#F39C12",
    "missing": "#E74C3C",
}

DEFAULT_BTN_STYLE = """
    QPushButton {{
        background-color: {bg};
        color: #ffffff;
        padding: 8px 12px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 10pt;
        border: none;
    }}
    QPushButton:hover {{
        background-color: {hover};
    }}
"""

FILTER_BTN_STYLE = """
    QPushButton {{
        background-color: transparent;
        color: {color};
        border: 1px solid {color};
        border-radius: 10px;
        padding: 6px 10px;
        font-weight: 600;
    }}
    QPushButton:checked {{
        background-color: {color};
        color: #ffffff;
    }}
"""

LAYER_FILTER_COLOR = "#3a7bd5"
LAYER_BADGE_STYLE = FILTER_BTN_STYLE.format(color=LAYER_FILTER_COLOR)

CORE = None


class FlowLayout(QtWidgets.QLayout):
    """A simple flow layout that wraps widgets onto multiple rows (no horizontal scrollbar)."""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self._items = []
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._doLayout(QtCore.QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _doLayout(self, rect, testOnly):
        spacing = self.spacing()
        lines = []
        line = []
        line_width = 0
        line_height = 0
        max_width = rect.width()

        # collect items into wrapped lines (measure pass)
        for item in self._items:
            sz = item.sizeHint()
            w = sz.width()
            h = sz.height()

            if line and (line_width + spacing + w > max_width):
                lines.append((line, line_width, line_height))
                line = []
                line_width = 0
                line_height = 0

            if line:
                line_width += spacing + w
            else:
                line_width += w

            line.append((item, w, h))
            line_height = max(line_height, h)

        if line:
            lines.append((line, line_width, line_height))

        # layout pass: center each line horizontally
        x0 = rect.x()
        y = rect.y()
        for line_items, total_w, lh in lines:
            start_x = x0 + max(0, (max_width - total_w) // 2)
            x = start_x
            for item, w, h in line_items:
                if not testOnly:
                    item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
                x += w + spacing
            y += lh + spacing

        if not lines:
            return 0
        return y - spacing - rect.y()


def shorten_layer_name(name: str) -> str:
    """Return the middle token of an underscore-separated layer name.
    Example: '_layer_cfx_master' -> 'cfx' (middle token).
    Falls back to the original name when there are <=2 tokens.
    """
    parts = name.split("_")
    if len(parts) <= 2:
        return name
    return parts[len(parts) // 2]


def darken_color(hex_color: str, factor: float = 0.85) -> str:
    """Return a slightly darker hex color (factor between 0 and 1)."""
    c = hex_color.lstrip("#")
    if len(c) != 6:
        return hex_color
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def get_source_scene_from_usd_path(usd_path: str) -> str:
    # 1. Trouver le dossier contenant le .usda/.usd
    usd_file = Path(usd_path)
    parent_dir = usd_file.parent.parent.parent # remonter de 3 niveaux

    # 2. Construire le chemin vers versioninfo.json
    versioninfo_path = parent_dir / "versioninfo.json"

    # 3. Lire le JSON et retourner la valeur de "sourceScene"
    if not versioninfo_path.exists():
        raise FileNotFoundError(f"{versioninfo_path} not found")
    with open(versioninfo_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sourceScene", None)


def go_to_source_scene(layer_name: str, path: Optional[str]) -> None:
    try:
        source_scene = get_source_scene_from_usd_path(path)
    except FileNotFoundError as e:
        QtWidgets.QMessageBox.warning(
            QtWidgets.QApplication.activeWindow(),
            "Source scene not found",
            f"Could not find the versioninfo.json file for this layer.\n\n{e}"
        )
        return
    if not source_scene:
        QtWidgets.QMessageBox.information(
            QtWidgets.QApplication.activeWindow(),
            "No source scene",
            "No source scene is specified in versioninfo.json."
        )
        return
    CORE.pb.mediaBrowser.goToSource(source_scene)
    CORE.pb.show()
    CORE.pb.activateWindow()
    CORE.pb.raise_()
    CORE.pb.checkVisibleTabs()
    if CORE.pb.isMinimized():
        CORE.pb.showNormal()


def fmt_time(ts: float) -> str:
    """Format epoch timestamp to human-friendly string matching core.py."""
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


def _show_dependencies_popup(parent, layer_name: str, dependencies: Iterable[Tuple[str, str]]):
    """Popup listing dependency names and their statuses."""
    dlg = QtWidgets.QDialog(parent)
    dlg.setWindowTitle(f"Dépendances — {shorten_layer_name(layer_name)}")
    dlg.setModal(True)
    dlg.setMinimumWidth(360)
    layout = QtWidgets.QVBoxLayout(dlg)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    header = QtWidgets.QLabel(f"<b>{layer_name}</b>")
    header.setStyleSheet("color: #ffffff;")
    layout.addWidget(header)

    if not dependencies:
        empty = QtWidgets.QLabel("Aucune dépendance répertoriée.")
        empty.setStyleSheet("color: #cccccc;")
        layout.addWidget(empty)
    else:
        for dep in dependencies:
            # dep may be tuple (name, status) or dict-like
            if isinstance(dep, (list, tuple)):
                dep_name, dep_status = dep[0], dep[1]
                dep_mtime = dep[2] if len(dep) > 2 else None
            elif isinstance(dep, dict):
                dep_name = dep.get("name") or dep.get("layer") or str(dep)
                dep_status = dep.get("status")
                dep_mtime = dep.get("mtime_str") or dep.get("mtime")
            else:
                dep_name = str(dep)
                dep_status = ""
                dep_mtime = None
            row = QtWidgets.QWidget()
            hl = QtWidgets.QHBoxLayout(row)
            hl.setContentsMargins(0, 4, 0, 4)
            hl.setSpacing(8)

            dot = QtWidgets.QLabel()
            dot.setFixedSize(12, 12)
            status_color = STATUS_COLORS.get(dep_status, "#7F8C8D")
            dot.setStyleSheet(f"background-color: {status_color}; border-radius: 6px;")
            hl.addWidget(dot)

            name_lbl = QtWidgets.QLabel(dep_name)
            name_lbl.setStyleSheet("color: #ffffff;")
            hl.addWidget(name_lbl)

            spacer = QtWidgets.QWidget()
            spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            hl.addWidget(spacer)

            # show status and optional mtime
            status_text = dep_status or ""
            if dep_mtime:
                status_text = f"{status_text} — {dep_mtime}"
            status_lbl = QtWidgets.QLabel(status_text)
            status_lbl.setStyleSheet("color: #cccccc;")
            hl.addWidget(status_lbl)

            layout.addWidget(row)

    btn_close = QtWidgets.QPushButton("Fermer")
    btn_close.clicked.connect(dlg.accept)
    btn_close.setStyleSheet("""
        QPushButton {
            padding: 6px 12px;
            border-radius: 8px;
            background-color: transparent;
            color: #ffffff;
            border: 1px solid #6c6c6c;
        }
        QPushButton:hover {
            background-color: #2d2d30;
        }
    """)
    layout.addWidget(btn_close, alignment=QtCore.Qt.AlignRight)

    dlg.exec_()


def make_layer_row(layer_name: str, status: Optional[str] = None, path: Optional[str] = None,
                   dependencies: Optional[List[Tuple[str, str]]] = None) -> QtWidgets.QWidget:
    """Create a single-row widget showing the layer as a badge-like clickable button."""
    row = QtWidgets.QWidget()
    v = QtWidgets.QVBoxLayout(row)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)

    content = QtWidgets.QWidget()
    h = QtWidgets.QHBoxLayout(content)
    h.setContentsMargins(12, 8, 12, 8)
    h.setSpacing(0)

    display_name = shorten_layer_name(layer_name)
    color = STATUS_COLORS.get(status, "#7F8C8D")
    hover_color = darken_color(color, 0.8)

    btn = QtWidgets.QPushButton(display_name)
    btn.setCursor(QtCore.Qt.PointingHandCursor)
    btn.setStyleSheet(DEFAULT_BTN_STYLE.format(bg=color, hover=hover_color))
    btn.setMinimumHeight(30)
    btn.setMinimumWidth(120)
    btn.setMaximumWidth(300)

    # tooltip shows the full layer name (and optional path validity)
    tooltip = layer_name
    if path:
        is_valid = os.path.exists(path)
        tooltip = layer_name if is_valid else f"Not found: {path}"
    btn.setToolTip(tooltip)

    def _on_clicked():
        parent = QtWidgets.QApplication.activeWindow()
        _show_dependencies_popup(parent, layer_name, dependencies or [])

    btn.clicked.connect(_on_clicked)

    # Context menu: right-click on a layer to show actions (Go to source scene)
    def _on_go_to_source_scene():
        go_to_source_scene(layer_name, path)

    def _on_context_menu(pos: QtCore.QPoint):
        menu = QtWidgets.QMenu()
        act = QtWidgets.QAction("Go to source scene", menu)
        act.triggered.connect(_on_go_to_source_scene)
        menu.addAction(act)
        # show the menu at the global position
        menu.exec_(btn.mapToGlobal(pos))

    # enable custom context menu and connect the handler
    btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    btn.customContextMenuRequested.connect(_on_context_menu)

    h.addStretch()
    h.addWidget(btn)
    h.addStretch()

    v.addWidget(content)

    return row


def apply_dark_theme(app: QtWidgets.QApplication):
    app.setStyle("Fusion")

    dark_palette = QtGui.QPalette()
    dark_color = QtGui.QColor(45, 45, 48)
    text_color = QtGui.QColor(220, 220, 220)
    highlight_color = QtGui.QColor(42, 130, 218)

    dark_palette.setColor(QtGui.QPalette.Window, dark_color)
    dark_palette.setColor(QtGui.QPalette.WindowText, text_color)
    dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))
    dark_palette.setColor(QtGui.QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QtGui.QPalette.ToolTipBase, text_color)
    dark_palette.setColor(QtGui.QPalette.ToolTipText, text_color)
    dark_palette.setColor(QtGui.QPalette.Text, text_color)
    dark_palette.setColor(QtGui.QPalette.Button, dark_color)
    dark_palette.setColor(QtGui.QPalette.ButtonText, text_color)
    dark_palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(255, 0, 0))
    dark_palette.setColor(QtGui.QPalette.Highlight, highlight_color)
    dark_palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 255, 255))

    app.setPalette(dark_palette)
    app.setStyleSheet("""
        QToolTip { color: #ffffff; background-color: #2d2d30; border: 1px solid #6c6c6c; }
        QHeaderView::section { background-color: #3c3c3f; color: #dddddd; }
        QTableWidget { gridline-color: #4b4b4b; }
        QTreeWidget { background-color: #2d2d30; color: #dddddd; }
    """)


def get_layer_info(info) -> Tuple[Set[str], Optional[str], List[Tuple[str, str]]]:
    """Normalize different shapes of layer info into (statuses, path, deps)."""
    statuses: Set[str] = set()
    path: Optional[str] = None
    deps: List[Tuple[str, str]] = []

    if isinstance(info, dict):
        path = info.get("path")
        if "prereq_statuses" in info and info["prereq_statuses"]:
            for p in info["prereq_statuses"]:
                st = p.get("status") or "missing"
                dn = (
                    p.get("name")
                    or p.get("layer")
                    or p.get("dependency")
                    or p.get("dep")
                    or p.get("id")
                    or p.get("path")
                    or str(p)
                )
                mtime_str = p.get("mtime_str") or (fmt_time(p.get("mtime")) if p.get("mtime") else None)
                deps.append((dn, st, mtime_str))
                if st:
                    statuses.add(st)
        elif "prereqs" in info and info["prereqs"]:
            for p in info["prereqs"]:
                if isinstance(p, dict):
                    st = p.get("status") or "missing"
                    dn = p.get("name") or p.get("layer") or str(p)
                    mtime_str = p.get("mtime_str") or (fmt_time(p.get("mtime")) if p.get("mtime") else None)
                    deps.append((dn, st, mtime_str))
                    if st:
                        statuses.add(st)
        elif "status" in info and info["status"]:
            statuses.add(info["status"])
    elif isinstance(info, (list, set)):
        for it in info:
            if isinstance(it, dict):
                st = it.get("status") or "missing"
                dn = it.get("name") or it.get("layer") or str(it)
                mtime_str = it.get("mtime_str") or (fmt_time(it.get("mtime")) if it.get("mtime") else None)
                deps.append((dn, st, mtime_str))
                if st:
                    statuses.add(st)
            elif isinstance(it, str):
                statuses.add(it)
    elif isinstance(info, str):
        statuses.add(info)

    return statuses, path, deps


def open_tree_ui(tree: Dict[str, Dict[str, Dict]], title: str, core):
    global CORE
    CORE = core
    _owns_app = QtWidgets.QApplication.instance() is None
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    icon_path = Path(__file__).resolve().parents[1] / "app_icon.png"
    if icon_path.exists():
        QtWidgets.QApplication.setWindowIcon(QtGui.QIcon(str(icon_path)))

    apply_dark_theme(app)

    w = QtWidgets.QWidget()
    w.setWindowTitle(title)
    layout = QtWidgets.QHBoxLayout(w)
    left_panel = QtWidgets.QWidget()
    left_panel.setFixedWidth(280)
    left_layout = QtWidgets.QVBoxLayout(left_panel)
    left_layout.setContentsMargins(6, 6, 6, 6)
    left_layout.setSpacing(8)
    left_layout.setAlignment(QtCore.Qt.AlignTop)

    filter_box = QtWidgets.QGroupBox("Filter by statuses")
    filter_layout = QtWidgets.QHBoxLayout(filter_box)
    filter_layout.setAlignment(QtCore.Qt.AlignHCenter)
    filter_box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def make_filter_btn(text: str, color: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setStyleSheet(FILTER_BTN_STYLE.format(color=color))
        return btn

    cb_up = make_filter_btn("up-to-date", STATUS_COLORS.get("up-to-date"))
    cb_out = make_filter_btn("outdated", STATUS_COLORS.get("outdated"))
    cb_miss = make_filter_btn("missing", STATUS_COLORS.get("missing"))
    filter_layout.addWidget(cb_up)
    filter_layout.addWidget(cb_out)
    filter_layout.addWidget(cb_miss)
    left_layout.addWidget(filter_box)

    def make_layer_filter_btn(text: str) -> QtWidgets.QPushButton:
        btn = QtWidgets.QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(False)
        btn.setStyleSheet(LAYER_BADGE_STYLE)
        return btn

    layer_buttons: Dict[str, QtWidgets.QPushButton] = {}
    unique_short_map: Dict[str, Set[str]] = {}
    for seq_name, shots in tree.items():
        for shot_name, layers in shots.items():
            for layer_name in layers.keys():
                short = shorten_layer_name(layer_name)
                unique_short_map.setdefault(short, set()).add(layer_name)

    layer_box_group = QtWidgets.QGroupBox("Filter renders")
    layer_box_layout = QtWidgets.QHBoxLayout(layer_box_group)
    layer_box_layout.setContentsMargins(6, 6, 6, 6)
    layer_box_layout.setSpacing(6)
    layer_box_group.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    # Use a FlowLayout so buttons wrap onto multiple rows and no horizontal scrollbar is needed.
    layer_inner = QtWidgets.QWidget()
    flow = FlowLayout(layer_inner, spacing=6)
    layer_inner.setLayout(flow)

    for short in sorted(unique_short_map.keys()):
        b = make_layer_filter_btn(short)
        layer_buttons[short.lower()] = b
        b.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        flow.addWidget(b)

    layer_box_layout.addWidget(layer_inner)
    left_layout.addWidget(layer_box_group)

    # create search and tree widgets but place them in a middle panel between filters and renders
    search_box = QtWidgets.QLineEdit()
    search_box.setPlaceholderText("Filter shots (type to search)...")
    search_box.setStyleSheet("color: #ffffff;")
    search_box.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    tree_widget = QtWidgets.QTreeWidget()
    tree_widget.setHeaderHidden(True)
    tree_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    # add left panel first (filters)
    layout.addWidget(left_panel, 1)

    # middle panel holds search and the shots tree (positioned between filters and renders)
    middle_panel = QtWidgets.QWidget()
    middle_panel.setFixedWidth(360)
    middle_layout = QtWidgets.QVBoxLayout(middle_panel)
    middle_layout.setContentsMargins(6, 6, 6, 6)
    middle_layout.setSpacing(6)
    middle_layout.addWidget(search_box)
    middle_layout.addWidget(tree_widget, 1)
    layout.addWidget(middle_panel, 1)

    right_panel = QtWidgets.QWidget()
    right_layout = QtWidgets.QVBoxLayout(right_panel)
    right_layout.setContentsMargins(6, 6, 6, 6)
    right_layout.setSpacing(6)

    header_label = QtWidgets.QLabel("")
    header_label.setStyleSheet("color: #ffffff; font-weight: 800; font-size: 16pt;")
    header_label.setMinimumHeight(36)
    right_layout.addWidget(header_label)

    layers_scroll = QtWidgets.QScrollArea()
    layers_scroll.setWidgetResizable(True)
    layers_container = QtWidgets.QWidget()
    layers_layout = QtWidgets.QVBoxLayout(layers_container)
    layers_layout.setContentsMargins(6, 6, 6, 6)
    layers_layout.setSpacing(6)
    # Assure que les widgets s'empilent à partir du haut (pas de centrage vertical)
    layers_layout.setAlignment(QtCore.Qt.AlignTop)
    # Evite que le container prenne toute la hauteur disponible (préserve l'empilement en haut)
    layers_container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    layers_scroll.setWidget(layers_container)
    right_layout.addWidget(layers_scroll, 1)

    layout.addWidget(right_panel, 2)


    def get_priority_status(statuses: set) -> str:
        # Priority: outdated > missing > up-to-date
        if "outdated" in statuses:
            return "outdated"
        if "missing" in statuses:
            return "missing"
        if "up-to-date" in statuses:
            return "up-to-date"
        # fallback: pick any
        return next(iter(statuses), "missing")

    def rebuild_tree():
        sel: Set[str] = set()
        if cb_up.isChecked():
            sel.add("up-to-date")
        if cb_out.isChecked():
            sel.add("outdated")
        if cb_miss.isChecked():
            sel.add("missing")
        

        # If no status filters are checked, treat as all selected
        if not sel:
            sel = set(STATUS_COLORS.keys())
        
        selected_layers = {k for k, btn in layer_buttons.items() if btn.isChecked()}
        query = search_box.text().strip().lower()
        tree_widget.clear()
        # Clear selection and right-hand content when filters/search change
        tree_widget.setCurrentItem(None)
        try:
            header_label.setText("")
        except Exception:
            pass
        for i in reversed(range(layers_layout.count())):
            w_item = layers_layout.itemAt(i)
            if w_item is not None:
                widget = w_item.widget()
                if widget is not None:
                    widget.setParent(None)

        for seq_name, shots in sorted(tree.items()):
            seq_item = None
            for shot_name, layers in sorted(shots.items()):
                if query and query not in shot_name.lower():
                    continue

                shot_matches = False
                shot_statuses = set()
                for item_name, info in layers.items():
                    short = shorten_layer_name(item_name).lower()
                    if selected_layers and short not in selected_layers:
                        continue

                    statuses, _, _ = get_layer_info(info)
                    if statuses & sel:
                        shot_matches = True
                    shot_statuses.update(statuses)

                if shot_matches:
                    if seq_item is None:
                        seq_item = QtWidgets.QTreeWidgetItem([seq_name])
                        seq_item.setFlags(seq_item.flags() & ~QtCore.Qt.ItemIsSelectable)
                        tree_widget.addTopLevelItem(seq_item)
                    shot_item = QtWidgets.QTreeWidgetItem([shot_name])
                    # Determine the most important status for this shot
                    priority_status = get_priority_status(shot_statuses)
                    color = STATUS_COLORS.get(priority_status, "#7F8C8D")
                    # Set text color for the shot item
                    brush = QtGui.QBrush(QtGui.QColor(color))
                    shot_item.setForeground(0, brush)
                    seq_item.addChild(shot_item)

        tree_widget.expandAll()

    rebuild_tree()

    cb_up.toggled.connect(lambda _: rebuild_tree())
    cb_out.toggled.connect(lambda _: rebuild_tree())
    cb_miss.toggled.connect(lambda _: rebuild_tree())
    search_box.textChanged.connect(lambda _: rebuild_tree())
    for b in layer_buttons.values():
        b.toggled.connect(lambda _: rebuild_tree())

    def on_item_selected():
        item = tree_widget.currentItem()
        if item is None:
            return
        parent = item.parent()

        # clear previous widgets
        for i in reversed(range(layers_layout.count())):
            w_item = layers_layout.itemAt(i)
            if w_item is not None:
                widget = w_item.widget()
                if widget is not None:
                    widget.setParent(None)

        if parent is None:
            seq_name = item.text(0)
            header_label.setText(f"{seq_name}")
            return
        else:
            seq_name = parent.text(0)
            shot_name = item.text(0)
            header_label.setText(f"{seq_name} / {shot_name}")
            shot_layers = tree.get(seq_name, {}).get(shot_name, {})

            priority = ["outdated", "missing", "up-to-date"]
            current_selected_layers = {k for k, btn in layer_buttons.items() if btn.isChecked()}

            for layer, info in sorted(shot_layers.items()):
                short = shorten_layer_name(layer).lower()
                if current_selected_layers and short not in current_selected_layers:
                    continue

                statuses, path, deps = get_layer_info(info)
                chosen = next((p for p in priority if p in statuses), "missing")
                row = make_layer_row(layer, status=chosen, path=path, dependencies=deps)
                layers_layout.addWidget(row)

    tree_widget.currentItemChanged.connect(lambda cur, prev: on_item_selected())

    # Do not auto-select any item on startup; leave selection empty until user clicks.

    w.resize(900, 600)
    w.show()

    if _owns_app:
        app.exec_()
    else:
        loop = QtCore.QEventLoop()
        w.destroyed.connect(loop.quit)
        loop.exec_()
