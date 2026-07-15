"""
UI Loader - Simplified Qt Window Version
Standalone Qt window for loading shot assets.
Compatible with both Nuke 15 (PySide2) and Nuke 16+ (PySide6).
"""

import nuke  # type: ignore
import os
import re
import json
import subprocess
import webbrowser
from .config import Config
from .asset_discoverer import AssetDiscoverer
from .nuke_node_builder import NukeNodeBuilder
from .version_utils import version_int, extract_version_from_path
from .reconnect_stamps import run_reconnect_on_postage_stamps
from .distribute_write_render_order import distribute_write_render_order

# Import appropriate PySide version
QtWidgets, QtCore, QtGui, PYSIDE_VERSION = Config.get_pyside_module()


# Dark, flat stylesheet applied to the whole dialog. Widget-specific tweaks
# are routed through objectName so we never sprinkle inline setStyleSheet
# calls inside the UI code.
STYLESHEET = """
QDialog {
    background-color: #1e1e1e;
    color: #e8e8e8;
}
QLabel { color: #d8d8d8; }

QFrame#projectTitle {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-left: 4px solid #5a8cff;
    border-radius: 6px;
}
QFrame#projectTitle QLabel { background: transparent; color: #f0f0f0; }

QFrame#headerBanner {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
}
QLabel#bannerText {
    background: transparent;
    color: #e8e8e8;
    font-size: 13px;
}

QGroupBox {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    margin-top: 16px;
    padding: 12px 10px 10px 10px;
    color: #e8e8e8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #9a9a9a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}

QLabel#filterLabel {
    color: #9a9a9a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding-right: 6px;
}

QPushButton {
    background-color: #2d2d30;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px 14px;
    color: #e8e8e8;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #38383b;
    border-color: #505054;
}
QPushButton:pressed { background-color: #1e1e1e; }
QPushButton:disabled { color: #5a5a5a; background-color: #232325; }

/* Filter pills — rectangular with a hint of rounding */
QPushButton#filterPill {
    border-radius: 3px;
    padding: 5px 14px;
    background-color: #2a2a2c;
    border: 1px solid #3a3a3a;
}
QPushButton#filterPill:hover {
    border-color: #5a8cff;
    color: #ffffff;
}
QPushButton#filterPill:checked {
    background-color: #2c4870;
    border-color: #5a8cff;
    color: #ffffff;
    font-weight: 600;
}

/* Action button variants */
QPushButton#primaryAction {
    background-color: #2f5a3a;
    border: 1px solid #4a7a4a;
    color: #eaf5ea;
    font-weight: 600;
    padding: 8px 18px;
}
QPushButton#primaryAction:hover {
    background-color: #3a6a45;
    border-color: #5fa860;
}

QPushButton#secondaryAction {
    background-color: #3a3a5a;
    border: 1px solid #4f4f7a;
    color: #e8e8f5;
    font-weight: 600;
    padding: 8px 18px;
}
QPushButton#secondaryAction:hover {
    background-color: #45456a;
    border-color: #6868a0;
}

QPushButton#warningAction {
    background-color: #5a4a2a;
    border: 1px solid #7a653a;
    color: #f4e8d4;
    font-weight: 600;
    padding: 8px 18px;
}
QPushButton#warningAction:hover {
    background-color: #6a5530;
    border-color: #9a7e4a;
}

QPushButton#updateAction {
    background-color: #6a4a30;
    border: 1px solid #8a623a;
    color: #f5dec0;
    font-weight: 600;
    padding: 8px 18px;
}
QPushButton#updateAction:hover {
    background-color: #7a5538;
    border-color: #a87a4a;
}

QPushButton#dangerAction {
    background-color: #6a2f2f;
    border: 1px solid #8a3a3a;
    color: #f5d6d6;
    font-weight: 600;
    padding: 8px 18px;
}
QPushButton#dangerAction:hover {
    background-color: #7a3838;
    border-color: #a64a4a;
}

/* Hide (trash) button — transparent icon-only button, one per asset row */
QPushButton#hideButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 0;
    color: #9a6a6a;
}
QPushButton#hideButton:hover {
    background-color: #3a2a2a;
    border-color: #7a3a3a;
    color: #f5d6d6;
}

/* Recover button — mirrors hideButton but with a green tint so it reads as
   a restore/undo action instead of a destructive one. Shown in place of the
   trash icon for rows that are currently in the shot's hidden list. */
QPushButton#recoverButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 0;
    color: #6a9a6a;
}
QPushButton#recoverButton:hover {
    background-color: #2a3a2a;
    border-color: #4a7a4a;
    color: #d6f5d6;
}

/* Table */
QTableWidget {
    background-color: #1f1f20;
    alternate-background-color: #25252a;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    gridline-color: #2e2e30;
    color: #e8e8e8;
    selection-background-color: #2c4870;
    selection-color: #ffffff;
}
QTableWidget::item { padding: 6px 4px; }
QTableWidget::item:selected {
    background-color: #2c4870;
    color: #ffffff;
}
QHeaderView { background-color: #252526; }
QHeaderView::section {
    background-color: #2a2a2c;
    border: none;
    border-right: 1px solid #353537;
    border-bottom: 1px solid #353537;
    padding: 9px 6px;
    color: #9a9a9a;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.3px;
}

/* Inputs */
QComboBox, QLineEdit {
    background-color: #2d2d30;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    padding: 4px 7px;
    color: #e8e8e8;
}
QComboBox:hover, QLineEdit:hover { border-color: #4a4a4d; }
QLineEdit:focus, QComboBox:focus { border-color: #5a8cff; }
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background-color: #2d2d30;
    border: 1px solid #3a3a3a;
    selection-background-color: #2c4870;
    color: #e8e8e8;
    padding: 2px;
}

/* Checkbox */
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4a4a4d;
    border-radius: 3px;
    background-color: #2d2d30;
}
QCheckBox::indicator:checked {
    background-color: #5a8cff;
    border-color: #5a8cff;
}
QCheckBox::indicator:hover { border-color: #5a8cff; }

/* Scrollbars */
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    border: none;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background-color: #3a3a3d;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background-color: #50505a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 10px;
    border: none;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background-color: #3a3a3d;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover { background-color: #50505a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QMenu {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    color: #e8e8e8;
    padding: 4px;
}
QMenu::item { padding: 6px 18px; border-radius: 3px; }
QMenu::item:selected { background-color: #2c4870; color: #ffffff; }

/* Custom tab headers — plain QPushButtons styled as tabs. We deliberately
   avoid QTabBar/QTabWidget because in this PySide2/Nuke 15 environment its
   selected-tab vertical shift clips the top of bold text and no combination
   of padding/margin overrides could defeat it. QPushButton has no such shift. */
QPushButton#tabHeader {
    background-color: #2a2a2c;
    color: #9a9a9a;
    border: 1px solid #3a3a3a;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 9px 22px;
    margin: 0;
    font-weight: bold;
    font-size: 11px;
}
QPushButton#tabHeader:hover {
    background-color: #38383b;
    color: #e8e8e8;
}
QPushButton#tabHeader:checked {
    background-color: #1e1e1e;
    color: #ffffff;
    border-color: #5a8cff;
}

/* Logs view — monospace console look */
QPlainTextEdit#logView {
    background-color: #141416;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    color: #d8d8d8;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 8px;
    selection-background-color: #2c4870;
    selection-color: #ffffff;
}
"""


class _StatusColorDelegate(QtWidgets.QStyledItemDelegate):
    """Paints the Status cell using its BackgroundRole color even when the
    row is selected. Without this the default selection highlight masks the
    status color, which is the only at-a-glance cue for loaded/outdated/etc."""

    def paint(self, painter, option, index):
        bg = index.data(QtCore.Qt.BackgroundRole)
        if isinstance(bg, QtGui.QBrush) and bg.color().alpha() > 0:
            opt = QtWidgets.QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            opt.state &= ~QtWidgets.QStyle.State_Selected
            opt.backgroundBrush = bg
            super(_StatusColorDelegate, self).paint(painter, opt, index)
            return
        super(_StatusColorDelegate, self).paint(painter, option, index)


class _ConsoleStream:
    """File-like object that tees writes to the original stream AND a
    QPlainTextEdit. Installed in place of sys.stdout/sys.stderr while the
    loader dialog is open so the Logs tab mirrors everything the tool prints,
    without breaking Nuke's own script-editor output."""

    def __init__(self, original, text_widget):
        self._original = original
        self._text_widget = text_widget

    def write(self, text):
        if self._original is not None:
            try:
                self._original.write(text)
            except Exception:
                pass
        if not text or self._text_widget is None:
            return
        # PySide raises RuntimeError when the underlying C++ widget has been
        # destroyed (dialog closed without restoring streams). Swallow it so
        # a stray print after teardown doesn't propagate.
        try:
            cursor = self._text_widget.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertText(text)
            self._text_widget.setTextCursor(cursor)
            self._text_widget.ensureCursorVisible()
        except Exception:
            self._text_widget = None

    def flush(self):
        if self._original is not None:
            try:
                self._original.flush()
            except Exception:
                pass

    def isatty(self):
        return False


class _PackageComboBox(QtWidgets.QComboBox):
    """QComboBox that displays only the bare package name (Qt::UserRole) when
    collapsed, while the popup list shows the full
    "PKG_v001    (v053 / 09/07/26)" annotation. Keeps the closed banner
    compact without hiding the traceability info on scroll."""

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))
        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        idx = self.currentIndex()
        if idx >= 0:
            short = self.itemData(idx, QtCore.Qt.UserRole)
            if short:
                opt.currentText = short
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)
        painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt)


class AssetItem:
    """Represents an asset in the table."""
    def __init__(self, asset_type, asset_name, versions, versions_dict, source_type=""):
        self.asset_type = asset_type
        self.asset_name = asset_name
        self.source_type = source_type  # "external", "2dRender", "3dRender", "Camera"
        self.versions = versions
        self.selected_version = versions[-1] if versions else None
        self.versions_dict = versions_dict  # Full version data
        self.selected_colorspace = "Auto"  # Colorspace selection (Auto = Nuke default)

        # Update tracking
        self.loaded_node = None  # Nuke node if loaded
        self.loaded_version = None  # Version currently loaded in scene
        self.has_update = False  # True if newer version available
        self.update_target_version = None  # Version that "Update to Latest" will apply
        self.status_text = "Not loaded"  # Status display text
        self.status_color = None  # Color for status display
        self.has_duplicates = False  # True if multiple loader-owned Reads match this asset

        # Foreign-shot tracking — set when the Read points at an asset whose
        # path lives under a different SQ/SH than the current context. These
        # items are discovered straight from the scene (not from the local
        # asset list) so their loaded_node is bound at construction time.
        self.is_foreign = False
        self.foreign_sequence = ""
        self.foreign_shot = ""

        # True when this row is present in the shot's hidden list. Only ever
        # set to True while the "Show Hidden Assets" checkbox is on — when the
        # checkbox is off, hidden entries are filtered out before an AssetItem
        # is even constructed. Drives the "recover vs trash" button switch.
        self.is_hidden = False


