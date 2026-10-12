"""Shot Loader dialog: Loader / Render Manager / Logs tabs + auto-refresh."""

import traceback
import webbrowser

import nuke

from ..core.config import Config
from ..core import project
from ..core.session import ShotSession
from ..precomp import engine
from .qt import QtCore, QtWidgets
from ..scene import utils as scene
from . import icons
from . import widgets as w
from .loader_tab import LoaderTab
from .log_console import LogConsole
from .render_tab import RenderManagerTab
from .styles import STYLESHEET

TAB_LOADER, TAB_RENDER, TAB_LOGS = range(3)
_TICK_MS = 100
_DEADLINE_CHECK_TICKS = 10   # the top-level widget scan is cached ~1s


class ShotLoaderWindow(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shot Asset Loader")
        self.setMinimumSize(1200, 600)
        # Destroyed on close: a hidden instance would keep teeing stdout and
        # receiving broadcast events (one help tab per stale dialog).
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Tee stdout/stderr first so everything printed below reaches the Logs tab.
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("logView")
        self.log_view.setMaximumBlockCount(5000)
        self.console = LogConsole(self.log_view)

        self.session = ShotSession(scene.script_path())
        self.loader_tab = LoaderTab(self.session)
        self.render_tab = RenderManagerTab(self.session, self.console)

        self._elapsed_ms = 0
        self._spin_angle = 0.0
        self._paused = False
        self._deadline_ticks = 0
        self._deadline_open = False
        self._height_fitted = False

        self._build_ui()
        self.setStyleSheet(STYLESHEET)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

        self._detect_shot()
        self.render_tab.request_refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        logs_tab = QtWidgets.QWidget()
        logs_layout = QtWidgets.QVBoxLayout(logs_tab)
        logs_layout.setContentsMargins(14, 14, 14, 14)
        logs_layout.setSpacing(8)
        logs_layout.addWidget(self.log_view)
        clear_row = QtWidgets.QHBoxLayout()
        clear_row.addStretch()
        clear_row.addWidget(w.button("Clear", self.log_view.clear))
        logs_layout.addLayout(clear_row)

        self.tab_stack = QtWidgets.QStackedWidget()
        tab_bar = QtWidgets.QHBoxLayout()
        tab_bar.setContentsMargins(0, 0, 0, 0)
        tab_bar.setSpacing(2)
        self.tab_buttons = []
        for index, (label, page) in enumerate((("Loader", self.loader_tab),
                                               ("Render Manager", self.render_tab),
                                               ("Logs", logs_tab))):
            self.tab_stack.addWidget(page)
            btn = w.button(label, lambda _=False, i=index: self._switch_tab(i), "tabHeader")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            tab_bar.addWidget(btn)
            self.tab_buttons.append(btn)
        self.tab_buttons[TAB_LOADER].setChecked(True)
        tab_bar.addStretch()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        layout.addLayout(tab_bar)
        layout.addWidget(self.tab_stack)
        layout.addWidget(self._build_status_bar())

    def _build_status_bar(self):
        """Auto-refresh spinner, pause toggle and countdown bar."""
        bar = QtWidgets.QFrame()
        bar.setObjectName("statusBar")
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.spinner = QtWidgets.QLabel()
        self.spinner.setFixedSize(18, 18)
        self.spinner.setPixmap(icons.spinner_pixmap(self._spin_angle))
        layout.addWidget(self.spinner)
        self.status_label = QtWidgets.QLabel("Auto-refresh")
        self.status_label.setObjectName("statusText")
        layout.addWidget(self.status_label)

        self.pause_btn = w.icon_button("pauseToggle", (18, 18))
        self.pause_btn.setIconSize(QtCore.QSize(12, 12))
        self.pause_btn.setCheckable(True)
        self.pause_btn.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pause_btn.setToolTip("Pause auto-refresh")
        self.pause_btn.setIcon(icons.pause_icon())
        self.pause_btn.toggled.connect(self._on_pause_toggled)
        layout.addWidget(self.pause_btn)
        layout.addStretch()

        self.countdown = QtWidgets.QProgressBar()
        self.countdown.setObjectName("tickBar")
        self.countdown.setFixedSize(220, 6)
        self.countdown.setTextVisible(False)
        self.countdown.setRange(0, Config.AUTO_REFRESH_MS)
        layout.addWidget(self.countdown)
        return bar

    def set_current_tab(self, index):
        if 0 <= index < len(self.tab_buttons):
            self.tab_buttons[index].setChecked(True)
            self._switch_tab(index)

    def _switch_tab(self, index):
        self.tab_stack.setCurrentIndex(index)
        if index == TAB_RENDER:  # pick up Writes added/renamed since last visit
            self.render_tab.request_refresh()

    # ------------------------------------------------------------------
    # Shot context
    # ------------------------------------------------------------------

    def _detect_shot(self):
        try:
            script = scene.script_path()
            context = project.detect_shot_context(script) if script else None
            if context is None:
                message = ("Save your Nuke script inside a shot folder to use the loader" if not script
                           else "Could not detect sequence/shot from the script path")
                self.loader_tab.banner.set_message(message)
                self.render_tab.banner.set_message(message)
                return
            self.session.sequence, self.session.shot = context
            print(f"[ShotAssetLoader] Auto-selected: {self.session.sequence}/{self.session.shot}")
            self.loader_tab.scan()
            self.loader_tab.refresh_status(silent=True)
        except Exception as e:
            print(f"[ShotAssetLoader] Context detection failed (not critical): {e}")

    # ------------------------------------------------------------------
    # Auto-refresh
    # ------------------------------------------------------------------

    def _on_tick(self):
        """100ms: spinner + countdown, refresh every AUTO_REFRESH_MS. Frozen
        entirely whenever the refresh would be skipped anyway."""
        if self._refresh_blocked():
            return
        if self.isMinimized():   # nobody looks: no sync freezing Nuke; refreshed as soon as it's shown again
            self._elapsed_ms = Config.AUTO_REFRESH_MS
            return
        self._elapsed_ms += _TICK_MS
        self._spin_angle = (self._spin_angle + 3.0) % 360.0
        self.spinner.setPixmap(icons.spinner_pixmap(self._spin_angle))
        self.countdown.setValue(min(self._elapsed_ms, Config.AUTO_REFRESH_MS))
        if self._elapsed_ms >= Config.AUTO_REFRESH_MS:
            self._elapsed_ms = 0
            self._auto_refresh()

    def _refresh_blocked(self):
        """Paused, Nuke rendering, a submission in progress, or the Deadline
        submitter open (it builds its jobs from the node selection)."""
        if self._paused or engine.is_busy():
            return True
        try:
            if nuke.executing():
                return True
        except Exception:
            pass
        if self._deadline_ticks <= 0:
            self._deadline_open = _deadline_submitter_open()
            self._deadline_ticks = _DEADLINE_CHECK_TICKS
        else:
            self._deadline_ticks -= 1
        return self._deadline_open

    def _auto_refresh(self):
        if not self.session.follows(scene.script_path()):
            self._reopen()
            return
        try:
            self.render_tab.request_refresh()
        except Exception as e:
            print(f"[ShotAssetLoader] auto-refresh render manager failed: {e}")
        try:
            self.console.run_deduped(lambda: self.loader_tab.refresh_status(silent=True), "loader_status")
            self.loader_tab.refresh_banner()
        except Exception as e:
            print(f"[ShotAssetLoader] auto-refresh asset check failed: {e}")

    def _reopen(self):
        """Another project's or shot's script is open in this Nuke now: a
        fresh dialog (session, prefs, tables) replaces this one, same place
        and tab."""
        print("[ShotAssetLoader] The current script belongs to another shot — reopening the dialog")
        self._timer.stop()
        tab, geometry = self.tab_stack.currentIndex(), self.geometry()
        QtCore.QTimer.singleShot(0, lambda: _replace_window(self, tab, geometry))

    def _on_pause_toggled(self, checked):
        self._paused = bool(checked)
        self.pause_btn.setIcon(icons.play_icon() if self._paused else icons.pause_icon())
        self.pause_btn.setToolTip("Resume auto-refresh" if self._paused else "Pause auto-refresh")
        self.status_label.setText("Auto-refresh | paused" if self._paused else "Auto-refresh")
        if not self._paused:  # resume on a full cycle
            self._elapsed_ms = 0
            self.countdown.setValue(0)

    # ------------------------------------------------------------------
    # Qt events
    # ------------------------------------------------------------------

    def event(self, e):
        # The title-bar "?" button opens the documentation.
        if e.type() == QtCore.QEvent.EnterWhatsThisMode:
            webbrowser.open(Config.HELP_URL)
            e.accept()
            return True
        return super().event(e)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._height_fitted:
            self._height_fitted = True
            # After the first layout pass, when table heights are known.
            QtCore.QTimer.singleShot(0, self._fit_height)

    def closeEvent(self, event):
        self._timer.stop()
        self.console.restore()
        super().closeEvent(event)

    def _fit_height(self):
        """Grow so the current tab's rows fit, within the screen."""
        tab = self.render_tab if self.tab_stack.currentIndex() == TAB_RENDER else self.loader_tab
        delta = tab.height_delta()
        if delta <= 0:
            return
        screen = QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry() if screen is not None else None
        max_height = available.height() - 60 if available is not None else 1080
        height = min(self.height() + delta, max_height)
        if height <= self.height():
            return
        self.resize(self.width(), height)
        if available is not None and self.frameGeometry().bottom() > available.bottom():
            self.move(self.x(), max(available.top(), available.bottom() - self.frameGeometry().height()))


def _deadline_submitter_open():
    app = QtWidgets.QApplication.instance()
    if app is None:
        return False
    try:
        widgets = app.topLevelWidgets()
    except Exception:
        return False
    for widget in widgets:
        try:
            if widget.isVisible() and ("Deadline" in type(widget).__name__ or "Deadline" in (widget.windowTitle() or "")):
                return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

_instance = None


def _open_window():
    """The live dialog, or None (closed dialogs are deleted on close)."""
    try:
        return _instance if _instance is not None and _instance.isVisible() else None
    except RuntimeError:  # underlying C++ object already deleted
        return None


def _replace_window(old, tab, geometry):
    global _instance
    parent = old.parentWidget()
    old.close()
    _instance = ShotLoaderWindow(parent)
    _instance.setGeometry(geometry)
    _instance.set_current_tab(tab)
    _instance.show()


def show_shot_asset_loader(initial_tab=TAB_LOADER):
    """Show the dialog (reusing the open one while it still matches the
    current script). initial_tab: 0 Loader, 1 Render Manager, 2 Logs."""
    global _instance
    try:
        window = _open_window()
        if window is not None and not window.session.follows(scene.script_path()):
            window.close()
            window = None
        if window is None:
            window = _instance = ShotLoaderWindow(QtWidgets.QApplication.instance().activeWindow())
        window.set_current_tab(initial_tab)
        window.show()
        window.raise_()
        window.activateWindow()
    except Exception as e:
        nuke.message(f"Error showing Shot Asset Loader: {e}")
        print(f"[ShotAssetLoader] Error: {e}")
        traceback.print_exc()


def show_shot_render_manager():
    show_shot_asset_loader(initial_tab=TAB_RENDER)
