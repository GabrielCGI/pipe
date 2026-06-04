"""
UI Loader - Simplified Qt Window Version
Standalone Qt window for loading shot assets.
Compatible with both Nuke 15 (PySide2) and Nuke 16+ (PySide6).
"""

import nuke
import os
import re
import subprocess
import webbrowser
from .config import Config
from .asset_discoverer import AssetDiscoverer
from .nuke_node_builder import NukeNodeBuilder
from .version_utils import version_int, extract_version_from_path
from .reconnect_stamps import run_reconnect_on_postage_stamps

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

QLabel#headerBanner {
    padding: 14px 18px;
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
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

        # Camera-specific config (ignored for other asset types)
        self.node_name = ""
        self.prim_path = ""

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


class ShotAssetLoaderWindow(QtWidgets.QDialog):
    """Standalone Qt window for shot asset loading."""

    HELP_URL = "https://www.notion.so/illogic/Nuke-Shot-Loader-3679d24ae7e3804491f7ceade8e2a1e3"

    def __init__(self, parent=None):
        super(ShotAssetLoaderWindow, self).__init__(parent)

        self.setWindowTitle("Shot Asset Loader")
        self.setMinimumSize(1200, 600)

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

        # Backend modules
        self.discoverer = AssetDiscoverer(self._project_root)
        self.node_builder = NukeNodeBuilder()

        # Data
        self.current_sequence = None
        self.current_shot = None
        self.current_assets = {}
        self.asset_items = []

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
                    import PyOpenColorIO as OCIO
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

        # Header banner — populated by _detect_script_context / _scan_shot_assets
        self.info_label = QtWidgets.QLabel("Detecting shot context from script path…")
        self.info_label.setObjectName("headerBanner")
        self.info_label.setTextFormat(QtCore.Qt.RichText)
        main_layout.addWidget(self.info_label)

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
        assets_layout.addLayout(filter_layout)

        # Asset table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Type", "Version",
            "Colorspace", "Status", "Node Name", "Prim Path",
        ])
        column_widths = [180, 80, 80, 130, 220, 150, 170]
        for i, w in enumerate(column_widths):
            self.table.setColumnWidth(i, w)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setStretchLastSection(True)
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

        # Register both pages, then build the matching tab buttons
        self.tab_stack.addWidget(loader_tab)
        self.tab_stack.addWidget(logs_tab)

        self._add_tab_button("Loader", 0)
        self._add_tab_button("Logs", 1)
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
            #    e.g. SEQ_busInt-SH130_comp_v001.nk
            filename = normalized.rsplit('/', 1)[-1]
            filename_match = re.match(r'^([^-]+)-([^_]+)_.+_v\d{3,4}\.nk$', filename)
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
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("Plate", plate_name, versions, versions_dict, source_type="external")
            self._default_to_latest_full(item, scene_range)
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # 3D Renders
        for render_name, versions_dict in self.current_assets.get("3d_renders", {}).items():
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("3D Render", render_name, versions, versions_dict, source_type="3dRender")
            self._default_to_latest_full(item, scene_range)
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # 2D Renders
        for render_name, versions_dict in self.current_assets.get("2d_renders", {}).items():
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("2D Render", render_name, versions, versions_dict, source_type="2dRender")
            self._default_to_latest_full(item, scene_range)
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # Rotos (all versions)
        rotos = self.current_assets.get("rotos", {})
        for version in sorted(rotos.keys()):
            layers = rotos[version]

            item = AssetItem("Roto", "roto", [version], {version: layers}, source_type="external")
            item.selected_version = version
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # Cameras
        for cam_name, versions_dict in self.current_assets.get("cameras", {}).items():
            versions = sorted(versions_dict.keys())
            if not versions:
                continue

            item = AssetItem("Camera", cam_name, versions, versions_dict, source_type="Camera")
            item.node_name = cam_name
            item.prim_path = "/root/cameras/shotcam"
            self.asset_items.append(item)
            self._add_row(row, item)
            row += 1

        # Foreign-shot Reads — discovered straight from the scene. Their
        # loaded_node is bound at creation time so _do_check_for_updates can
        # treat them like already-loaded local assets.
        for foreign_item in self._discover_foreign_assets():
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

        # Col 5 / 6 - Node Name & Prim Path (Camera-only, editable)
        if item.asset_type == "Camera":
            node_name_edit = QtWidgets.QLineEdit(item.node_name)
            node_name_edit.textChanged.connect(lambda t, r=row: self._on_node_name_changed(r, t))
            self.table.setCellWidget(row, 5, node_name_edit)

            prim_path_edit = QtWidgets.QLineEdit(item.prim_path)
            prim_path_edit.textChanged.connect(lambda t, r=row: self._on_prim_path_changed(r, t))
            self.table.setCellWidget(row, 6, prim_path_edit)
        else:
            for col in (5, 6):
                placeholder = QtWidgets.QTableWidgetItem("")
                placeholder.setFlags(placeholder.flags() & ~QtCore.Qt.ItemIsEditable)
                self.table.setItem(row, col, placeholder)

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

    def _on_node_name_changed(self, row, text):
        """Handle Camera node-name edit."""
        if row < len(self.asset_items):
            self.asset_items[row].node_name = text

    def _on_prim_path_changed(self, row, text):
        """Handle Camera prim-path edit."""
        if row < len(self.asset_items):
            self.asset_items[row].prim_path = text

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

        # Per-camera config (node_name + prim_path), keyed by cam_name
        camera_configs = {}

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
                camera_configs[item.asset_name] = {
                    "node_name": item.node_name,
                    "prim_path": item.prim_path,
                }

        # Load
        try:
            self.node_builder.load_assets(
                sequence=self.current_sequence,
                shot=self.current_shot,
                assets=filtered_assets,
                asset_colorspaces=asset_colorspaces,
                project_root=self._project_root,
                camera_configs=camera_configs,
            )

            # Re-câble les PostageStamp existants (par titre) pour qu'ils
            # pointent sur les nouveaux Anchors qu'on vient de créer. Silent
            # car le popup de succès ci-dessous tient lieu de feedback;
            # le rapport détaillé reste imprimé dans la console.
            try:
                run_reconnect_on_postage_stamps(silent=True)
            except Exception as e:
                print(f"[ShotAssetLoader] reconnect_stamps failed (non-fatal): {e}")

            msg = (
                f"Successfully loaded {len(self.node_builder.created_nodes)} node(s) "
                f"for {self.current_sequence}/{self.current_shot}"
            )
            if already_loaded:
                msg += f"\n\nSkipped {len(already_loaded)} already-loaded asset(s)."
            QtWidgets.QMessageBox.information(self, "Success", msg)

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
        camera_nodes = [n for n in all_nodes if n.Class() == "Camera4"]

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
            node, has_duplicates = self._find_node_for_asset(item, read_nodes, camera_nodes)
            item.has_duplicates = has_duplicates

            if node:
                # Node found in scene
                item.loaded_node = node

                # For cameras: pre-fill the Node Name / Prim Path cells from the
                # live node so the user sees what's actually in the scene.
                if item.asset_type == "Camera":
                    item.node_name = node.name()
                    if 'import_prim_path' in node.knobs():
                        item.prim_path = node['import_prim_path'].value() or ""

                    node_name_widget = self.table.cellWidget(row, 5)
                    if isinstance(node_name_widget, QtWidgets.QLineEdit):
                        node_name_widget.setText(item.node_name)
                    prim_path_widget = self.table.cellWidget(row, 6)
                    if isinstance(prim_path_widget, QtWidgets.QLineEdit):
                        prim_path_widget.setText(item.prim_path)

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
                return False

            return frames.issuperset(range(scene_range[0], scene_range[1] + 1))
        except Exception as e:
            print(f"[ShotAssetLoader] Frame coverage check failed for {item.asset_name}: {e}")
            return False

    def _find_node_for_asset(self, item, read_nodes, camera_nodes):
        """Find the Nuke node corresponding to an asset item.

        Returns:
            (node, has_duplicates):
                node: the matched Nuke node, or None if nothing matches.
                has_duplicates: True only for Reads when, after filtering on
                    `fromShotLoader` and applying the name-suffix tiebreaker,
                    more than one candidate still remains — the caller should
                    surface this as a "duplicate" status to the user.

        Reads must carry the `fromShotLoader` knob (True) to be considered —
        this excludes manually-imported Reads that happen to share the path.
        When the artist Ctrl+C/Ctrl+V's a loader Read, Nuke copies the knob
        too, so we then prefer the candidate whose name has no trailing-digit
        suffix (the original load). If that still leaves multiple, we pick
        the highest version and flag the duplicate.
        """
        # Cameras: a shot generally has one camera, so first try the project
        # convention — a Camera4 named "SHOT_CAM". Fall back to file-knob
        # matching for renamed / non-canonical setups.
        if item.asset_type == "Camera":
            for cam_node in camera_nodes:
                if cam_node.name().upper() == "SHOT_CAM":
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
        needle = f"/{item.asset_name}/"
        candidates = []

        for read_node in read_nodes:
            # Only consider Reads tagged by the loader — manual imports are
            # ignored even if their file path matches.
            if not self._is_loader_owned(read_node):
                continue
            if 'file' not in read_node.knobs():
                continue

            file_path = (read_node['file'].value() or "").replace('\\', '/')
            if not file_path:
                continue
            if self.current_sequence not in file_path or self.current_shot not in file_path:
                continue
            if needle.lower() not in file_path.lower():
                continue

            candidates.append((read_node, file_path))

        if not candidates:
            return None, False

        if len(candidates) == 1:
            return candidates[0][0], False

        # Multiple candidates — duplicate suspicion. Nuke renames copies by
        # appending an incrementing number (usually just digits, sometimes
        # `_N`), so the un-suffixed name is the original load.
        suffix_pattern = re.compile(r'_?\d+$')
        unsuffixed = [c for c in candidates if not suffix_pattern.search(c[0].name())]

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

    def _perform_updates(self, items, scope_label="selected"):
        """Shared update logic: keeps only items with available updates that are loaded, confirms, then applies."""
        updateable = [item for item in items if item.has_update and item.loaded_node]

        if not updateable:
            QtWidgets.QMessageBox.information(
                self,
                "No Updates",
                f"No {scope_label} assets have updates available"
            )
            return

        # Confirm update
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Update",
            f"Update {len(updateable)} asset(s) to latest version?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

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
                    # have cached from the previous version's path. Camera4
                    # has no reload knob — guarded so it's a Read-only action.
                    if (
                        item.loaded_node.Class() == "Read"
                        and 'reload' in item.loaded_node.knobs()
                    ):
                        try:
                            item.loaded_node['reload'].execute()
                        except Exception as e:
                            print(
                                f"[ShotAssetLoader] reload knob failed for "
                                f"{item.loaded_node.name()}: {e}"
                            )
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