class ShotAssetLoaderWindow(QtWidgets.QDialog):
    """Standalone Qt window for shot asset loading."""

    HELP_URL = "https://www.notion.so/illogic/Nuke-Shot-Loader-3679d24ae7e3804491f7ceade8e2a1e3"

    def __init__(self, parent=None):
        super(ShotAssetLoaderWindow, self).__init__(parent)

        self.setWindowTitle("Shot Asset Loader")
        self.setMinimumSize(1200, 600)

        # Destroy the dialog on close instead of merely hiding it (Qt's
        # default). Without this, every call to show_shot_asset_loader()
        # spawns a fresh instance that stays parented to Nuke's main window
        # forever — old dialogs remain alive, quietly receiving broadcast
        # events like EnterWhatsThisMode (so clicking the title-bar "?" would
        # open one help tab per accumulated instance) and stacking their
        # _ConsoleStream wrappers on top of sys.stdout.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Build the Logs widget first and tee sys.stdout/sys.stderr through it
        # right away, so prints fired during the rest of __init__ (project
        # root detection, asset scan) show up in the Logs tab. The widget is
        # parented to a layout later in _init_ui.
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("logView")
        self.log_view.setMaximumBlockCount(5000)  # cap memory on long sessions

        import sys as _sys
        self._orig_stdout = _sys.stdout
        self._orig_stderr = _sys.stderr
        _sys.stdout = _ConsoleStream(_sys.stdout, self.log_view)
        _sys.stderr = _ConsoleStream(_sys.stderr, self.log_view)

        # Project root is auto-detected from the saved Nuke script path
        # (pipeline: <drive>:/<projectName>/...). Falls back to the config
        # default if the script isn't saved or doesn't match.
        detected_root = self._detect_project_root_from_script()
        self._project_root = detected_root or Config.DEFAULT_PROJECT_ROOT
        self._project_detected = detected_root is not None

        # Per-project prefs JSON — created empty on the first-ever open for a
        # production. Path stored on self so later features (read/write of
        # remembered settings) can reuse it.
        self._prefs_path = self._ensure_prefs_file()

        # Backend modules
        self.discoverer = AssetDiscoverer(self._project_root)
        self.node_builder = NukeNodeBuilder()

        # Data
        self.current_sequence = None
        self.current_shot = None
        self.current_assets = {}
        self.asset_items = []

        # Whether the "Show Hidden Assets" checkbox is on. Controls whether
        # _populate_table skips shot-hidden entries (default) or includes
        # them with a Recover button in place of the trash icon.
        self._show_hidden = False

        # Cache: folder_path → set(frame_numbers) — populated on first coverage
        # check, reused across silent re-checks (filter switches, etc.). We
        # cache the full frame set rather than just (first, last) so the
        # coverage test can detect gaps. Cleared on explicit "Check for Updates".
        self._frame_set_cache = {}

        # OCIO colorspace list — built once per dialog. The list itself doesn't
        # change while the dialog is open, and _add_row is called once per
        # asset, so without this cache the OCIO config gets walked (and
        # logged) dozens of times per scan.
        self._colorspaces_cache = None

        self._init_ui()
        self._detect_script_context()  # Auto-detect context from Nuke script path
        # Populate the Render Manager tables so they're ready if the user
        # switches straight to that tab without triggering a lazy refresh.
        self._refresh_render_manager()

    def event(self, e):
        # The title-bar "?" button (WindowContextHelpButtonHint, shown by
        # default on QDialog under Windows) puts the dialog into Qt's
        # "What's This?" mode. We hijack that event to open the Notion doc
        # instead, since we don't ship per-widget WhatsThis help.
        if e.type() == QtCore.QEvent.EnterWhatsThisMode:
            webbrowser.open(self.HELP_URL)
            e.accept()
            return True
        return super(ShotAssetLoaderWindow, self).event(e)

    def closeEvent(self, event):
        # Restore the original streams before the dialog (and its log widget)
        # are destroyed. Otherwise a stray print after teardown would write
        # into a deleted QPlainTextEdit.
        self._restore_streams()
        super(ShotAssetLoaderWindow, self).closeEvent(event)

    def _restore_streams(self):
        import sys as _sys
        orig_out = getattr(self, "_orig_stdout", None)
        if orig_out is not None and isinstance(_sys.stdout, _ConsoleStream):
            _sys.stdout = orig_out
        orig_err = getattr(self, "_orig_stderr", None)
        if orig_err is not None and isinstance(_sys.stderr, _ConsoleStream):
            _sys.stderr = orig_err
        self._orig_stdout = None
        self._orig_stderr = None

    def showEvent(self, event):
        super(ShotAssetLoaderWindow, self).showEvent(event)
        # Grow the dialog vertically on first show so every asset row is
        # visible without scrolling. Deferred via singleShot(0) so Qt has
        # finished its initial layout pass (otherwise the table viewport
        # height is still 0 and the delta math is wrong).
        if not getattr(self, "_height_adjusted", False):
            self._height_adjusted = True
            QtCore.QTimer.singleShot(0, self._adjust_height_to_fit_assets)

    def _adjust_height_to_fit_assets(self):
        """Resize the dialog so every visible asset row fits without
        scrolling. Capped at the screen's available height so the window
        never extends past the monitor edge."""
        if not self.asset_items:
            return

        visible_rows = sum(
            1 for row in range(self.table.rowCount())
            if not self.table.isRowHidden(row)
        )
        if visible_rows == 0:
            return

        row_h = self.table.verticalHeader().defaultSectionSize()
        header_h = self.table.horizontalHeader().height()
        frame_pad = self.table.frameWidth() * 2
        # Small extra cushion so the last row isn't flush against the border
        # and the horizontal scrollbar (if any) doesn't clip it.
        desired_table_h = header_h + visible_rows * row_h + frame_pad + 6

        current_table_h = self.table.height()
        delta = desired_table_h - current_table_h
        if delta <= 0:
            return

        screen = QtWidgets.QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            # Leave a small margin for the title bar / OS chrome.
            max_h = avail.height() - 60
        else:
            avail = None
            max_h = 1080

        new_h = min(self.height() + delta, max_h)
        if new_h <= self.height():
            return

        self.resize(self.width(), new_h)

        # If we grew downward past the screen, nudge the window up so the
        # full dialog stays visible.
        if avail is not None:
            frame = self.frameGeometry()
            if frame.bottom() > avail.bottom():
                new_y = max(avail.top(), avail.bottom() - frame.height())
                self.move(self.x(), new_y)

    def _detect_project_root_from_script(self):
        """
        Parse the current Nuke script path to extract the project root.

        Pipeline structure: <drive>:/<projectName>/...
        Returns the detected project root (e.g., "I:\\McDonald_2511") or None
        if the script isn't saved or doesn't match the expected layout.
        """
        try:
            script_path = nuke.root().name()

            if not script_path or script_path == "Root":
                print("[ShotAssetLoader] No saved script, using default project root")
                return None

            normalized = script_path.replace('\\', '/')

            # Capture <drive>:/<projectName>
            match = re.match(r'^([A-Za-z]:/[^/]+)', normalized)
            if not match:
                print(f"[ShotAssetLoader] Script path doesn't match <drive>:/<project>/... : {script_path}")
                return None

            project_root = match.group(1).replace('/', os.sep)
            print(f"[ShotAssetLoader] Detected project root from script: {project_root}")
            return project_root

        except Exception as e:
            print(f"[ShotAssetLoader] Failed to detect project root: {e}")
            return None

    def _ensure_prefs_file(self):
        """
        Ensure the per-project prefs JSON exists on disk. Called once when the
        dialog opens; on the first-ever open for a production it creates the
        folder tree and writes an empty `{}` JSON file.

        Path: <project_root>/04_Resources/Nuke/prefs/shotloader/<prod>_prefs_shotloader.json

        Returns the absolute path on success, or None if no project was
        detected or the file couldn't be created (e.g. disk not accessible).
        """
        if not self._project_detected:
            return None

        project_name = os.path.basename(self._project_root.rstrip(os.sep))
        prefs_dir = os.path.join(
            self._project_root, "04_Resources", "Nuke", "prefs", "shotloader",
        )
        prefs_path = os.path.join(prefs_dir, f"{project_name}_prefs_shotloader.json")

        if os.path.exists(prefs_path):
            print(f"[ShotAssetLoader] Prefs file found: {prefs_path}")
            return prefs_path

        try:
            os.makedirs(prefs_dir, exist_ok=True)
            with open(prefs_path, "w", encoding="utf-8") as f:
                f.write("{}\n")
            print(f"[ShotAssetLoader] Created empty prefs file: {prefs_path}")
            return prefs_path
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to create prefs file at {prefs_path}: {e}")
            return None

    def _load_prefs(self):
        """Read the per-project prefs JSON. Returns {} on missing/malformed
        file — persistence must never crash the dialog on corrupt data."""
        if not self._prefs_path or not os.path.exists(self._prefs_path):
            return {}
        try:
            with open(self._prefs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            print("[ShotAssetLoader] Prefs root is not a dict, ignoring")
            return {}
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to read prefs: {e}")
            return {}

    def _save_prefs(self, data):
        """Persist the prefs dict back to disk. No-ops if the path is unset."""
        if not self._prefs_path:
            return
        try:
            with open(self._prefs_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ShotAssetLoader] Failed to write prefs: {e}")

    def _shot_key(self):
        """Composite key used to scope prefs entries to the current shot."""
        return f"{self.current_sequence}/{self.current_shot}"

    def _is_precomp_asset(self, name):
        """True if an asset name looks like a precomp render (case-insensitive
        substring match on 'precomp'). Precomps are cached to disk by the
        Render Manager and reloaded via the Precomp gizmo, not through this
        loader — surfacing them here would only clutter the table."""
        return "precomp" in (name or "").lower()

    def _hidden_set_for_shot(self):
        """Return (asset_type, asset_name) tuples the user has marked as
        hidden for the current sequence/shot. Consumed by _populate_table
        to skip those assets during rendering."""
        if not self.current_sequence or not self.current_shot:
            return set()
        prefs = self._load_prefs()
        entries = prefs.get("hidden_assets", {}).get(self._shot_key(), [])
        result = set()
        for entry in entries:
            if isinstance(entry, dict) and "type" in entry and "name" in entry:
                result.add((entry["type"], entry["name"]))
        return result

    def _hide_asset(self, item):
        """Persist an asset as hidden for the current shot, then refresh the
        table so it disappears immediately. Called by the per-row trash button."""
        if not self._prefs_path:
            QtWidgets.QMessageBox.warning(
                self, "Cannot Hide Asset",
                "No prefs file available for this project.\n"
                "Save your script inside a detected project so the loader "
                "can persist hidden-asset choices."
            )
            return
        if not self.current_sequence or not self.current_shot:
            return

        prefs = self._load_prefs()
        hidden_map = prefs.setdefault("hidden_assets", {})
        entries = hidden_map.setdefault(self._shot_key(), [])
        key = {"type": item.asset_type, "name": item.asset_name}
        if key not in entries:
            entries.append(key)
        self._save_prefs(prefs)
        print(
            f"[ShotAssetLoader] Hidden '{item.asset_type}/{item.asset_name}' "
            f"from {self._shot_key()} — restore by editing {self._prefs_path}"
        )
        # Rebuild the table with the new filter applied, refresh the ASSETS
        # count in the banner, then re-tag loaded state on the freshly
        # created AssetItem instances (populate discards the previous
        # loaded_node references, so without this pass every remaining row
        # would flip back to "Not loaded" until the user hits refresh).
        self._populate_table()
        self._refresh_info_banner()
        self._do_check_for_updates(silent=True)

    def _recover_asset(self, item):
        """Drop an asset's entry from the shot's hidden list in prefs, so it
        starts appearing normally again. Also tidies up empty containers in
        the JSON (empty shot list → remove key; empty hidden_assets → remove
        key) so the file stays clean over time."""
        if not self._prefs_path:
            return
        if not self.current_sequence or not self.current_shot:
            return

        prefs = self._load_prefs()
        hidden_map = prefs.get("hidden_assets", {})
        shot_key = self._shot_key()
        entries = hidden_map.get(shot_key, [])
        remaining = [
            e for e in entries
            if not (
                isinstance(e, dict)
                and e.get("type") == item.asset_type
                and e.get("name") == item.asset_name
            )
        ]
        if len(remaining) == len(entries):
            return  # Nothing matched — nothing to remove

        if remaining:
            hidden_map[shot_key] = remaining
        else:
            hidden_map.pop(shot_key, None)
        if not hidden_map:
            prefs.pop("hidden_assets", None)

        self._save_prefs(prefs)
        print(
            f"[ShotAssetLoader] Recovered '{item.asset_type}/{item.asset_name}' "
            f"in {shot_key}"
        )
        # Same triple-step as _hide_asset: repopulate → refresh banner →
        # re-tag loaded state so status colors don't flip to "Not loaded".
        self._populate_table()
        self._refresh_info_banner()
        self._do_check_for_updates(silent=True)

    # --- Package snapshots -------------------------------------------------
    # A "package" is a snapshot of the selected version of every asset in the
    # table at a given moment, saved to prefs so the artist can rewind the
    # comp to any previously-loaded state. Save is triggered by successful
    # Load / Update actions; recall is via the "Choose Package" button.

    _PACKAGE_NAME_RE = re.compile(r'^PKG_v(\d+)$')

    def _extract_compo_version_from_script(self):
        """Pull the 'v###' token from the current Nuke script filename so we
        can stamp it on each saved package. Returns None when the script
        isn't saved or the filename doesn't follow the pipeline convention."""
        try:
            script_path = nuke.root().name()
            if not script_path or script_path == "Root":
                return None
            filename = os.path.basename(script_path)
            m = re.search(r'_v(\d{3,4})\.nk$', filename)
            if m:
                return f"v{m.group(1)}"
        except Exception:
            pass
        return None

    def _packages_for_shot(self):
        """Return the list of package dicts for the current shot (empty when
        no shot context or no packages saved yet)."""
        if not self.current_sequence or not self.current_shot:
            return []
        prefs = self._load_prefs()
        packages = prefs.get("packages", {}).get(self._shot_key(), [])
        return packages if isinstance(packages, list) else []

    def _current_package_for_shot(self):
        """Return the PKG_v### name pinned as 'current' for this shot, or None
        if no pin exists. Updated by _save_package_snapshot (bumped to the
        newest package after every Load/Update) and by _on_choose_package
        (set to whichever package the artist explicitly recalls). Drives the
        default selection of the package combo on refresh."""
        if not self.current_sequence or not self.current_shot:
            return None
        prefs = self._load_prefs()
        current_map = prefs.get("current_package", {})
        if not isinstance(current_map, dict):
            return None
        val = current_map.get(self._shot_key())
        return val if isinstance(val, str) else None

    def _next_package_name(self, packages):
        """Compute the next PKG_v### slot. We scan the existing names rather
        than just len()+1 so a manually edited prefs (deleted middle entry)
        doesn't produce a colliding name."""
        highest = 0
        for pkg in packages:
            m = self._PACKAGE_NAME_RE.match(pkg.get("name", ""))
            if m:
                n = int(m.group(1))
                if n > highest:
                    highest = n
        return f"PKG_v{highest + 1:03d}"

    def _snapshot_current_assets(self):
        """Freeze the currently-selected version of every row into a list of
        plain dicts, ready to serialise into prefs. Foreign-shot items carry
        their origin seq/shot so lookup on recall still works."""
        snapshot = []
        for item in self.asset_items:
            if not item.selected_version:
                continue
            entry = {
                "type": item.asset_type,
                "name": item.asset_name,
                "version": item.selected_version,
            }
            if item.is_foreign:
                entry["foreign_sequence"] = item.foreign_sequence
                entry["foreign_shot"] = item.foreign_shot
            snapshot.append(entry)
        return snapshot

    def _save_package_snapshot(self):
        """Persist the current selection as a new PKG_v### entry in prefs and
        pin the shot's `current_package` to the newest snapshot so any prior
        rollback is undone. De-dups against the previous package (same
        compo_version + same asset versions) so a Load followed by an Update
        on the same state doesn't produce two identical records back-to-back;
        the current_package pin is still refreshed either way."""
        if not self._prefs_path:
            return
        if not self.current_sequence or not self.current_shot:
            return
        if not self.asset_items:
            return

        import datetime as _dt
        date_str = _dt.date.today().strftime("%d/%m/%y")

        prefs = self._load_prefs()
        packages_map = prefs.setdefault("packages", {})
        packages = packages_map.setdefault(self._shot_key(), [])

        new_snapshot = self._snapshot_current_assets()
        if not new_snapshot:
            return
        compo_version = self._extract_compo_version_from_script() or ""

        matches_last = False
        if packages:
            last = packages[-1]
            matches_last = (
                last.get("compo_version", "") == compo_version
                and last.get("assets") == new_snapshot
            )

        if not matches_last:
            pkg_name = self._next_package_name(packages)
            packages.append({
                "name": pkg_name,
                "compo_version": compo_version,
                "date": date_str,
                "assets": new_snapshot,
            })
            print(
                f"[ShotAssetLoader] Saved snapshot {pkg_name} "
                f"({compo_version or '?'} / {date_str}) for {self._shot_key()} "
                f"— {len(new_snapshot)} asset(s)"
            )

        # Any Load/Update snaps current_package to the newest entry, so a
        # user previously rolled back is automatically re-aligned. The pin
        # is refreshed even on a dedup no-append, since the state now
        # matches the last saved snapshot by definition.
        if packages:
            current_map = prefs.setdefault("current_package", {})
            current_map[self._shot_key()] = packages[-1]["name"]

        self._save_prefs(prefs)
        self._refresh_package_dropdown()

    def _refresh_package_dropdown(self):
        """Rebuild the package combo from the packages stored for the current
        shot. Selects the newest entry by default. When there are none, shows
        a disabled placeholder so the widget stays visible."""
        combo = getattr(self, "package_combo", None)
        if combo is None:
            return
        packages = self._packages_for_shot()
        combo.blockSignals(True)
        combo.clear()
        if not packages:
            combo.addItem("(no packages yet)")
            combo.setEnabled(False)
            if hasattr(self, "choose_package_btn"):
                self.choose_package_btn.setEnabled(False)
        else:
            for pkg in packages:
                name = pkg.get("name", "?")
                compo = pkg.get("compo_version") or "?"
                date_str = pkg.get("date") or "?"
                # The full "PKG_v001  (v053 / 09/07/26)" text becomes the item's
                # display role — visible in the popup list. userData carries the
                # bare name so _PackageComboBox.paintEvent can show just that
                # when the combo is collapsed.
                combo.addItem(f"{name}    ({compo} / {date_str})", name)
            # Default to the shot's pinned current_package; fall back to newest
            # when no pin is stored (fresh shot, or older prefs file).
            current_pkg = self._current_package_for_shot()
            target_idx = combo.count() - 1
            if current_pkg:
                for i in range(combo.count()):
                    if combo.itemData(i) == current_pkg:
                        target_idx = i
                        break
            combo.setCurrentIndex(target_idx)
            combo.setEnabled(True)
            if hasattr(self, "choose_package_btn"):
                self.choose_package_btn.setEnabled(True)
        combo.blockSignals(False)

    def _on_choose_package(self):
        """Apply the versions from the package selected in the combo to the
        table dropdowns AND update any already-loaded nodes to match. Rows
        that are only listed (not loaded) simply have their dropdown adjusted
        so the next Load picks the package's version."""
        packages = self._packages_for_shot()
        if not packages:
            return
        idx = self.package_combo.currentIndex()
        if idx < 0 or idx >= len(packages):
            return
        pkg = packages[idx]
        pkg_name = pkg.get("name", "package")
        entries = pkg.get("assets", [])
        if not entries:
            QtWidgets.QMessageBox.information(
                self, "Empty Package",
                f"{pkg_name} has no assets recorded."
            )
            return

        # Lookup by (type, name). Foreign items share the same asset_name/type
        # as local ones would; the seq/shot fields are only used for display,
        # so we don't need to include them in the key.
        version_lookup = {
            (e.get("type"), e.get("name")): e.get("version")
            for e in entries if e.get("version")
        }

        adjusted_rows = []
        missing_on_disk = []
        not_in_current = []

        for row, item in enumerate(self.asset_items):
            target = version_lookup.pop((item.asset_type, item.asset_name), None)
            if not target:
                continue
            if target not in item.versions:
                missing_on_disk.append(
                    f"{item.asset_type} / {item.asset_name} ({target})"
                )
                continue
            item.selected_version = target
            combo = self.table.cellWidget(row, 2)
            if isinstance(combo, QtWidgets.QComboBox):
                combo.blockSignals(True)
                combo.setCurrentText(target)
                combo.blockSignals(False)
            adjusted_rows.append(item)

        # Anything left in version_lookup is in the package but not in the
        # current table — probably a hidden asset or an asset that no longer
        # exists on disk. Worth surfacing so the artist knows.
        for (t, n), v in version_lookup.items():
            not_in_current.append(f"{t} / {n} ({v})")

        # Items where the loaded scene node's version differs from the package
        # target — those need an actual node update. The rest just get their
        # status recomputed against the new selection.
        to_update = [
            it for it in adjusted_rows
            if it.loaded_node and it.loaded_version != it.selected_version
        ]

        applied = True
        if to_update:
            for it in to_update:
                it.update_target_version = it.selected_version
                it.has_update = True
            applied = self._perform_updates(
                to_update,
                scope_label="package",
                confirm_message=(
                    f"Apply {pkg_name} to {len(to_update)} loaded asset(s)?"
                ),
                save_snapshot=False,
            )
        else:
            # No node updates needed — just recompute Status against the new
            # dropdown selections and refresh the visible cells.
            for it in adjusted_rows:
                self._refresh_status_for_selection(it)
            self._refresh_table_status()

        if not applied:
            # User cancelled the confirm dialog inside _perform_updates.
            # Leave current_package alone and skip the warnings popup — the
            # artist explicitly backed out.
            return

        # Pin this package as the shot's current so subsequent opens and any
        # future dropdown refresh default back to it. Only the next Load or
        # Update will unpin it (back to the newest snapshot).
        prefs = self._load_prefs()
        current_map = prefs.setdefault("current_package", {})
        current_map[self._shot_key()] = pkg_name
        self._save_prefs(prefs)
        self._refresh_package_dropdown()

        # Report the mismatch cases in a single non-blocking dialog so the
        # artist can see what didn't apply cleanly.
        warnings = []
        if missing_on_disk:
            warnings.append(
                "Versions from the package no longer available on disk:\n  - "
                + "\n  - ".join(missing_on_disk[:10])
            )
        if not_in_current:
            warnings.append(
                "Assets recorded in the package but not in the current table "
                "(hidden or removed):\n  - "
                + "\n  - ".join(not_in_current[:10])
            )
        if warnings:
            QtWidgets.QMessageBox.warning(
                self, f"{pkg_name} — Partial Apply", "\n\n".join(warnings)
            )

    def _on_show_hidden_toggled(self, checked):
        """React to the 'Show Hidden Assets' checkbox: rebuild the table so
        hidden entries appear (with Recover buttons) or disappear."""
        self._show_hidden = bool(checked)
        self._populate_table()
        self._refresh_info_banner()
        self._do_check_for_updates(silent=True)

    def _get_ocio_colorspaces(self):
        """
        Get list of available colorspaces from Nuke's OCIO configuration.

        Returns:
            list: List of colorspace names, with "Auto" as first item
        """
        if self._colorspaces_cache is not None:
            return self._colorspaces_cache

        colorspaces = ["Auto"]  # Default option

        try:
            # Get Nuke root node
            root = nuke.root()

            # Check if colorManagement knob exists
            if not root.knob('colorManagement'):
                print("[ShotAssetLoader] Warning: colorManagement knob not found in root node")
                colorspaces.extend(["default", "linear", "sRGB", "Rec.709"])
                self._colorspaces_cache = colorspaces
                return colorspaces

            # Get color management mode
            color_management = root['colorManagement'].value()
            print(f"[ShotAssetLoader] Color management mode: {color_management}")

            if color_management == "OCIO":
                # Try to get OCIO colorspaces using PyOpenColorIO
                try:
                    import PyOpenColorIO as OCIO # type: ignore
                    config = OCIO.GetCurrentConfig()

                    # Support both OCIO v1 and v2 APIs
                    if hasattr(config, 'getColorSpaces'):
                        # OCIO v2 API (Nuke 16+)
                        print("[ShotAssetLoader] Using OCIO v2 API")
                        for cs in config.getColorSpaces():
                            colorspaces.append(cs.getName())
                    elif hasattr(config, 'getNumColorSpaces'):
                        # OCIO v1 API (Nuke 15 and earlier)
                        print("[ShotAssetLoader] Using OCIO v1 API")
                        for i in range(config.getNumColorSpaces()):
                            cs = config.getColorSpaceNameByIndex(i)
                            colorspaces.append(cs)
                    else:
                        raise AttributeError("Unknown OCIO API version - neither v1 nor v2 methods found")

                    print(f"[ShotAssetLoader] Successfully loaded {len(colorspaces)-1} colorspaces from OCIO config")
                    self._colorspaces_cache = colorspaces
                    return colorspaces

                except ImportError:
                    # PyOpenColorIO not available, use fallback list
                    print("[ShotAssetLoader] PyOpenColorIO module not available, using fallback OCIO colorspace list")
                    colorspaces.extend([
                        "scene_linear",
                        "ARRI LogC4",
                        "sRGB",
                        "Rec.709",
                        "linear",
                        "default"
                    ])
                except Exception as e:
                    print(f"[ShotAssetLoader] Error loading OCIO config: {e}")
                    import traceback
                    traceback.print_exc()
                    colorspaces.extend([
                        "scene_linear",
                        "ARRI LogC4",
                        "sRGB",
                        "Rec.709",
                        "linear",
                        "default"
                    ])
            else:
                # Nuke native color management, use basic list
                print(f"[ShotAssetLoader] Using Nuke native colorspaces (mode: {color_management})")
                colorspaces.extend([
                    "default",
                    "linear",
                    "sRGB",
                    "Rec.709",
                    "Cineon",
                    "Gamma1.8",
                    "Gamma2.2"
                ])

        except AttributeError as e:
            print(f"[ShotAssetLoader] Error accessing Nuke root node: {e}")
            import traceback
            traceback.print_exc()
            colorspaces.extend(["default", "linear", "sRGB", "Rec.709"])
        except Exception as e:
            print(f"[ShotAssetLoader] Unexpected error getting colorspaces: {e}")
            import traceback
            traceback.print_exc()
            colorspaces.extend(["default", "linear", "sRGB", "Rec.709"])

        self._colorspaces_cache = colorspaces
        return colorspaces

    def _make_trash_icon(self, color="#c8a0a0", size=16):
        """Draw a small trash-can icon programmatically. SP_TrashIcon renders
        inconsistently across Qt versions/platforms — on this project's Nuke
        build it came out looking like a generic emoji glyph that testers
        didn't recognise as a bin. Drawing it ourselves gives a predictable,
        readable silhouette everywhere."""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pen = QtGui.QPen(QtGui.QColor(color))
            pen.setWidthF(1.3)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            painter.setPen(pen)
            # Coordinates assume a 16x16 canvas; the visual scales cleanly at
            # the small icon sizes we use (14–16px).
            # Lid handle (small bump above the lid)
            painter.drawLine(6, 3, 10, 3)
            painter.drawLine(6, 3, 6, 5)
            painter.drawLine(10, 3, 10, 5)
            # Lid line
            painter.drawLine(3, 5, 13, 5)
            # Body — slight trapezoid so it reads as a bin
            painter.drawLine(4, 6, 5, 13)
            painter.drawLine(12, 6, 11, 13)
            painter.drawLine(5, 13, 11, 13)
            # Interior vertical strokes
            painter.drawLine(7, 7, 7, 12)
            painter.drawLine(9, 7, 9, 12)
        finally:
            painter.end()
        return QtGui.QIcon(pixmap)

    def _make_recover_icon(self, color="#8ac68a", size=16):
        """Draw a leftward-hook arrow (↩) suggesting 'put this back'. Shown
        on rows that are currently hidden (visible only via 'Show Hidden
        Assets') so the artist can restore them without editing the JSON."""
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pen = QtGui.QPen(QtGui.QColor(color))
            pen.setWidthF(1.4)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            painter.setPen(pen)
            # Coordinates on a 16x16 canvas. The glyph is a right-angle bend:
            # a vertical stem on the right, coming down and turning left into
            # a horizontal shaft ending in a leftward arrowhead.
            # Vertical stem (top-right, coming down)
            painter.drawLine(12, 3, 12, 10)
            # Horizontal shaft (going left from stem bottom)
            painter.drawLine(12, 10, 4, 10)
            # Arrowhead (left tip)
            painter.drawLine(4, 10, 7, 7)
            painter.drawLine(4, 10, 7, 13)
        finally:
            painter.end()
        return QtGui.QIcon(pixmap)

    def _load_thumbnail_pixmap(self, path, height, radius=6):
        """Load a project thumbnail, scale to `height`, and clip corners to
        `radius`. Silent when the file is missing/unreadable (thumbnails are
        optional per-project, unlike the studio logo). Returns None on any
        failure so the caller can just skip adding the widget."""
        if not path or not os.path.exists(path):
            return None
        src = QtGui.QPixmap(path)
        if src.isNull():
            return None
        scaled = src.scaledToHeight(height, QtCore.Qt.SmoothTransformation)
        rounded = QtGui.QPixmap(scaled.size())
        rounded.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(rounded)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            clip = QtGui.QPainterPath()
            clip.addRoundedRect(
                QtCore.QRectF(0, 0, scaled.width(), scaled.height()),
                radius, radius,
            )
            painter.setClipPath(clip)
            painter.drawPixmap(0, 0, scaled)
        finally:
            painter.end()
        return rounded

    def _load_logo_pixmap(self, path, opacity, height):
        """Load a logo image, scale to `height`, and pre-multiply alpha by
        `opacity` so it renders as a semi-transparent QPixmap. Returns None
        on missing/unreadable file so callers can silently skip the logo."""
        if not path or not os.path.exists(path):
            print(f"[ShotAssetLoader] Logo not found: {path}")
            return None
        src = QtGui.QPixmap(path)
        if src.isNull():
            print(f"[ShotAssetLoader] Could not read logo: {path}")
            return None
        scaled = src.scaledToHeight(height, QtCore.Qt.SmoothTransformation)
        faded = QtGui.QPixmap(scaled.size())
        faded.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(faded)
        painter.setOpacity(opacity)
        painter.drawPixmap(0, 0, scaled)
        painter.end()
        return faded

    def _init_ui(self):
        """Initialize UI."""
        # Top-level: a custom tab bar (checkable QPushButtons) above a
        # QStackedWidget. The existing dialog content goes on page 0 (Loader);
        # the Logs page reuses self.log_view (already created in __init__ so
        # the stdout/stderr redirect can be installed before any prints fire).
        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setSpacing(0)

        # Tab bar row — buttons sit flush against the top of the stack
        self.tab_bar_layout = QtWidgets.QHBoxLayout()
        self.tab_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_bar_layout.setSpacing(2)
        self.tab_buttons = []

        self.tab_stack = QtWidgets.QStackedWidget()

        loader_tab = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(loader_tab)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # Project title — drive letter prefix stripped, e.g. "I:\McDonald_2511" → "McDonald_2511".
        # If detection from the script path failed, advertise it explicitly
        # instead of silently displaying the fallback project's name.
        if self._project_detected:
            project_name = os.path.basename(self._project_root.rstrip(os.sep))
        else:
            project_name = "No Project Found"
        project_frame = QtWidgets.QFrame()
        project_frame.setObjectName("projectTitle")
        title_layout = QtWidgets.QHBoxLayout(project_frame)
        title_layout.setContentsMargins(18, 12, 18, 12)
        title_layout.setSpacing(12)

        # Per-project thumbnail — lives at <project_root>/00_Pipeline/project.jpg.
        # Optional: skipped silently when absent so unconfigured projects don't
        # spam the console. Placed left of the PROJECT text as a small avatar-
        # style preview.
        if self._project_detected:
            thumbnail_pixmap = self._load_thumbnail_pixmap(
                os.path.join(self._project_root, "00_Pipeline", "project.jpg"),
                height=56,
            )
            if thumbnail_pixmap is not None:
                thumbnail_label = QtWidgets.QLabel()
                thumbnail_label.setPixmap(thumbnail_pixmap)
                thumbnail_label.setFixedSize(thumbnail_pixmap.size())
                title_layout.addWidget(
                    thumbnail_label, alignment=QtCore.Qt.AlignVCenter,
                )

        title_text = QtWidgets.QLabel()
        title_text.setTextFormat(QtCore.Qt.RichText)
        title_text.setText(
            '<span style="font-size:10px; color:#8a8a8a; letter-spacing:2.5px; '
            'font-weight:600;">PROJECT</span><br>'
            f'<span style="font-size:20px; color:#f0f0f0; font-weight:700; '
            f'letter-spacing:0.5px;">{project_name}</span>'
        )
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        logo_pixmap = self._load_logo_pixmap(
            Config.LOGO_PATH, opacity=Config.LOGO_OPACITY, height=56,
        )
        if logo_pixmap is not None:
            logo_label = QtWidgets.QLabel()
            logo_label.setPixmap(logo_pixmap)
            logo_label.setFixedSize(logo_pixmap.size())
            title_layout.addWidget(logo_label, alignment=QtCore.Qt.AlignVCenter)

        main_layout.addWidget(project_frame)

        # Header banner — SHOT/FRAMES/FPS/FORMAT/ASSETS chips on the left,
        # the PKG snapshot browser on the right, all inside one framed strip
        # so the shot context reads as a single line.
        banner_frame = QtWidgets.QFrame()
        banner_frame.setObjectName("headerBanner")
        banner_layout = QtWidgets.QHBoxLayout(banner_frame)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        banner_layout.setSpacing(12)

        self.info_label = QtWidgets.QLabel("Detecting shot context from script path…")
        self.info_label.setObjectName("bannerText")
        self.info_label.setTextFormat(QtCore.Qt.RichText)
        banner_layout.addWidget(self.info_label)
        banner_layout.addStretch()

        package_label = QtWidgets.QLabel("PACKAGE :")
        package_label.setObjectName("filterLabel")
        banner_layout.addWidget(package_label)

        self.package_combo = _PackageComboBox()
        self.package_combo.setMinimumWidth(140)
        banner_layout.addWidget(self.package_combo)

        self.choose_package_btn = QtWidgets.QPushButton("Choose Package")
        self.choose_package_btn.setObjectName("secondaryAction")
        self.choose_package_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.choose_package_btn.clicked.connect(self._on_choose_package)
        banner_layout.addWidget(self.choose_package_btn)

        main_layout.addWidget(banner_frame)

        # Assets section
        assets_group = QtWidgets.QGroupBox("AVAILABLE ASSETS")
        assets_layout = QtWidgets.QVBoxLayout()
        assets_layout.setContentsMargins(6, 4, 6, 6)
        assets_layout.setSpacing(10)

        # Filter pills row
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setSpacing(6)
        filter_label = QtWidgets.QLabel("FILTERS :")
        filter_label.setObjectName("filterLabel")
        filter_layout.addWidget(filter_label)

        self.filter_buttons = {}
        filter_sources = ["All", "3dRender", "2dRender", "external", "Camera", "From Other Shots", "Loaded"]
        for source in filter_sources:
            btn = QtWidgets.QPushButton(source)
            btn.setObjectName("filterPill")
            btn.setCheckable(True)
            btn.setChecked(source == "All")
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, s=source: self._apply_source_filter(s))
            filter_layout.addWidget(btn)
            self.filter_buttons[source] = btn

        filter_layout.addStretch()

        # Show-hidden toggle — sits on the right, past the stretch, so it's
        # visually separated from the exclusive source pills on the left.
        # Toggling it repopulates the table: on = includes hidden entries with
        # a Recover button, off = filters them out entirely.
        self.show_hidden_checkbox = QtWidgets.QCheckBox("Show Hidden Assets")
        self.show_hidden_checkbox.setCursor(QtCore.Qt.PointingHandCursor)
        self.show_hidden_checkbox.setChecked(self._show_hidden)
        self.show_hidden_checkbox.toggled.connect(self._on_show_hidden_toggled)
        filter_layout.addWidget(self.show_hidden_checkbox)

        assets_layout.addLayout(filter_layout)

        # Asset table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Type", "Version",
            "Colorspace", "Status", "",
        ])
        column_widths = [200, 100, 100, 150, 280, 36]
        for i, w in enumerate(column_widths):
            self.table.setColumnWidth(i, w)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.horizontalHeader().setHighlightSections(False)
        # Status stretches to fill; the hide-button column stays fixed-narrow
        # regardless of window width.
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.Fixed)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Keep the colored Status cell visible even when the row is selected
        # (default selection highlight would mask the status color cue).
        self.table.setItemDelegateForColumn(4, _StatusColorDelegate(self.table))

        # Cell widgets (QComboBox in Version/Colorspace, QLineEdit for Cameras)
        # don't automatically follow a column resize until the user releases
        # the mouse. Force live geometry updates so the resize feels smooth.
        self.table.horizontalHeader().sectionResized.connect(self._on_column_resized)

        assets_layout.addWidget(self.table)
        assets_group.setLayout(assets_layout)
        main_layout.addWidget(assets_group, stretch=1)

        # Action bar — two action rows, then Close alone on its own row at
        # the bottom-right so it's clearly separated from destructive actions.
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(8)

        # Row 1 — selection helpers (left) + update actions (right)
        row1 = QtWidgets.QHBoxLayout()
        row1.setSpacing(8)

        select_all_btn = QtWidgets.QPushButton("Select All")
        select_all_btn.setCursor(QtCore.Qt.PointingHandCursor)
        select_all_btn.clicked.connect(self._select_all)
        row1.addWidget(select_all_btn)

        deselect_all_btn = QtWidgets.QPushButton("Deselect All")
        deselect_all_btn.setCursor(QtCore.Qt.PointingHandCursor)
        deselect_all_btn.clicked.connect(self._deselect_all)
        row1.addWidget(deselect_all_btn)

        row1.addStretch()

        check_updates_btn = QtWidgets.QPushButton("Check for Updates")
        check_updates_btn.setObjectName("warningAction")
        check_updates_btn.setCursor(QtCore.Qt.PointingHandCursor)
        check_updates_btn.clicked.connect(self._check_for_updates)
        row1.addWidget(check_updates_btn)

        update_selected_btn = QtWidgets.QPushButton("Update Selected")
        update_selected_btn.setObjectName("updateAction")
        update_selected_btn.setCursor(QtCore.Qt.PointingHandCursor)
        update_selected_btn.clicked.connect(self._update_selected_assets)
        row1.addWidget(update_selected_btn)

        update_all_loaded_btn = QtWidgets.QPushButton("Update All Loaded")
        update_all_loaded_btn.setObjectName("dangerAction")
        update_all_loaded_btn.setCursor(QtCore.Qt.PointingHandCursor)
        update_all_loaded_btn.clicked.connect(self._update_all_loaded_assets)
        row1.addWidget(update_all_loaded_btn)

        button_layout.addLayout(row1)

        # Row 2 — primary load actions
        row2 = QtWidgets.QHBoxLayout()
        row2.setSpacing(8)
        row2.addStretch()

        load_selected_btn = QtWidgets.QPushButton("Load Selected")
        load_selected_btn.setObjectName("primaryAction")
        load_selected_btn.setCursor(QtCore.Qt.PointingHandCursor)
        load_selected_btn.clicked.connect(self._load_selected_assets)
        row2.addWidget(load_selected_btn)

        load_all_btn = QtWidgets.QPushButton("Load All")
        load_all_btn.setObjectName("secondaryAction")
        load_all_btn.setCursor(QtCore.Qt.PointingHandCursor)
        load_all_btn.clicked.connect(self._load_all_assets)
        row2.addWidget(load_all_btn)

        button_layout.addLayout(row2)

        # Row 3 — Close alone, bottom-right
        close_row = QtWidgets.QHBoxLayout()
        close_row.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        close_row.addWidget(close_btn)
        button_layout.addLayout(close_row)

        main_layout.addLayout(button_layout)

        # ---- Render Manager page ----
        # Two tables side-by-side vertically: Precomp writes on top (Write
        # nodes whose name contains "Precomp"), other writes below. Both
        # are refreshed lazily when the tab becomes visible so newly-added
        # Writes are picked up without restarting the dialog.
        self.render_tab = QtWidgets.QWidget()
        render_layout = QtWidgets.QVBoxLayout(self.render_tab)
        render_layout.setContentsMargins(14, 14, 14, 14)
        render_layout.setSpacing(12)

        precomp_group = QtWidgets.QGroupBox("WRITES PRECOMP")
        precomp_group_layout = QtWidgets.QVBoxLayout()
        precomp_group_layout.setContentsMargins(6, 4, 6, 6)
        self.precomp_writes_table = self._build_writes_table(
            ["Name", "Identifier", "Version", "Render Order", "Status"]
        )
        self.precomp_writes_table.setColumnWidth(0, 220)
        self.precomp_writes_table.setColumnWidth(1, 220)
        self.precomp_writes_table.setColumnWidth(2, 80)
        self.precomp_writes_table.setColumnWidth(3, 110)
        # Same delegate as the loader table so the Cached/Live tint is not
        # washed out by the row-selection highlight.
        self.precomp_writes_table.setItemDelegateForColumn(
            4, _StatusColorDelegate(self.precomp_writes_table)
        )
        precomp_group_layout.addWidget(self.precomp_writes_table)
        precomp_group.setLayout(precomp_group_layout)
        render_layout.addWidget(precomp_group, stretch=1)

        # Write Compo — typically a single final-output Write. stretch=0 +
        # a height cap on the table itself (see _size_writes_table_to_content)
        # keeps the section from claiming half the tab for one row.
        compo_group = QtWidgets.QGroupBox("WRITES COMPO")
        compo_group_layout = QtWidgets.QVBoxLayout()
        compo_group_layout.setContentsMargins(6, 4, 6, 6)
        self.compo_writes_table = self._build_writes_table(
            ["Name", "Identifier", "Version", "Render Order"]
        )
        self.compo_writes_table.setColumnWidth(0, 220)
        self.compo_writes_table.setColumnWidth(2, 80)
        self.compo_writes_table.setColumnWidth(3, 110)
        # Identifier takes the leftover width so long identifiers stay
        # readable; Name, Version and Render Order keep their fixed size.
        compo_header = self.compo_writes_table.horizontalHeader()
        compo_header.setStretchLastSection(False)
        compo_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        compo_group_layout.addWidget(self.compo_writes_table)
        compo_group.setLayout(compo_group_layout)
        render_layout.addWidget(compo_group, stretch=0)

        render_actions = QtWidgets.QHBoxLayout()

        render_all_btn = QtWidgets.QPushButton("Render Compo and Precomps")
        render_all_btn.setObjectName("primaryAction")
        render_all_btn.setCursor(QtCore.Qt.PointingHandCursor)
        render_all_btn.clicked.connect(self._submit_render_all)
        render_actions.addWidget(render_all_btn)

        render_compo_btn = QtWidgets.QPushButton("Render Compo")
        render_compo_btn.setObjectName("secondaryAction")
        render_compo_btn.setCursor(QtCore.Qt.PointingHandCursor)
        render_compo_btn.clicked.connect(self._submit_render_compo)
        render_actions.addWidget(render_compo_btn)

        render_precomps_btn = QtWidgets.QPushButton("Render Precomps")
        render_precomps_btn.setObjectName("updateAction")
        render_precomps_btn.setCursor(QtCore.Qt.PointingHandCursor)
        render_precomps_btn.clicked.connect(self._submit_render_precomps)
        render_actions.addWidget(render_precomps_btn)

        render_actions.addStretch()
        refresh_writes_btn = QtWidgets.QPushButton("Refresh")
        refresh_writes_btn.setCursor(QtCore.Qt.PointingHandCursor)
        refresh_writes_btn.clicked.connect(self._refresh_render_manager)
        render_actions.addWidget(refresh_writes_btn)
        render_layout.addLayout(render_actions)

        # ---- Logs page ----
        logs_tab = QtWidgets.QWidget()
        logs_layout = QtWidgets.QVBoxLayout(logs_tab)
        logs_layout.setContentsMargins(14, 14, 14, 14)
        logs_layout.setSpacing(8)
        logs_layout.addWidget(self.log_view)

        logs_buttons = QtWidgets.QHBoxLayout()
        logs_buttons.addStretch()
        clear_log_btn = QtWidgets.QPushButton("Clear")
        clear_log_btn.setCursor(QtCore.Qt.PointingHandCursor)
        clear_log_btn.clicked.connect(self.log_view.clear)
        logs_buttons.addWidget(clear_log_btn)
        logs_layout.addLayout(logs_buttons)

        # Register all pages, then build the matching tab buttons. Order
        # matters — the index passed to _add_tab_button must match the
        # widget's position in tab_stack.
        self.tab_stack.addWidget(loader_tab)
        self.tab_stack.addWidget(self.render_tab)
        self.tab_stack.addWidget(logs_tab)

        self._add_tab_button("Loader", 0)
        self._add_tab_button("Render Manager", 1)
        self._add_tab_button("Logs", 2)
        self.tab_buttons[0].setChecked(True)
        self.tab_bar_layout.addStretch()

        outer_layout.addLayout(self.tab_bar_layout)
        outer_layout.addWidget(self.tab_stack)
        self.setLayout(outer_layout)

        # Apply the global stylesheet last so all objectName tags resolve.
        self.setStyleSheet(STYLESHEET)

    def _add_tab_button(self, label, page_index):
        btn = QtWidgets.QPushButton(label)
        btn.setObjectName("tabHeader")
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setCursor(QtCore.Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked=False, i=page_index: self._switch_tab(i))
        self.tab_buttons.append(btn)
        self.tab_bar_layout.addWidget(btn)

    def _switch_tab(self, index):
        self.tab_stack.setCurrentIndex(index)
        # Render Manager lazily re-scans on every visit so Writes added
        # or renamed since the last look show up without a manual refresh.
        if self.tab_stack.currentWidget() is getattr(self, "render_tab", None):
            self._refresh_render_manager()

    def _build_writes_table(self, columns):
        """Factory for a Write-node table with the given column labels. The
        two Render Manager tables share styling (row height, selection
        behaviour, header colouring) but not their column layout — Precomp
        writes carry Version/Status metadata while the Compo table just
        lists the node."""
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
        return table

    def _refresh_render_manager(self):
        """Scan the current scene for Write nodes and split them across the
        two tables: nodes carrying the studio's `tag` knob set to
        "PrecompWrite" go to the top table (matching the gizmo tag is more
        robust than a name check since the artist can rename the node);
        the remaining writes whose name contains "Compo" go to the bottom.
        Writes matching neither rule are silently skipped — they aren't
        part of the comp render pipeline."""
        precomp_writes = []
        compo_writes = []
        for node in nuke.allNodes("Write"):
            if self._read_tag(node) == "PrecompWrite":
                precomp_writes.append(node)
            elif "Compo" in node.name():
                compo_writes.append(node)
        # Redistribute render_order across every Write upstream of
        # Write_Compo before displaying, so the Render Order column
        # reflects the freshly-computed topological order rather than a
        # stale value the artist may have left behind.
        self._distribute_render_orders()
        self._populate_precomp_table(precomp_writes)
        self._populate_compo_table(compo_writes)
        # Compo table is usually a single row — cap its height so it doesn't
        # split the tab in half. Done after populate so the row count is
        # already reflected in the table.
        self._size_writes_table_to_content(self.compo_writes_table)

    def _read_tag(self, node):
        """Safe read of a node's `tag` knob (empty string if absent). Wrapped
        because the knob is set by the Precomp gizmo, so unrelated Writes
        won't have it and we don't want a bare `node['tag']` KeyError."""
        try:
            if 'tag' in node.knobs():
                return (node['tag'].value() or "").strip()
        except Exception:
            pass
        return ""

    def _distribute_render_orders(self):
        """Auto-assign render_order on every Write upstream of the Compo
        Write via the studio helper so precomps render before the final
        comp. The Compo Write is located by matching the same filter as
        the Write Compo table (any Write whose name contains "Compo" and
        doesn't carry the PrecompWrite tag) so variant namings like
        "Write_Compo_v001" still trigger the distribution — an earlier
        version hardcoded "Write_Compo" and silently skipped in every
        other case. Errors are swallowed with a log so a broken graph
        doesn't break the tab."""
        compo_write = None
        for node in nuke.allNodes("Write"):
            if self._read_tag(node) == "PrecompWrite":
                continue
            if "Compo" in node.name():
                compo_write = node
                break

        if compo_write is None:
            print(
                "[ShotAssetLoader] No Compo Write found in the scene — "
                "skipping render_order distribution"
            )
            return

        print(
            f"[ShotAssetLoader] Distributing render_order upstream of "
            f"{compo_write.name()}"
        )
        try:
            distribute_write_render_order(root_name=compo_write.name())
        except Exception as e:
            print(f"[ShotAssetLoader] distribute_write_render_order failed: {e}")

    def _submit_render_all(self):
        compo = self._find_compo_write()
        live = self._find_live_precomp_writes()
        if not (live or compo):
            print(
                "[ShotAssetLoader] Nothing to render (no Live precomps and no "
                "Compo write) — aborting Deadline submit"
            )
            return
        self._prism_save_version()
        self._bump_precomp_versions(live)
        self._refresh_compo_write(compo)
        self._select_only(list(live) + ([compo] if compo else []))
        self._launch_deadline_submit("Render Compo and Precomps")

    def _submit_render_compo(self):
        compo = self._find_compo_write()
        if compo is None:
            print(
                "[ShotAssetLoader] No Compo write found — aborting Deadline submit"
            )
            return
        self._prism_save_version()
        self._refresh_compo_write(compo)
        self._select_only([compo])
        self._launch_deadline_submit("Render Compo")

    def _submit_render_precomps(self):
        live = self._find_live_precomp_writes()
        if not live:
            print(
                "[ShotAssetLoader] No Live precomps to render — aborting "
                "Deadline submit"
            )
            return
        self._prism_save_version()
        self._bump_precomp_versions(live)
        self._select_only(live)
        self._launch_deadline_submit("Render Precomps")

    def _prism_save_version(self):
        """Trigger Prism's 'Save Version' menu action so every farm submit
        is pinned to a fresh, versioned .nk on disk — Deadline copies the
        current script to the farm, and without a save the artist could
        submit a stale version to renders."""
        item = nuke.menu("Nuke").findItem("Prism/Save Version")
        if item is None:
            print(
                "[ShotAssetLoader] Prism/Save Version not found in the Nuke "
                "menu — skipping save (submitting current on-disk state)"
            )
            return
        try:
            item.invoke()
            print("[ShotAssetLoader] Prism Save Version invoked")
        except Exception as e:
            print(f"[ShotAssetLoader] Prism Save Version failed: {e}")

    def _bump_precomp_versions(self, nodes):
        """Kick each precomp Write's `add_version` knob so its output path
        rolls to the next version before we submit — otherwise the farm
        would overwrite the current cache in place."""
        for node in nodes:
            if 'add_version' not in node.knobs():
                print(
                    f"[ShotAssetLoader] No 'add_version' knob on {node.name()} "
                    "— skipping"
                )
                continue
            try:
                node['add_version'].execute()
                print(f"[ShotAssetLoader] add_version on {node.name()}")
            except Exception as e:
                print(
                    f"[ShotAssetLoader] add_version failed on {node.name()}: {e}"
                )

    def _refresh_compo_write(self, node):
        """Kick the Compo write's `refresh` knob so its metadata (typically
        the versioned output path and frame range) matches the just-saved
        script before the submit dialog reads it."""
        if node is None:
            return
        if 'refresh' not in node.knobs():
            print(
                f"[ShotAssetLoader] No 'refresh' knob on {node.name()} — skipping"
            )
            return
        try:
            node['refresh'].execute()
            print(f"[ShotAssetLoader] refresh on {node.name()}")
        except Exception as e:
            print(f"[ShotAssetLoader] refresh failed on {node.name()}: {e}")

    def _iter_precomp_writes(self):
        """Yield every Write node carrying the studio's PrecompWrite tag.
        recurseGroups=True so Writes wrapped inside a studio gizmo still get
        picked up — the table's own scan runs at root only, so if this
        starts returning extras that don't appear in the table, we'll need
        to bring the two scans back in sync."""
        for node in nuke.allNodes("Write", recurseGroups=True):
            if self._read_tag(node) == "PrecompWrite":
                yield node

    def _find_compo_write(self):
        """The Compo Write is any non-PrecompWrite Write whose name contains
        'Compo' — mirrors the Write Compo table and _distribute_render_orders
        so the three code paths agree on which node is the final output."""
        for node in nuke.allNodes("Write", recurseGroups=True):
            if self._read_tag(node) == "PrecompWrite":
                continue
            if "Compo" in node.name():
                return node
        return None

    def _find_live_precomp_writes(self):
        """Precomps whose cache is missing/stale — the gizmo's hasError() is
        True when its internal cache Read fails, matching the 'Live' state
        shown in the Render Manager table. Cached precomps are skipped
        because their disk output already exists; re-rendering them would
        just burn farm time."""
        live = []
        for node in self._iter_precomp_writes():
            try:
                err = node.hasError()
            except Exception as e:
                print(
                    f"[ShotAssetLoader]   {node.name()} hasError raised {e}"
                    " — treating as Live"
                )
                err = True
            state = "Live" if err else "Cached"
            print(f"[ShotAssetLoader]   {node.name()}: {state}")
            if err:
                live.append(node)
        return live

    def _select_only(self, nodes):
        """Clear the whole scene's selection then select the given nodes.
        Deadline's 'Selected Nodes Only' (set by our sanity check) uses this
        selection to decide which Writes to submit, so any stray selection
        the artist left behind would silently join the job."""
        for n in nuke.allNodes(recurseGroups=True):
            try:
                n.setSelected(False)
            except Exception:
                pass
        names = []
        for n in nodes:
            try:
                n.setSelected(True)
                names.append(n.name())
            except Exception:
                pass
        print(f"[ShotAssetLoader] Selected for submit: {', '.join(names) or '(none)'}")

    def _launch_deadline_submit(self, source):
        """Invoke the Illogic fork of the Nuke-to-Deadline submitter. The fork
        (SubmitNukeToDeadline_Illogic on the Deadline repo, next to the stock
        SubmitNukeToDeadline) groups Writes by render_order for dependencies so
        siblings run in parallel instead of chaining. Falls back to the stock
        Thinkbox menu action if the fork isn't importable — e.g. the network
        share is unreachable or the fork hasn't been deployed yet."""
        print(f"[ShotAssetLoader] {source} -> Submit Nuke To Deadline (Illogic fork)")
        self._prime_deadline_sticky()
        try:
            import SubmitNukeToDeadline_Illogic  # type: ignore
            SubmitNukeToDeadline_Illogic.SubmitToDeadline()
            return
        except Exception as e:
            print(
                f"[ShotAssetLoader] Illogic submitter unavailable ({e}) — "
                "falling back to Thinkbox menu"
            )

        item = nuke.menu("Nuke").findItem("Thinkbox/Submit Nuke To Deadline")
        if item is None:
            print(
                "[ShotAssetLoader] Thinkbox/Submit Nuke To Deadline not found "
                "in the Nuke menu — is the Deadline submitter installed?"
            )
            return
        try:
            item.invoke()
        except Exception as e:
            print(f"[ShotAssetLoader] Deadline submitter failed: {e}")

    def _prime_deadline_sticky(self):
        """Overwrite the Deadline Nuke sticky ini with our per-project defaults
        before the submit dialog opens. The submitter reads the ini at startup
        (ReadStickySettings) and pipes it through DeadlineGlobals, so anything
        we write here shows up in the dialog. Pool/group come from the project's
        pipeline.json (poolPresets 'Nuke' entry); the rest are studio-wide
        constants requested for these buttons."""
        import configparser

        pool = None
        group = None
        pipeline_json = os.path.join(
            self._project_root, "00_Pipeline", "pipeline.json"
        )
        try:
            with open(pipeline_json, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for preset in data.get("deadline", {}).get("poolPresets", []):
                if preset.get("name") == "Nuke":
                    pool = preset.get("pool")
                    group = preset.get("group")
                    break
            if pool is None or group is None:
                print(
                    "[ShotAssetLoader] pipeline.json has no poolPresets 'Nuke' "
                    f"entry at {pipeline_json} — pool/group left untouched"
                )
        except Exception as e:
            print(
                f"[ShotAssetLoader] Could not read {pipeline_json}: {e} — "
                "pool/group left untouched"
            )

        sticky_path = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Thinkbox", "Deadline10", "settings", "nuke_py_submission.ini",
        )
        try:
            os.makedirs(os.path.dirname(sticky_path), exist_ok=True)
            config = configparser.ConfigParser()
            if os.path.isfile(sticky_path):
                config.read(sticky_path)
            if not config.has_section("Sticky"):
                config.add_section("Sticky")

            if pool:
                config.set("Sticky", "Pool", pool)
            if group:
                config.set("Sticky", "Group", group)
            config.set("Sticky", "Priority", "90")
            config.set("Sticky", "FrameListMode", "Global")
            config.set("Sticky", "EnforceRenderOrder", "True")
            config.set("Sticky", "SubmitScene", "False")
            config.set("Sticky", "BatchMode", "True")

            with open(sticky_path, "w") as fh:
                config.write(fh)
            print(
                f"[ShotAssetLoader] Deadline sticky primed (pool={pool} "
                f"group={group}) at {sticky_path}"
            )
        except Exception as e:
            print(f"[ShotAssetLoader] Could not prime Deadline sticky: {e}")

        # Deadline's ReadSceneStickySettings reads hidden String knobs stored
        # on nuke.root() by previous submissions and OVERWRITES the ini-derived
        # values. If any of those knobs exist, we have to update them too or
        # the .ini is silently ignored. Absent knobs are left alone so the ini
        # wins for scenes that were never submitted before.
        root = nuke.root()
        root_overrides = {}
        if pool:
            root_overrides["Pool"] = pool
        if group:
            root_overrides["Group"] = group
        root_overrides["Priority"] = "90"
        root_overrides["FrameListMode"] = "Global"
        root_overrides["EnforceRenderOrder"] = "True"
        root_overrides["SubmitScene"] = "False"
        root_overrides["BatchMode"] = "True"
        updated = []
        for name, value in root_overrides.items():
            if name in root.knobs():
                try:
                    root.knob(name).setValue(value)
                    updated.append(name)
                except Exception as e:
                    print(
                        f"[ShotAssetLoader] Could not update root knob {name}: {e}"
                    )
        if updated:
            print(
                "[ShotAssetLoader] Root sticky knobs overridden: "
                f"{', '.join(updated)}"
            )

    def _size_writes_table_to_content(self, table):
        """Pin a writes table's height to just enough for its rows. Used on
        the Write Compo table so a single entry doesn't get half the tab
        to itself. Clamped to at least one row (empty table still reads as
        a table, not a collapsed strip) and at most four rows before it
        starts scrolling."""
        row_h = table.verticalHeader().defaultSectionSize()
        header_h = table.horizontalHeader().height() or 30
        frame_pad = table.frameWidth() * 2
        rows = max(1, min(4, table.rowCount()))
        height = header_h + row_h * rows + frame_pad + 6
        table.setMinimumHeight(height)
        table.setMaximumHeight(height)

    def _make_bold_name_cell(self, node):
        """Read-only bold-font table cell showing a node's name. Shared by
        both Render Manager tables so styling stays in sync."""
        item = QtWidgets.QTableWidgetItem(node.name())
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        return item

    def _make_render_order_cell(self, node):
        """Read-only cell showing a node's render_order as an integer.
        Empty when the knob is absent (shouldn't happen on a real Write)
        or unreadable."""
        text = ""
        try:
            if 'render_order' in node.knobs():
                text = str(int(node['render_order'].value()))
        except Exception:
            text = ""
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        return item

    def _make_version_cell(self, node):
        """Read-only cell showing a Write's version as vNNN.

        Two conventions coexist: the Precomp gizmo exposes an integer
        `versions` knob, while the Compo Write publishes its resolved
        output path through a `fileName` text knob (e.g.
        `.../Compo/v007/SBX-mathieu_Compo_v007.####.exr`). We try both,
        plus the vanilla `file` knob as a last resort so a hand-built
        Write still surfaces a version instead of a blank cell."""
        version_text = ""
        try:
            if 'versions' in node.knobs():
                raw = node['versions'].value()
                try:
                    version_text = f"v{int(raw):03d}"
                except (TypeError, ValueError):
                    # Non-numeric knob value (unusual) — surface as-is
                    # rather than dropping the info silently.
                    version_text = "" if raw is None else str(raw)
        except Exception:
            version_text = ""
        if not version_text:
            for knob_name in ("fileName", "file"):
                try:
                    if knob_name not in node.knobs():
                        continue
                    path = node[knob_name].value() or ""
                    if not path:
                        continue
                    parsed = extract_version_from_path(path)
                    if parsed:
                        version_text = parsed
                        break
                except Exception:
                    continue
        item = QtWidgets.QTableWidgetItem(version_text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        return item

    def _make_identifier_cell(self, node, prefix=""):
        """Read-only cell showing the node's `identifier` knob value, with
        an optional prefix (used for Precomp writes so their identifier
        reads as e.g. 'precomp_shot010_bg' and can't be confused with a
        Compo identifier of the same base name)."""
        text = ""
        try:
            if 'identifier' in node.knobs():
                raw = node['identifier'].value()
                if raw:
                    text = f"{prefix}{raw}"
        except Exception:
            text = ""
        item = QtWidgets.QTableWidgetItem(text)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        return item

    def _populate_precomp_table(self, nodes):
        """Fill the Precomp Writes table with (Name, Version, Status) rows.

        Version comes from the `versions` knob, formatted as vNNN. Status
        is "Live" when the Write's input(0) has an error (typically the
        cached precomp is missing / stale so the graph falls through to the
        live comp), and "Cached" otherwise — mirroring the TCL expression
        the studio uses on the node's own label."""
        table = self.precomp_writes_table
        table.setRowCount(0)
        for row, node in enumerate(nodes):
            table.insertRow(row)
            table.setItem(row, 0, self._make_bold_name_cell(node))
            table.setItem(row, 1, self._make_identifier_cell(node, prefix="precomp_"))
            table.setItem(row, 2, self._make_version_cell(node))
            table.setItem(row, 3, self._make_render_order_cell(node))

            # The studio's TCL uses `input(0).hasError()` from *inside* the
            # gizmo, where input(0) is the internal Read pointing at the
            # cache file. Called from Python on the outer gizmo, input(0)
            # would resolve to the external upstream (usually a Grade or
            # similar) which is not what we want — a live comp with a
            # healthy upstream would then report "Cached" even though the
            # cache Read is failing. Reading `hasError()` directly on the
            # gizmo is equivalent for this purpose since the internal Read
            # error propagates to the gizmo's error state.
            try:
                status_text = "Live" if node.hasError() else "Cached"
            except Exception:
                status_text = "?"
            s_item = QtWidgets.QTableWidgetItem(status_text)
            s_item.setFlags(s_item.flags() & ~QtCore.Qt.ItemIsEditable)
            # Same greens/reds as the loader Status column so the two tables
            # speak the same visual language (green = ready, red = stale).
            if status_text == "Cached":
                s_item.setBackground(QtGui.QColor("#3a5a3a"))
            elif status_text == "Live":
                s_item.setBackground(QtGui.QColor("#aa2c2c"))
            table.setItem(row, 4, s_item)

    def _populate_compo_table(self, nodes):
        """Fill the Write Compo table (Name + Identifier + Version + Render
        Order). Render Order completes the picture from the Precomp table:
        the Compo write is the root of the topological distribution and
        receives the highest value, so seeing it next to the Precomp orders
        makes the whole render sequence readable at a glance."""
        table = self.compo_writes_table
        table.setRowCount(0)
        for row, node in enumerate(nodes):
            table.insertRow(row)
            table.setItem(row, 0, self._make_bold_name_cell(node))
            table.setItem(row, 1, self._make_identifier_cell(node))
            table.setItem(row, 2, self._make_version_cell(node))
            table.setItem(row, 3, self._make_render_order_cell(node))

    def _detect_script_context(self):
        """Auto-detect sequence/shot from the Nuke script path, then scan."""
        try:
            script_path = nuke.root().name()

            # nuke.root().name() returns "Root" when the script isn't saved.
            if not script_path or script_path == "Root":
                self.info_label.setText(
                    "Save your Nuke script inside a shot folder to use the loader"
                )
                return

            normalized = script_path.replace('\\', '/')

            detected_sequence = None
            detected_shot = None

            # 1. Try filename pattern: <sequence>-<shot>_<task>_v<###>.nk
            #    e.g. SEQ_busInt-SH130_comp_v001.nk or LINEUP-CHAR_ALL_Compo_v001.nk.
            #    The shot itself may contain underscores (CHAR_ALL), so we
            #    anchor on `_<task>_v###.nk` at the tail and let the shot
            #    group greedily consume everything before it. Task is assumed
            #    to be a single token (no underscore).
            filename = normalized.rsplit('/', 1)[-1]
            filename_match = re.match(r'^([^-]+)-(.+)_[^_]+_v\d{3,4}\.nk$', filename)
            if filename_match:
                detected_sequence = filename_match.group(1)
                detected_shot = filename_match.group(2)
                print(f"[ShotAssetLoader] Detected from filename: {detected_sequence}/{detected_shot}")

            # 2. Fallback: path pattern /Shots/SEQ_xxx/SHxxx/
            if not detected_sequence or not detected_shot:
                path_match = re.search(r'/Shots/(SEQ_[^/]+)/(SH\d+)/', normalized)
                if path_match:
                    detected_sequence = path_match.group(1)
                    detected_shot = path_match.group(2)
                    print(f"[ShotAssetLoader] Detected from path: {detected_sequence}/{detected_shot}")

            if not detected_sequence or not detected_shot:
                self.info_label.setText(
                    "Could not detect sequence/shot from the script path"
                )
                return

            self.current_sequence = detected_sequence
            self.current_shot = detected_shot
            print(f"[ShotAssetLoader] Auto-selected: {detected_sequence}/{detected_shot}")

            self._scan_shot_assets()
            # Silent check on opening so the status column is accurate without popups
            self._do_check_for_updates(silent=True)

        except Exception as e:
            print(f"[ShotAssetLoader] Context detection failed (not critical): {e}")

    def _scan_shot_assets(self):
        """Scan assets for the current detected shot context."""
        sequence = self.current_sequence
        shot = self.current_shot

        if not sequence or not shot:
            return

        self.info_label.setText(f"Scanning assets for {sequence}/{shot}...")
        QtWidgets.QApplication.processEvents()

        print(f"\n[ShotAssetLoader] === SCAN START ===")
        print(f"[ShotAssetLoader] Project root: {self._project_root}")
        print(f"[ShotAssetLoader] Sequence: {sequence} | Shot: {shot}")

        self.current_assets = self.discoverer.discover_all_assets(sequence, shot)

        print(f"[ShotAssetLoader] === SCAN RESULTS ===")
        print(f"[ShotAssetLoader]   plates:     {len(self.current_assets.get('plates', {}))}")
        print(f"[ShotAssetLoader]   3d_renders: {len(self.current_assets.get('3d_renders', {}))}")
        print(f"[ShotAssetLoader]   2d_renders: {len(self.current_assets.get('2d_renders', {}))}")
        print(f"[ShotAssetLoader]   rotos:      {len(self.current_assets.get('rotos', {}))}")
        print(f"[ShotAssetLoader]   cameras:    {len(self.current_assets.get('cameras', {}))}")
        print(f"[ShotAssetLoader] === SCAN END ===")

        # Populate table
        self._populate_table()
        self._refresh_info_banner()
        # Packages are shot-scoped — reload the combo whenever the shot
        # context changes.
        self._refresh_package_dropdown()

    def _refresh_info_banner(self):
        """Rebuild the SHOT/FRAMES/FPS/FORMAT/ASSETS chip banner from the
        current scene state and asset list. Extracted from _scan_shot_assets
        so a lightweight refresh (e.g. after hiding an asset) can update the
        ASSETS count without triggering a full disk re-scan."""
        sequence = self.current_sequence
        shot = self.current_shot
        if not sequence or not shot:
            return

        # Frame range comes from the current Nuke scene — that's what the
        # artist is actually working in.
        try:
            frame_range = (
                int(nuke.root()['first_frame'].value()),
                int(nuke.root()['last_frame'].value()),
            )
        except Exception:
            frame_range = None
        frame_text = f"{frame_range[0]}-{frame_range[1]}" if frame_range else "Unknown"

        # Pull FPS and Format straight from the current Nuke scene — that's
        # what the artist is actually working in, more trustworthy than the
        # project defaults.
        fps_text = "Unknown"
        format_text = "Unknown"
        try:
            fps_value = float(nuke.root()['fps'].value())
            # Drop the trailing ".0" on integer framerates (24.0 → "24")
            fps_text = (
                f"{int(fps_value)}" if fps_value.is_integer() else f"{fps_value:g}"
            )
        except Exception:
            pass
        try:
            fmt = nuke.root()['format'].value()
            if fmt is not None:
                format_text = f"{fmt.width()}x{fmt.height()}"
        except Exception:
            pass

        total_assets = len(self.asset_items)
        chip = (
            "<span style='color:#9a9a9a; font-size:10px; letter-spacing:1.2px;'>"
            "{label}</span> &nbsp;<span style='color:#ffffff;'>{value}</span>"
        )
        self.info_label.setText(
            chip.format(label="SHOT", value=f"<b>{sequence}</b> / <b>{shot}</b>")
            + " &nbsp;&nbsp;&nbsp;&nbsp; "
            + chip.format(label="FRAMES", value=frame_text)
            + " &nbsp;&nbsp;&nbsp;&nbsp; "
            + chip.format(label="FPS", value=fps_text)
            + " &nbsp;&nbsp;&nbsp;&nbsp; "
            + chip.format(label="FORMAT", value=format_text)
            + " &nbsp;&nbsp;&nbsp;&nbsp; "
            + chip.format(label="ASSETS", value=str(total_assets))
        )

    def _populate_table(self):
        """Populate asset table."""
        self.asset_items.clear()
        self.table.setRowCount(0)

        # Assets the user has explicitly hidden for this shot via the trash
        # button — read from the per-project prefs JSON. Any (type, name)
        # match here is silently skipped below.
        hidden_set = self._hidden_set_for_shot()

        # Scene frame range — used to default the Version dropdown to the
        # highest *full-coverage* version rather than the absolute latest, so
        # the first load doesn't silently pick up a partial render.
        try:
            scene_range = (
                int(nuke.root()['first_frame'].value()),
                int(nuke.root()['last_frame'].value()),
            )
        except Exception:
            scene_range = None

        row = 0

        # Plates
        for plate_name, versions_dict in self.current_assets.get("plates", {}).items():
            if self._is_precomp_asset(plate_name):
                continue
            is_hidden = ("Plate", plate_name) in hidden_set
            if is_hidden and not self._show_hidden:
                continue
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("Plate", plate_name, versions, versions_dict, source_type="external")
            item.is_hidden = is_hidden
            self._default_to_latest_full(item, scene_range)
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # 3D Renders
        for render_name, versions_dict in self.current_assets.get("3d_renders", {}).items():
            if self._is_precomp_asset(render_name):
                continue
            is_hidden = ("3D Render", render_name) in hidden_set
            if is_hidden and not self._show_hidden:
                continue
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("3D Render", render_name, versions, versions_dict, source_type="3dRender")
            item.is_hidden = is_hidden
            self._default_to_latest_full(item, scene_range)
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # 2D Renders
        for render_name, versions_dict in self.current_assets.get("2d_renders", {}).items():
            if self._is_precomp_asset(render_name):
                continue
            is_hidden = ("2D Render", render_name) in hidden_set
            if is_hidden and not self._show_hidden:
                continue
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("2D Render", render_name, versions, versions_dict, source_type="2dRender")
            item.is_hidden = is_hidden
            self._default_to_latest_full(item, scene_range)
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # Rotos (all versions). Hidden as a group under the shared name
        # "roto" — one trash click hides every version row at once, matching
        # how the user thinks about "the roto" as one asset.
        rotos = self.current_assets.get("rotos", {})
        roto_hidden = ("Roto", "roto") in hidden_set
        if self._show_hidden or not roto_hidden:
            for version in sorted(rotos.keys()):
                layers = rotos[version]

                item = AssetItem("Roto", "roto", [version], {version: layers}, source_type="external")
                item.selected_version = version
                item.is_hidden = roto_hidden
                self.asset_items.append(item)
                self._add_row(row, item)
                row += 1

        # Cameras
        for cam_name, versions_dict in self.current_assets.get("cameras", {}).items():
            if self._is_precomp_asset(cam_name):
                continue
            is_hidden = ("Camera", cam_name) in hidden_set
            if is_hidden and not self._show_hidden:
                continue
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("Camera", cam_name, versions, versions_dict, source_type="Camera")
            item.is_hidden = is_hidden
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # Foreign-shot Reads — discovered straight from the scene. Their
        # loaded_node is bound at creation time so _do_check_for_updates can
        # treat them like already-loaded local assets.
        for foreign_item in self._discover_foreign_assets():
            if self._is_precomp_asset(foreign_item.asset_name):
                continue
            is_hidden = (foreign_item.asset_type, foreign_item.asset_name) in hidden_set
            if is_hidden and not self._show_hidden:
                continue
            foreign_item.is_hidden = is_hidden
            self.asset_items.append(foreign_item)
            self._add_row(row, foreign_item)
            row += 1

        # Hide source filters that have no matching assets (e.g. "external"
        # when the shot has neither plates nor rotos).
        self._refresh_filter_visibility()

        # Re-apply active filter after repopulating
        active_filter = "All"
        for source, btn in self.filter_buttons.items():
            if btn.isChecked():
                active_filter = source
                break
        if active_filter != "All":
            self._apply_source_filter(active_filter)

    def _refresh_filter_visibility(self):
        """Hide source-specific filter pills that have zero matching items.
        'All' and 'Loaded' stay always visible. 'From Other Shots' shows only
        when at least one foreign-shot item is present. If the active filter
        is the one being hidden, fall back to 'All'."""
        source_types_present = {item.source_type for item in self.asset_items}
        has_foreign = any(item.is_foreign for item in self.asset_items)
        for source, btn in self.filter_buttons.items():
            if source in ("All", "Loaded"):
                btn.setVisible(True)
                continue
            if source == "From Other Shots":
                btn.setVisible(has_foreign)
                continue
            btn.setVisible(source in source_types_present)

        # If the active filter just became invisible, switch back to "All"
        for source, btn in self.filter_buttons.items():
            if btn.isChecked() and not btn.isVisible():
                self._apply_source_filter("All")
                break

    def _add_row(self, row, item):
        """Add a row to table."""
        self.table.insertRow(row)

        # Col 0 - Name (bold, primary identifier). Foreign-shot assets get a
        # "(from SQ/SH)" suffix so the artist sees the origin at a glance.
        display_name = item.asset_name
        if item.is_foreign:
            display_name = f"{item.asset_name}  (from {item.foreign_sequence}/{item.foreign_shot})"
        name_item = QtWidgets.QTableWidgetItem(display_name)
        name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
        name_font = name_item.font()
        name_font.setBold(True)
        name_item.setFont(name_font)
        self.table.setItem(row, 0, name_item)

        # Col 1 - Type
        type_item = QtWidgets.QTableWidgetItem(item.asset_type)
        type_item.setFlags(type_item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.table.setItem(row, 1, type_item)

        # Col 2 - Version dropdown
        version_combo = QtWidgets.QComboBox()
        version_combo.addItems(item.versions)
        version_combo.setCurrentText(item.selected_version)
        version_combo.currentTextChanged.connect(lambda v, r=row: self._on_version_changed(r, v))
        self.table.setCellWidget(row, 2, version_combo)

        # Col 3 - Colorspace dropdown
        colorspace_combo = QtWidgets.QComboBox()
        colorspaces = self._get_ocio_colorspaces()
        colorspace_combo.addItems(colorspaces)
        colorspace_combo.setCurrentText(item.selected_colorspace)
        colorspace_combo.currentTextChanged.connect(lambda cs, r=row: self._on_colorspace_changed(r, cs))
        self.table.setCellWidget(row, 3, colorspace_combo)

        # Col 4 - Status (custom delegate keeps the color visible when selected)
        status_item = QtWidgets.QTableWidgetItem(item.status_text)
        status_item.setFlags(status_item.flags() & ~QtCore.Qt.ItemIsEditable)
        if item.status_color:
            status_item.setBackground(QtGui.QColor(item.status_color))
        self.table.setItem(row, 4, status_item)

        # Col 5 - Trash button (normal rows) OR Recover button (rows shown
        # only because "Show Hidden Assets" is on). The recover button drops
        # the asset's entry from the prefs JSON so it re-appears normally
        # on subsequent openings.
        if item.is_hidden:
            action_btn = QtWidgets.QPushButton()
            action_btn.setObjectName("recoverButton")
            action_btn.setToolTip(
                "Recover this asset — removes it from the hidden list in "
                "the prefs JSON so it appears normally again."
            )
            action_btn.setIcon(self._make_recover_icon())
            action_btn.clicked.connect(
                lambda _=False, it=item: self._recover_asset(it)
            )
        else:
            action_btn = QtWidgets.QPushButton()
            action_btn.setObjectName("hideButton")
            action_btn.setToolTip(
                "Hide this asset from the loader for the current shot.\n"
                "Tick 'Show Hidden Assets' to see and recover it later."
            )
            action_btn.setIcon(self._make_trash_icon())
            action_btn.clicked.connect(
                lambda _=False, it=item: self._hide_asset(it)
            )
        action_btn.setCursor(QtCore.Qt.PointingHandCursor)
        action_btn.setFixedSize(24, 22)
        action_btn.setIconSize(QtCore.QSize(14, 14))
        # Wrap the button in a centered container so the cell's leftover space
        # doesn't stretch the button.
        cell = QtWidgets.QWidget()
        cell_layout = QtWidgets.QHBoxLayout(cell)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setAlignment(QtCore.Qt.AlignCenter)
        cell_layout.addWidget(action_btn)
        self.table.setCellWidget(row, 5, cell)

    def _get_selected_items(self):
        """Return asset items for the rows currently highlighted in the table.
        Hidden rows (filtered out) are excluded even if still in the selection model."""
        sm = self.table.selectionModel()
        if sm is None:
            return []
        selected = []
        for index in sm.selectedRows():
            row = index.row()
            if self.table.isRowHidden(row):
                continue
            if 0 <= row < len(self.asset_items):
                selected.append(self.asset_items[row])
        return selected

    def _on_version_changed(self, row, version):
        """Handle version change. Updates the asset's selected_version and
        re-evaluates its Status against the loaded version so the user sees
        immediately whether applying it would be an update, a rollback, or
        a no-op."""
        if row >= len(self.asset_items):
            return
        item = self.asset_items[row]
        item.selected_version = version
        self._refresh_status_for_selection(item)
        status_item = self.table.item(row, 4)
        if status_item:
            status_item.setText(item.status_text)
            if item.status_color:
                status_item.setBackground(QtGui.QColor(item.status_color))
            else:
                status_item.setBackground(QtGui.QBrush())

    def _refresh_status_for_selection(self, item):
        """Recompute Status text/color from the currently selected dropdown
        version vs the version actually loaded in the scene.

        - selected < loaded → purple "Rollback" (warns the user that clicking
          Update on this row will downgrade the node)
        - selected > loaded → orange "Update"
        - selected == loaded → green "Up to date"
        - not loaded → leave the existing "Not loaded" status untouched

        Also rewrites update_target_version so that "Update Selected" applies
        exactly what the dropdown shows, not the auto-picked latest."""
        if not item.loaded_node or not item.loaded_version:
            return
        # Don't mask the duplicate warning when the user fiddles the version
        # dropdown — the scene state is the actual problem, not the version.
        if item.has_duplicates:
            return

        selected_int = version_int(item.selected_version)
        loaded_int = version_int(item.loaded_version)

        item.update_target_version = item.selected_version

        if selected_int < loaded_int:
            item.has_update = True
            item.status_text = f"Rollback: {item.loaded_version} → {item.selected_version}"
            item.status_color = "#8844cc"  # Purple — going backwards
        elif selected_int > loaded_int:
            item.has_update = True
            item.status_text = f"Update: {item.loaded_version} → {item.selected_version}"
            item.status_color = "#cc8844"  # Orange — moving forward
        else:
            item.has_update = False
            item.status_text = f"Up to date ({item.loaded_version})"
            item.status_color = "#3a5a3a"  # Green

    def _on_colorspace_changed(self, row, colorspace):
        """Handle colorspace change."""
        if row < len(self.asset_items):
            self.asset_items[row].selected_colorspace = colorspace
            print(f"[ShotAssetLoader] Set colorspace for {self.asset_items[row].asset_name} to {colorspace}")

    def _select_all(self):
        """Select all visible asset rows (rows hidden by the active filter are skipped)."""
        sm = self.table.selectionModel()
        if sm is None:
            return
        model = self.table.model()
        last_col = self.table.columnCount() - 1
        selection = QtCore.QItemSelection()
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            selection.select(model.index(row, 0), model.index(row, last_col))
        sm.select(
            selection,
            QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows,
        )

    def _deselect_all(self):
        """Clear the table selection."""
        self.table.clearSelection()

    def _on_column_resized(self, logical_index, _old_size, _new_size):
        """Force in-cell widgets (QComboBox, QLineEdit) to follow the live
        column drag. Without this, embedded widgets stay at their previous
        geometry until the user releases the mouse.

        Resizing column N also shifts every column to its right, so widgets
        from `logical_index` to the last column all need their geometry
        refreshed — not just the one being dragged."""
        model = self.table.model()
        if model is None:
            return
        row_count = self.table.rowCount()
        col_count = self.table.columnCount()
        for col in range(logical_index, col_count):
            for row in range(row_count):
                widget = self.table.cellWidget(row, col)
                if widget is None:
                    continue
                widget.setGeometry(self.table.visualRect(model.index(row, col)))

    def _apply_source_filter(self, source):
        """Filter table rows by source type. 'All' shows everything, 'Loaded' shows
        only assets currently present in the Nuke scene."""
        # Update button states: only the active filter is checked
        for s, btn in self.filter_buttons.items():
            btn.setChecked(s == source)

        # Refresh loaded state before applying the "Loaded" filter so newly
        # loaded / removed nodes are reflected immediately.
        if source == "Loaded":
            self._do_check_for_updates(silent=True)

        for row, item in enumerate(self.asset_items):
            if source == "All":
                self.table.setRowHidden(row, False)
                continue

            if source == "Loaded":
                matches_filter = item.loaded_node is not None
            elif source == "From Other Shots":
                matches_filter = item.is_foreign
            else:
                matches_filter = (item.source_type == source)

            self.table.setRowHidden(row, not matches_filter)

        # Drop hidden rows from the current selection so "Load Selected" /
        # "Update Selected" only act on what the user can actually see.
        sm = self.table.selectionModel()
        if sm is not None:
            for index in list(sm.selectedRows()):
                if self.table.isRowHidden(index.row()):
                    sm.select(
                        index,
                        QtCore.QItemSelectionModel.Deselect | QtCore.QItemSelectionModel.Rows,
                    )

    def _load_selected_assets(self):
        """Load assets whose rows are currently selected (highlighted) in the table."""
        selected = self._get_selected_items()

        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets selected")
            return

        self._load_assets(selected)

    def _load_all_assets(self):
        """Load all assets."""
        if not self.asset_items:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets to load")
            return

        self._load_assets(self.asset_items)

    def _load_assets(self, items):
        """Load asset items."""
        # Refresh the loaded state so duplicate-import detection is accurate
        # even if the user changed the scene since the last check.
        self._do_check_for_updates(silent=True)

        already_loaded = [it for it in items if it.loaded_node is not None]
        to_load = [it for it in items if it.loaded_node is None]

        if not to_load:
            names = ", ".join(f"{it.asset_type} '{it.asset_name}'" for it in already_loaded[:5])
            more = f" (+{len(already_loaded) - 5} more)" if len(already_loaded) > 5 else ""
            QtWidgets.QMessageBox.information(
                self,
                "Nothing to Load",
                f"All {len(items)} selected asset(s) are already in the script:\n{names}{more}"
            )
            return

        items = to_load

        # Build filtered assets dict
        filtered_assets = {
            "plates": {},
            "3d_renders": {},
            "2d_renders": {},
            "rotos": {},
            "cameras": {}
        }

        # Build colorspaces dict (maps asset_name to colorspace)
        asset_colorspaces = {}

        for item in items:
            # Store colorspace for this asset (only if not "Auto")
            colorspace_key = f"{item.asset_type}_{item.asset_name}"
            if item.selected_colorspace and item.selected_colorspace != "Auto":
                asset_colorspaces[colorspace_key] = item.selected_colorspace

            if item.asset_type == "Plate":
                filtered_assets["plates"][item.asset_name] = {
                    item.selected_version: item.versions_dict[item.selected_version]
                }
            elif item.asset_type == "3D Render":
                filtered_assets["3d_renders"][item.asset_name] = {
                    item.selected_version: item.versions_dict[item.selected_version]
                }
            elif item.asset_type == "2D Render":
                filtered_assets["2d_renders"][item.asset_name] = {
                    item.selected_version: item.versions_dict[item.selected_version]
                }
            elif item.asset_type == "Roto":
                filtered_assets["rotos"][item.selected_version] = item.versions_dict[item.selected_version]
            elif item.asset_type == "Camera":
                filtered_assets["cameras"][item.asset_name] = {
                    item.selected_version: item.versions_dict[item.selected_version]
                }

        # Load
        try:
            self.node_builder.load_assets(
                sequence=self.current_sequence,
                shot=self.current_shot,
                assets=filtered_assets,
                asset_colorspaces=asset_colorspaces,
                project_root=self._project_root,
            )

            # Re-câble les PostageStamp existants (par titre) pour qu'ils
            # pointent sur les nouveaux Anchors qu'on vient de créer. Silent
            # car le popup de succès ci-dessous tient lieu de feedback;
            # le rapport détaillé reste imprimé dans la console.
            try:
                run_reconnect_on_postage_stamps(silent=True)
            except Exception as e:
                print(f"[ShotAssetLoader] reconnect_stamps failed (non-fatal): {e}")

            # Resolve the freshly-created Read/Camera nodes back onto their
            # asset items and push the status (tile_color + label suffix) onto
            # them — without this pass, a first load lands with default-colored
            # tiles until the user manually hits "Check for Updates".
            self._do_check_for_updates(silent=True)

            msg = (
                f"Successfully loaded {len(self.node_builder.created_nodes)} node(s) "
                f"for {self.current_sequence}/{self.current_shot}"
            )
            if already_loaded:
                msg += f"\n\nSkipped {len(already_loaded)} already-loaded asset(s)."
            QtWidgets.QMessageBox.information(self, "Success", msg)

            # Record a package snapshot after a successful load — this is one
            # of the user-triggered moments where "the compo state changed"
            # and traceability matters.
            self._save_package_snapshot()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error loading assets:\n{e}")
            print(f"[ShotAssetLoader] Error: {e}")
            import traceback
            traceback.print_exc()

    def _check_for_updates(self):
        """Check for updates on loaded nodes (manual refresh). Drops the
        frame-set cache so we re-scan disk, re-scans the shot folder so any
        newly-rendered assets show up without restarting the dialog, then
        surfaces a summary popup."""
        self._frame_set_cache.clear()
        # Re-discover assets from disk — picks up versions/passes added since
        # the dialog was opened. _populate_table() rebuilds the table rows.
        self._scan_shot_assets()
        self._do_check_for_updates(silent=False)

    def _do_check_for_updates(self, silent=False):
        """Check for updates on loaded nodes. If silent, only updates the status column (no popups)."""
        if not self.current_sequence or not self.current_shot:
            if not silent:
                QtWidgets.QMessageBox.warning(self, "Warning", "Please scan a shot first")
            return

        if not self.asset_items:
            if not silent:
                QtWidgets.QMessageBox.warning(self, "Warning", "No assets to check")
            return

        # Scan all nodes in scene
        all_nodes = nuke.allNodes()
        read_nodes = [n for n in all_nodes if n.Class() == "Read"]
        camera_nodes = [n for n in all_nodes if n.Class() == "Camera3"]

        # Pre-filter Reads once (loader-owned + current shot/sequence) so
        # _find_node_for_asset doesn't re-check `_is_loader_owned` and re-read
        # the `file` knob for every (asset × Read) pair. Knob reads are the
        # main cost in the per-asset loop on heavy scenes.
        loader_reads = []
        for r in read_nodes:
            if not self._is_loader_owned(r):
                continue
            if 'file' not in r.knobs():
                continue
            fp = (r['file'].value() or "").replace('\\', '/')
            if not fp:
                continue
            if self.current_sequence not in fp or self.current_shot not in fp:
                continue
            loader_reads.append((r, fp, fp.lower()))

        # Scene frame range — used to grade updates as full vs partial coverage.
        try:
            scene_range = (
                int(nuke.root()['first_frame'].value()),
                int(nuke.root()['last_frame'].value()),
            )
        except Exception:
            scene_range = None

        updates_found = 0

        # Check each asset item
        for row, item in enumerate(self.asset_items):
            # Foreign-shot items are pre-bound to a specific Read at populate
            # time. Skip the path-needle match (its current-shot filter would
            # reject them anyway) and just validate the node still exists,
            # then re-evaluate the update target against the foreign versions.
            if item.is_foreign:
                if item.loaded_node in read_nodes:
                    file_path = ""
                    if 'file' in item.loaded_node.knobs():
                        file_path = item.loaded_node['file'].value() or ""
                    extracted = extract_version_from_path(file_path)
                    if extracted:
                        item.loaded_version = extracted
                        if self._apply_update_target_status(item, scene_range):
                            updates_found += 1
                    else:
                        item.update_target_version = None
                        item.status_text = "Version not found in path"
                        item.status_color = None
                else:
                    item.loaded_node = None
                    item.loaded_version = None
                    item.has_update = False
                    item.status_text = "Not loaded (removed from scene)"
                    item.status_color = None
                continue

            # Try to find corresponding node in scene
            node, has_duplicates = self._find_node_for_asset(item, loader_reads, camera_nodes)
            item.has_duplicates = has_duplicates

            if node:
                # Node found in scene
                item.loaded_node = node

                # Extract version from node's file path
                file_path = None
                if 'file' in node.knobs():
                    file_path = node['file'].value()

                # Camera present in scene with no file assigned → treat as v000
                # so the user gets a clear "update available" status rather than
                # the generic "File path not found" message.
                if item.asset_type == "Camera" and not file_path:
                    item.loaded_version = "v000"
                    if self._apply_update_target_status(item, scene_range):
                        updates_found += 1
                    continue

                if file_path:
                    extracted = extract_version_from_path(file_path)
                    if extracted:
                        item.loaded_version = extracted
                        if self._apply_update_target_status(item, scene_range):
                            updates_found += 1
                    else:
                        item.update_target_version = None
                        item.status_text = "Version not found in path"
                        item.status_color = None
                else:
                    item.update_target_version = None
                    item.status_text = "File path not found"
                    item.status_color = None
            else:
                # Node not found in scene
                item.loaded_node = None
                item.loaded_version = None
                item.has_update = False
                item.status_text = "Not loaded"
                item.status_color = None

        # Surface the duplicate condition on top of whatever status the loop
        # above set. Second pass so the camera early-`continue` can't bypass
        # it; cameras never carry has_duplicates anyway.
        # We also clear `has_update` so the Update buttons skip duplicated
        # assets — updating one copy while the other stays stale would only
        # deepen the confusion. The user has to clean the scene first.
        for item in self.asset_items:
            if item.has_duplicates:
                item.has_update = False
                item.update_target_version = None
                item.status_text = "Duplicate detected — clean up extras"
                item.status_color = "#aa2c2c"

        # Drop foreign-shot rows whose Read disappeared from the scene — they
        # were only listed because they were loaded; once removed they have
        # no business in the table (unlike local items, which stay listed as
        # available assets to load). Reverse iteration keeps indices valid.
        for row in range(len(self.asset_items) - 1, -1, -1):
            item = self.asset_items[row]
            if item.is_foreign and item.loaded_node is None:
                self.asset_items.pop(row)
                self.table.removeRow(row)

        # The "From Other Shots" pill may need to disappear if we just pruned
        # the last foreign item.
        self._refresh_filter_visibility()

        # Refresh table display
        self._refresh_table_status()

        # Mirror the freshly-computed state onto the Read/Camera nodes (label
        # suffix + tile_color) so the node graph shows the same cue as the UI.
        self._apply_status_to_loaded_nodes()

        # Force a reload on every loaded Read so Nuke drops any cached frame
        # set and picks up whatever is currently on disk (farm renders that
        # landed while the dialog was open, etc.).
        self._reload_all_loaded_reads()

        # Show message (only when not silent)
        if silent:
            print(f"[ShotAssetLoader] Silent check complete: {updates_found} update(s) available")
            return

        if updates_found > 0:
            QtWidgets.QMessageBox.information(
                self,
                "Updates Available",
                f"Found {updates_found} asset(s) with updates available"
            )
        else:
            QtWidgets.QMessageBox.information(
                self,
                "All Up to Date",
                "All loaded assets are up to date"
            )

    def _default_to_latest_full(self, item, scene_range):
        """Pick the highest *full-coverage* version as the dropdown default,
        so the first load doesn't silently land on a partial when one happens
        to exist above the latest full. Falls back to the highest version when
        no full version exists (same fallback as `_pick_update_target`)."""
        target, _ = self._pick_update_target(item, scene_range)
        if target:
            item.selected_version = target

    def _apply_update_target_status(self, item, scene_range):
        """
        Pick the best update target for `item` (full-priority), then set
        item.update_target_version / has_update / status_text / status_color.

        Returns True if an update was flagged, False otherwise.
        """
        target, is_full = self._pick_update_target(item, scene_range)
        item.update_target_version = target

        target_int = version_int(target)
        loaded_int = version_int(item.loaded_version)

        if target and target_int > loaded_int:
            item.has_update = True
            if is_full:
                item.status_text = f"Update: {item.loaded_version} → {target} (full)"
                item.status_color = "#4477cc"  # Blue — full update ready
            else:
                missing = self._count_missing_frames(item, target, scene_range)
                miss_text = f"{missing} frames missing" if missing else "frames missing"
                item.status_text = (
                    f"Update: {item.loaded_version} → {target} ({miss_text})"
                )
                item.status_color = "#cc8844"  # Orange — incomplete coverage
            return True

        # Up to date relative to the best full target. If a higher version
        # exists but is incomplete on disk, surface it as an orange update —
        # the user can still choose to apply it.
        higher_partial = None
        if is_full and item.versions:
            highest = max(item.versions, key=version_int)
            if version_int(highest) > loaded_int:
                higher_partial = highest

        if higher_partial:
            item.has_update = True
            item.update_target_version = higher_partial
            missing = self._count_missing_frames(item, higher_partial, scene_range)
            miss_text = f"{missing} frames missing" if missing else "frames missing"
            item.status_text = (
                f"Update: {item.loaded_version} → {higher_partial} ({miss_text})"
            )
            item.status_color = "#cc8844"  # Orange — incomplete coverage
            return True

        item.has_update = False
        # The latest is loaded but may still be incomplete on disk. Use a
        # darker green so the artist can tell apart "fully done" from "no
        # newer version exists but this one is missing frames".
        loaded_missing = self._count_missing_frames(item, item.loaded_version, scene_range)
        if loaded_missing:
            item.status_text = (
                f"Up to date ({item.loaded_version}, {loaded_missing} frames missing)"
            )
            item.status_color = "#1e3a1e"  # Darker green — latest but incomplete
        else:
            item.status_text = f"Up to date ({item.loaded_version})"
            item.status_color = "#3a5a3a"  # Green
        return False

    def _count_missing_frames(self, item, version, scene_range):
        """Number of frames in `scene_range` absent from disk for this version.

        Returns 0 when complete (or when the asset isn't per-frame, e.g. a
        Camera), or when there's no scene_range to compare against. Returns
        None only when the version data itself is missing/unreadable —
        callers treat that the same as 0 since there's nothing to report.

        Reuses `_frame_set_cache` so back-to-back calls (status check + Read
        node label sync) don't double-scan disk."""
        if not version:
            return 0
        if item.asset_type == "Camera":
            return 0
        if not scene_range:
            return 0
        version_data = item.versions_dict.get(version)
        if not version_data:
            return None
        if isinstance(version_data, dict):
            folder_path = next(iter(version_data.values()))
        else:
            folder_path = version_data
        if folder_path in self._frame_set_cache:
            frames = self._frame_set_cache[folder_path]
        else:
            frames = self.discoverer.get_frame_numbers_from_files(folder_path)
            self._frame_set_cache[folder_path] = frames
        if not frames:
            return None
        expected = range(scene_range[0], scene_range[1] + 1)
        return sum(1 for f in expected if f not in frames)

    def _pick_update_target(self, item, scene_range):
        """
        Pick the best update target for an asset.

        Full-coverage versions take priority: the highest fully-covering version
        wins over any higher partial version (e.g. full v016 wins over partial
        v017). If no version covers the scene range, fall back to the highest
        version overall (which will be flagged as partial).

        Walks versions from highest to lowest and returns the first full match
        — saves N-1 directory scans per asset in the common case where the
        latest version is full (the main cause of "Loaded" filter slowness).

        Returns:
            (version_str, is_full) or (None, False) if no versions exist.
        """
        if not item.versions:
            return None, False

        # Cameras aren't per-frame sequences — "full" always applies.
        if item.asset_type == "Camera":
            return max(item.versions, key=version_int), True

        sorted_desc = sorted(item.versions, key=version_int, reverse=True)
        for v in sorted_desc:
            if self._latest_version_covers_scene_range(item, v, scene_range):
                return v, True

        # No version covers the scene — flag the highest as partial.
        return sorted_desc[0], False

    def _latest_version_covers_scene_range(self, item, latest_version, scene_range):
        """
        Return True only if *every* frame in the scene range exists on disk
        for this version. Checking just the (first, last) endpoints would let
        FML preview renders (first/middle/last) pass for full coverage even
        though all the in-between frames are missing.

        Cameras (USD) are treated as always-complete because they aren't
        per-frame sequences.
        """
        if item.asset_type == "Camera":
            return True
        if not scene_range:
            # If we couldn't read the scene range, fail open as "full" so the
            # status falls back to the simple "update available" semantics.
            return True

        try:
            version_data = item.versions_dict.get(latest_version)
            if not version_data:
                return False

            if isinstance(version_data, dict):
                folder_path = next(iter(version_data.values()))
            else:
                folder_path = version_data

            if folder_path in self._frame_set_cache:
                frames = self._frame_set_cache[folder_path]
            else:
                frames = self.discoverer.get_frame_numbers_from_files(folder_path)
                self._frame_set_cache[folder_path] = frames

            if not frames:
                # No frame-numbered images found. Could be a static-image
                # asset (paintover .psd, stMap.png, ...) — those have no
                # per-frame coverage to check, so treat them as full when
                # there's at least one image file present. Otherwise the
                # folder is empty/unreadable and we fall back to False.
                return self.discoverer.folder_has_image(folder_path)

            return frames.issuperset(range(scene_range[0], scene_range[1] + 1))
        except Exception as e:
            print(f"[ShotAssetLoader] Frame coverage check failed for {item.asset_name}: {e}")
            return False

    # Trailing "_N" / "N" pattern Nuke appends when the artist Ctrl+C/Ctrl+V's
    # a loader Read. Precompiled here so the duplicate-tiebreaker doesn't
    # recompile it on every `_find_node_for_asset` call.
    _COPY_SUFFIX_RE = re.compile(r'_?\d+$')

    def _find_node_for_asset(self, item, loader_reads, camera_nodes):
        """Find the Nuke node corresponding to an asset item.

        Args:
            loader_reads: list of (read_node, file_path, file_path_lower)
                tuples pre-filtered by the caller — loader-owned Reads whose
                file path already matches the current sequence/shot. The
                caller does this once per check to save re-reading `file`
                knobs for every asset × Read pair.
            camera_nodes: raw list of Camera3 nodes from `nuke.allNodes()`.

        Returns:
            (node, has_duplicates):
                node: the matched Nuke node, or None if nothing matches.
                has_duplicates: True only for Reads when, after applying the
                    name-suffix tiebreaker, more than one candidate remains —
                    the caller should surface this as a "duplicate" status.

        Cameras are still resolved from the raw camera_nodes list — a shot
        typically has one Camera3, so pre-filtering isn't worth it there.
        When several Reads match the same asset, we prefer the candidate
        whose name has no trailing-digit suffix (the original load). If
        that still leaves multiple, we pick the highest version and flag
        the duplicate.
        """
        # Cameras: a shot generally has one camera, so first try the project
        # convention — a Camera3 named "CAM_SHOT". Fall back to file-knob
        # matching for renamed / non-canonical setups.
        if item.asset_type == "Camera":
            for cam_node in camera_nodes:
                if cam_node.name().upper() == "CAM_SHOT":
                    return cam_node, False

            for cam_node in camera_nodes:
                if 'file' not in cam_node.knobs():
                    continue
                file_path = (cam_node['file'].value() or "").replace('\\', '/')
                if self.current_sequence in file_path and self.current_shot in file_path:
                    if f"/{item.asset_name}/" in file_path:
                        return cam_node, False
            return None, False

        # Reads: asset_name is "plate"/"3D pass"/"2D pass"/"roto" → always
        # appears as a path component between slashes in the Prism layout.
        # The caller already dropped Reads that don't belong to this shot,
        # so we only need to match the name needle against the (cached)
        # lowercased path.
        needle_lower = f"/{item.asset_name.lower()}/"
        candidates = [
            (r, fp) for r, fp, fp_lower in loader_reads
            if needle_lower in fp_lower
        ]

        if not candidates:
            return None, False

        if len(candidates) == 1:
            return candidates[0][0], False

        # Multiple candidates — duplicate suspicion. Nuke renames copies by
        # appending an incrementing number (usually just digits, sometimes
        # `_N`), so the un-suffixed name is the original load.
        unsuffixed = [c for c in candidates if not self._COPY_SUFFIX_RE.search(c[0].name())]

        if len(unsuffixed) == 1:
            return unsuffixed[0][0], False

        # Still ambiguous: either zero or several un-suffixed candidates.
        # Pick the highest-version one and flag the duplicate so the table
        # row turns red and the user can clean up.
        pool = unsuffixed if unsuffixed else candidates
        pool.sort(
            key=lambda c: version_int(extract_version_from_path(c[1])),
            reverse=True,
        )
        names = ", ".join(c[0].name() for c in pool)
        print(
            f"[ShotAssetLoader] WARNING: duplicate loader Reads detected for "
            f"{item.asset_type} '{item.asset_name}': {names}"
        )
        return pool[0][0], True

    # Matches the Prism layout /<root>/03_Production/Shots/<SQ>/<SH>/Renders/
    # <bucket>/<asset_name>/v###/... . `bucket` is restricted to the known
    # asset families so unrelated paths (Comp output, etc.) are ignored.
    _FOREIGN_PATH_RE = re.compile(
        r'/[Ss]hots/([^/]+)/([^/]+)/Renders/(external|3dRender|2dRender)/([^/]+)/v\d{3,4}',
        re.IGNORECASE,
    )

    def _parse_foreign_asset_info(self, file_path):
        """Parse a Read's file path into shot-context + asset info. Returns a
        dict with seq/shot/asset_type/asset_name/source_type, or None if the
        path doesn't sit under the expected Prism Shots layout.
        """
        if not file_path:
            return None
        norm = file_path.replace('\\', '/')
        m = self._FOREIGN_PATH_RE.search(norm)
        if not m:
            return None

        seq, shot, bucket, asset_name = m.group(1), m.group(2), m.group(3), m.group(4)
        bucket_lower = bucket.lower()

        if bucket_lower == "external":
            # Roto folders sit under external/roto/v### — distinguish them
            # so the table shows the right Type pill.
            if asset_name.lower() == "roto":
                asset_type = "Roto"
            else:
                asset_type = "Plate"
            source_type = "external"
        elif bucket_lower == "3drender":
            asset_type = "3D Render"
            source_type = "3dRender"
        elif bucket_lower == "2drender":
            asset_type = "2D Render"
            source_type = "2dRender"
        else:
            return None

        return {
            "sequence": seq,
            "shot": shot,
            "asset_type": asset_type,
            "asset_name": asset_name,
            "source_type": source_type,
        }

    def _discover_foreign_assets(self):
        """Scan the Nuke scene for loader-owned Reads pointing at assets that
        live under a different SQ/SH than the current context. Returns a list
        of AssetItem instances with loaded_node already bound. Available
        versions are fetched from the foreign shot's filesystem so the
        update-check flow works the same way as for local assets.
        """
        if not self.current_sequence or not self.current_shot:
            return []

        # Dedup key: (seq, shot, asset_type, asset_name) — multi-layer Reads
        # sharing the same asset are represented by a single AssetItem (the
        # first one we encounter wins for the loaded_node binding).
        #
        # We intentionally bypass the `fromShotLoader` and name-suffix
        # filters here: foreign-shot Reads are typically brought in manually
        # by the artist (drag-dropped from another shot), so they don't
        # carry the loader's marker knob. The Prism-layout path regex is
        # strict enough on its own to keep unrelated Reads out.
        seen = {}
        for read_node in nuke.allNodes("Read"):
            if 'file' not in read_node.knobs():
                continue
            file_path = (read_node['file'].value() or "").replace('\\', '/')
            if not file_path:
                continue

            info = self._parse_foreign_asset_info(file_path)
            if not info:
                continue
            if info["sequence"] == self.current_sequence and info["shot"] == self.current_shot:
                continue  # Local — handled by the normal discovery flow.

            key = (info["sequence"], info["shot"], info["asset_type"], info["asset_name"])
            if key in seen:
                continue
            seen[key] = (read_node, info)

        if not seen:
            return []

        # Fetch the versions folder once per unique foreign asset. We bypass
        # the full discover_all_assets() — only the one asset path is needed.
        items = []
        for (seq, shot, asset_type, asset_name), (read_node, info) in seen.items():
            asset_path = self._build_foreign_asset_path(seq, shot, asset_type, asset_name)
            if not asset_path or not os.path.isdir(asset_path):
                print(
                    f"[ShotAssetLoader] Foreign asset path missing — skipping: {asset_path}"
                )
                continue

            try:
                versions_dict = self.discoverer._discover_versions_with_layers(asset_path)
            except Exception as e:
                print(f"[ShotAssetLoader] Foreign version scan failed for {asset_path}: {e}")
                continue

            if not versions_dict:
                print(f"[ShotAssetLoader] No versions found for foreign asset {asset_path}")
                continue

            versions = sorted(versions_dict.keys())

            item = AssetItem(
                asset_type,
                asset_name,
                versions,
                versions_dict,
                source_type=info["source_type"],
            )
            item.is_foreign = True
            item.foreign_sequence = seq
            item.foreign_shot = shot
            item.loaded_node = read_node
            # The update-target/status will be filled in by _do_check_for_updates.
            items.append(item)
            print(
                f"[ShotAssetLoader] Foreign {asset_type} '{asset_name}' from {seq}/{shot} "
                f"({len(versions)} version(s))"
            )

        return items

    def _build_foreign_asset_path(self, seq, shot, asset_type, asset_name):
        """Reconstruct the on-disk asset folder for a foreign Read. Mirrors the
        layout used by AssetDiscoverer (so the same _discover_versions_with_layers
        helper can scan it)."""
        if asset_type == "Plate":
            bucket = Config.PLATES_PATH
            tail = asset_name
        elif asset_type == "Roto":
            bucket = Config.PLATES_PATH
            tail = "roto"
        elif asset_type == "3D Render":
            bucket = Config.RENDERS_3D_PATH
            tail = asset_name
        elif asset_type == "2D Render":
            bucket = Config.RENDERS_2D_PATH
            tail = asset_name
        else:
            return None

        return os.path.join(
            self._project_root,
            Config.SHOTS_PATH,
            seq,
            shot,
            bucket,
            tail,
        )

    def _is_loader_owned(self, node):
        """Return True if the node carries the `fromShotLoader` checkbox at
        True — the marker set by NukeNodeBuilder on every Read it creates."""
        try:
            knob = node.knob('fromShotLoader')
            return knob is not None and bool(knob.value())
        except Exception:
            return False

    def _refresh_table_status(self):
        """Refresh status column in table."""
        for row, item in enumerate(self.asset_items):
            status_item = self.table.item(row, 4)
            if status_item:
                status_item.setText(item.status_text)
                if item.status_color:
                    status_item.setBackground(QtGui.QColor(item.status_color))
                else:
                    # Empty brush → cell inherits the alternating row color
                    status_item.setBackground(QtGui.QBrush())

    # Marker prefix written on the status line of a Read/Camera label so the
    # next sync can find and replace it without trampling user-authored lines
    # or the version_tcl expression set by NukeNodeBuilder at load time.
    _NODE_STATUS_MARKER = "»"

    # tile_color is a packed 0xRRGGBBAA int in Nuke. Mirrors the table status
    # palette so the node-graph cue and the dialog stay visually consistent.
    _NODE_STATUS_VISUALS = {
        "up_to_date":         ("up to date",                  0x3a5a3aff),  # Green
        "up_to_date_missing": ("up to date (frames missing)", 0x1e3a1eff),  # Darker green
        "to_update":          ("to update",                   0x4477ccff),  # Blue
        "to_update_missing":  ("to update (frames missing)",  0xcc8844ff),  # Orange
    }

    def _apply_status_to_loaded_nodes(self):
        """Push the current update state onto every loaded Nuke node so the
        artist sees it directly in the node graph (no need to open the loader).

        Re-runs at every check; only the line prefixed with `_NODE_STATUS_MARKER`
        is rewritten — any other label content (asset name, version_tcl, the
        artist's own notes) is left intact."""
        for item in self.asset_items:
            node = item.loaded_node
            if not node:
                continue
            # Duplicates already get the loud red row in the UI; leave their
            # node labels untouched so the artist isn't tempted to read them
            # as definitive while there's still cleanup to do.
            if item.has_duplicates:
                continue

            status_key = self._node_status_key(item)
            visual = self._NODE_STATUS_VISUALS.get(status_key)
            if not visual:
                continue
            text, tile_color = visual

            try:
                if 'tile_color' in node.knobs():
                    node['tile_color'].setValue(tile_color)
            except Exception as e:
                print(f"[ShotAssetLoader] tile_color sync failed for {node.name()}: {e}")

            try:
                if 'label' in node.knobs():
                    current = node['label'].value() or ""
                    lines = [
                        ln for ln in current.split('\n')
                        if not ln.startswith(self._NODE_STATUS_MARKER)
                    ]
                    lines.append(f"{self._NODE_STATUS_MARKER} {text}")
                    node['label'].setValue('\n'.join(lines))
            except Exception as e:
                print(f"[ShotAssetLoader] label sync failed for {node.name()}: {e}")

    def _reload_read(self, node):
        """Kick a Read's frame cache via its `reload` knob. No-op for non-Read
        nodes (Camera3 has no such knob)."""
        if not node or node.Class() != "Read":
            return
        if 'reload' not in node.knobs():
            return
        try:
            node['reload'].execute()
        except Exception as e:
            print(f"[ShotAssetLoader] reload knob failed for {node.name()}: {e}")

    def _reload_all_loaded_reads(self):
        """Reload every Read bound to an asset item. _reload_read is a no-op
        for non-Read nodes (Camera3) so we don't need to filter by type here."""
        for item in self.asset_items:
            if item.loaded_node:
                self._reload_read(item.loaded_node)

    def _node_status_key(self, item):
        """Map an item's current state to one of `_NODE_STATUS_VISUALS` keys,
        or None if the node shouldn't carry a status marker (e.g. rollback,
        unparseable version)."""
        has_missing = "frames missing" in item.status_text
        if item.has_update:
            return "to_update_missing" if has_missing else "to_update"
        # Only confirm up-to-date when we actually managed to read the loaded
        # version — otherwise the green tile would be misleading.
        if item.loaded_version:
            return "up_to_date_missing" if has_missing else "up_to_date"
        return None

    def _update_selected_assets(self):
        """Update assets whose rows are currently selected (highlighted) in the table."""
        selected = self._get_selected_items()

        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets selected")
            return

        self._perform_updates(selected, scope_label="selected")

    def _update_all_loaded_assets(self):
        """Update every loaded asset in the scene to its latest version."""
        if not self.asset_items:
            QtWidgets.QMessageBox.warning(self, "Warning", "No assets to update")
            return

        # Refresh has_update / loaded_node state silently so the action is based on fresh info
        self._do_check_for_updates(silent=True)

        self._perform_updates(self.asset_items, scope_label="loaded")

    def _perform_updates(self, items, scope_label="selected", confirm_message=None, save_snapshot=True):
        """Shared update logic: keeps only items with available updates that are loaded, confirms, then applies.

        `confirm_message` overrides the default confirmation text — used by
        Choose Package so the dialog says "Apply PKG_v003 to N asset(s)?"
        instead of the generic "Update to latest version?".

        `save_snapshot` disables the automatic PKG_v### save at the end of a
        successful update. Choose Package sets this to False since the artist
        is deliberately time-travelling to an existing package and creating a
        new snapshot on top of it would be confusing.

        Returns True if updates were actually applied, False when the user
        cancelled the confirm dialog or there was nothing to update. The
        return is consumed by Choose Package so it only pins current_package
        when the operation went through."""
        updateable = [item for item in items if item.has_update and item.loaded_node]

        if not updateable:
            QtWidgets.QMessageBox.information(
                self,
                "No Updates",
                f"No {scope_label} assets have updates available"
            )
            return False

        # Confirm update
        if confirm_message is None:
            confirm_message = f"Update {len(updateable)} asset(s) to latest version?"
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Update",
            confirm_message,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return False

        # Perform updates
        updated_count = 0
        failed_updates = []

        for item in updateable:
            try:
                # Use the target picked at check-time (full-priority), so a full
                # v016 wins over a partial v017 even though v017 is "latest".
                target_version = item.update_target_version or item.versions[-1]
                version_data = item.versions_dict[target_version]

                # Get first layer's path (for multi-layer assets)
                if isinstance(version_data, dict):
                    new_version_path = list(version_data.values())[0]
                else:
                    new_version_path = version_data

                # Get frame range from the Nuke scene. For foreign-shot items
                # we leave the Read's existing first/last untouched — the artist
                # likely retimed it for the current comp and the scene's range
                # is irrelevant.
                if item.is_foreign:
                    frame_range = None
                else:
                    try:
                        frame_range = (
                            int(nuke.root()['first_frame'].value()),
                            int(nuke.root()['last_frame'].value()),
                        )
                    except Exception:
                        frame_range = None

                # Update node
                success = self.node_builder.update_node_version(
                    item.loaded_node,
                    new_version_path,
                    frame_range
                )

                if success:
                    updated_count += 1
                    # Update item status
                    item.loaded_version = target_version
                    item.has_update = False
                    item.update_target_version = target_version
                    item.status_text = f"Up to date ({target_version})"
                    item.status_color = "#3a5a3a"  # Green

                    # Defensive reload: kick the Read's cache so Nuke shows the
                    # frames just written to disk rather than anything it may
                    # have cached from the previous version's path.
                    self._reload_read(item.loaded_node)
                else:
                    failed_updates.append(f"{item.asset_type} - {item.asset_name}")

            except Exception as e:
                failed_updates.append(f"{item.asset_type} - {item.asset_name}: {e}")
                print(f"[ShotAssetLoader] Error updating {item.asset_name}: {e}")

        # Re-check all statuses from the actual scene state so the table
        # reflects the freshly-loaded versions (and any newly-available
        # partials behind them) instead of stale per-item assumptions.
        self._do_check_for_updates(silent=True)

        # Show result
        message = f"Successfully updated {updated_count} asset(s)"
        if failed_updates:
            message += f"\n\nFailed to update {len(failed_updates)} asset(s):\n"
            message += "\n".join(failed_updates[:5])  # Show first 5 failures
            if len(failed_updates) > 5:
                message += f"\n... and {len(failed_updates) - 5} more"

        QtWidgets.QMessageBox.information(self, "Update Complete", message)

        # Record a package snapshot after a successful update. Skipped when
        # the caller opted out (e.g. Choose Package, which is itself applying
        # a previously-saved snapshot).
        if save_snapshot and updated_count > 0:
            self._save_package_snapshot()

        return True

    def _show_context_menu(self, position):
        """
        Show context menu on right-click in the assets table.

        Args:
            position: Position where the context menu was requested
        """
        # Get the row at the clicked position
        row = self.table.rowAt(position.y())
        if row < 0 or row >= len(self.asset_items):
            return  # No valid row clicked

        # Get the asset item for this row
        item = self.asset_items[row]

        # Create context menu
        menu = QtWidgets.QMenu(self)

        # Add "Open in Explorer" action
        open_folder_action = menu.addAction("Open in Explorer")
        open_folder_action.triggered.connect(lambda: self._open_asset_folder(row))

        # Show the menu at the cursor position
        menu.exec_(self.table.viewport().mapToGlobal(position))

    def _open_asset_folder(self, row):
        """
        Open the asset folder in Windows Explorer.

        Args:
            row (int): Row index in the table
        """
        if row < 0 or row >= len(self.asset_items):
            return

        item = self.asset_items[row]

        try:
            # Extract the folder path based on asset type
            folder_path = None

            if item.selected_version and item.selected_version in item.versions_dict:
                version_data = item.versions_dict[item.selected_version]

                # For Plates, 3D Renders, Rotos: versions_dict[version] is a dict of layers
                # Each layer value is a folder path
                if isinstance(version_data, dict):
                    # Get the first layer path
                    if version_data:
                        first_layer_path = next(iter(version_data.values()))
                        folder_path = first_layer_path
                else:
                    # For Cameras: versions_dict[version] is directly the folder path
                    folder_path = version_data

            if not folder_path or not os.path.exists(folder_path):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Path Not Found",
                    f"Could not find folder for {item.asset_type}: {item.asset_name}\nVersion: {item.selected_version}"
                )
                return

            # Open in Windows Explorer
            # Normalize path for Windows
            folder_path = os.path.normpath(folder_path)

            # Use subprocess to open explorer at the folder location
            subprocess.Popen(['explorer', folder_path])

            print(f"[ShotAssetLoader] Opened folder in Explorer: {folder_path}")

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Failed to open folder in Explorer:\n{str(e)}"
            )
            print(f"[ShotAssetLoader] Error opening folder: {e}")
            import traceback
            traceback.print_exc()


def show_shot_asset_loader():
    """Show the Shot Asset Loader window."""
    try:
        # Get Nuke's main window as parent
        app = QtWidgets.QApplication.instance()
        parent = app.activeWindow()

        window = ShotAssetLoaderWindow(parent)
        window.show()
        window.raise_()
        window.activateWindow()

    except Exception as e:
        nuke.message(f"Error showing Shot Asset Loader: {e}")
        print(f"[ShotAssetLoader] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    show_shot_asset_loader()
