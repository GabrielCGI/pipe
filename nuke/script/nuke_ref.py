"""
NukeRef - PureRef-like reference board for the Nuke Node Graph.

Architecture:
    Each reference is backed by a regular BackdropNode that owns the
    position, size and metadata. The image is rendered through two paths:

      1) Native: BackdropNode.setCustomIcon() puts the image on the node at
         the C++ level. This is what feeds the DAG mini-map (which lives
         inside DAG_Window's own paintEvent and we cannot inject Qt into).

      2) Overlay: a transparent QWidget glued to DAG_Window paints the
         image every frame in pure Qt, with no culling. This is what keeps
         deep zooms and partial-offscreen backdrops looking right.

    Both paths render in the same DAG-space rect, so visually they coincide
    in the main DAG. The user sees a single image; the Qt overlay covers
    the native icon. The mini-map only sees the native icon, which is the
    point.

    Live resize/move: dragging a backdrop's handle is an interactive drag.
    Some Nuke versions fire bdwidth knobChanged continuously during it; Nuke
    15.1 does not -- it withholds both knobChanged and DAG paint events until
    the mouse is released. To get real-time feedback regardless, we poll the
    live knob geometry at ~60Hz while a mouse button is held over a DAG and
    repaint the overlay (re-locking the aspect ratio) on every change, then
    stop the instant the button comes back up.

Install:
    1) Drop this file into ~/.nuke/
    2) Add to ~/.nuke/menu.py:

        import nuke_ref
        nuke_ref.install()
"""

import os
import time
import nuke

try:
    from PySide2.QtCore import (
        Qt, QTimer, QRectF, QRect, QPoint, QRunnable, QThreadPool, QEvent, QObject
    )
    from PySide2.QtGui import QPixmap, QImage, QCursor, QPainter, QColor
    from PySide2.QtWidgets import QApplication, QWidget
    import shiboken2 as shiboken
except ImportError:
    from PySide6.QtCore import (
        Qt, QTimer, QRectF, QRect, QPoint, QRunnable, QThreadPool, QEvent, QObject
    )
    from PySide6.QtGui import QPixmap, QImage, QCursor, QPainter, QColor
    from PySide6.QtWidgets import QApplication, QWidget
    import shiboken6 as shiboken


SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.webp')

DEFAULT_REF_WIDTH = 400  # DAG units

REF_PATH_KNOB = 'nuke_ref_path'
REF_NATIVE_W_KNOB = 'nuke_ref_native_w'
REF_NATIVE_H_KNOB = 'nuke_ref_native_h'

# How long after the last bdwidth change to keep nudging repaints so the
# resize settles cleanly once the user lets go of the handle.
RESIZE_DIM_WINDOW_S = 0.20
# Opacity of the image while actively resizing. Kept at full so the live
# resize stays clearly visible (the old behaviour dimmed it to 0.30).
RESIZE_DIM_OPACITY = 1.0

# --- Selection aids drawn on top of each reference by the overlay ----------
# Small semi-transparent squares at the four corners only. Size is in on-
# screen pixels (constant at any zoom) so they stay visible without hiding
# the image.
HANDLE_SIZE_PX = 11
_HANDLE_FILL = QColor(255, 255, 255, 160)
_HANDLE_EDGE = QColor(10, 10, 10, 190)

# Module-level state
_OVERLAYS = {}              # id(DAG_Window) -> _RefOverlay
_PIXMAP_CACHE = {}          # path -> {'native': QPixmap, 'levels': {w: QPixmap}}
_LAST_RESIZE_TS = {}        # node fullname -> time of last bdwidth change
_INSTALL_TIMER = None       # legacy slow timer (cleanup only, not paint)
_GEO_TIMER = None           # timer that re-glues overlay windows to DAGs

# Live-resize support. On Nuke 15.1 the bdwidth/bdheight knobs are NOT written
# while a backdrop handle is dragged -- they only commit on mouse release, so
# knobChanged (and our overlay) would otherwise update only at the end. The
# node's C++ on-screen size *does* update live though, via Node.screenWidth().
# So while a left button is held over a DAG we poll screenWidth() at ~60Hz and
# feed an override size to the overlay, then drop it the instant the mouse is
# released (the committed knob value takes over). Idle cost is zero.
_RESIZE_POLL_TIMER = None        # QTimer, active only during a mouse drag
_RESIZE_POLL_INTERVAL_MS = 16    # ~60Hz while dragging; idle cost is zero
_DRAG_LIVE = {}                  # node fullname -> (xpos, ypos, w, h) live override during a drag

# Event-driven overlay update: we install an eventFilter on each DAG_Window
# and trigger our overlay's repaint *exactly* when the DAG itself repaints.
# This eliminates the 30Hz polling that the previous version did.
_DAG_FILTER = None          # _DagEventFilter instance, shared across DAGs

# Cached list of "our" backdrop nodes, refreshed only when nodes are added or
# removed. allNodes('BackdropNode') walks the whole graph every call and gets
# expensive once the comp has many regular backdrops too.
_REF_NODES_CACHE = None     # list[nuke.Node] or None when invalidated
_REF_NODES_DIRTY = True

# Dirty-state cache. The overlay only repaints when one of these snapshots
# actually changes between ticks. In idle (no pan, no zoom, no node edits)
# the cost of a tick collapses to a few dict comparisons.
_DIRTY_STATE = {}           # id(DAG_Window) -> dict of last-known scene state


# ---------------------------------------------------------------------------
# Qt object liveness
# ---------------------------------------------------------------------------

def _is_alive(qt_obj):
    """True if the C++ object under a PySide wrapper still exists."""
    if qt_obj is None:
        return False
    try:
        return bool(shiboken.isValid(qt_obj))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Ref-node cache
# ---------------------------------------------------------------------------
#
# Calling nuke.allNodes('BackdropNode') every paint walks the whole graph in
# Nuke's C++ side and gets noticeable once the comp has many real backdrops
# alongside ours. We cache the filtered list of reference backdrops and
# invalidate it through Nuke callbacks for add/delete events.

def _invalidate_ref_cache(*args, **kwargs):
    """Mark the cached ref-nodes list as stale. Cheap; never traverses."""
    global _REF_NODES_DIRTY
    _REF_NODES_DIRTY = True
    # Force a repaint of every overlay so newly created / deleted refs
    # show up immediately rather than on the next pan/zoom.
    for ov in list(_OVERLAYS.values()):
        if _is_alive(ov):
            try:
                ov.update()
            except RuntimeError:
                pass


def _get_ref_nodes():
    """Return the cached list of reference backdrop nodes. Rebuild if stale."""
    global _REF_NODES_CACHE, _REF_NODES_DIRTY
    if _REF_NODES_DIRTY or _REF_NODES_CACHE is None:
        try:
            _REF_NODES_CACHE = [
                bd for bd in nuke.allNodes('BackdropNode')
                if REF_PATH_KNOB in bd.knobs()
            ]
        except Exception:
            _REF_NODES_CACHE = []
        _REF_NODES_DIRTY = False
    return _REF_NODES_CACHE


# ---------------------------------------------------------------------------
# Event-driven overlay updates
# ---------------------------------------------------------------------------
#
# Instead of polling at 30Hz with a QTimer, we install an event filter on
# each DAG_Window so our overlay repaints *only* when the DAG itself does.
# In idle the cost drops to zero. While the user pans or zooms, Nuke
# already repaints the DAG, and we piggyback on that event.

class _DagEventFilter(QObject):
    """
    Forwards DAG_Window paint/resize events into overlay updates and
    remembers the last mouse-click position in each DAG so paste_reference()
    can drop the new ref where the user last interacted with the graph --
    exactly how Nuke's own node creation behaves.
    """

    # id(DAG_Window) -> (x_local, y_local) of the most recent mouse press
    LAST_CLICK = {}

    def eventFilter(self, obj, event):
        et = event.type()

        # Paint covers pan, zoom, and arbitrary internal Nuke repaints.
        if et == QEvent.Paint:
            ov = _OVERLAYS.get(id(obj))
            if ov is not None and _is_alive(ov):
                # Don't synchronously paint here -- that would re-enter Qt's
                # paint pipeline. Schedule a paint for the next tick.
                try:
                    ov.update()
                except RuntimeError:
                    pass

        # Resize/Move/Show/Hide change where the DAG sits on screen. Since the
        # overlay is now a separate top-level window, it must re-glue itself to
        # the DAG's new global rect (and hide/show with the DAG's tab).
        elif et in (QEvent.Resize, QEvent.Move, QEvent.Show, QEvent.Hide):
            ov = _OVERLAYS.get(id(obj))
            if ov is not None and _is_alive(ov):
                try:
                    ov._sync_geometry()
                    ov.update()
                except RuntimeError:
                    pass

        # Track every mouse press inside any DAG so paste-at-cursor works
        # regardless of where the keyboard focus currently sits when the
        # user hits Ctrl+V. Without this, pressing the shortcut while the
        # cursor is over the menu bar or another panel would stack refs
        # at whatever the global cursor happened to be over.
        elif et == QEvent.MouseButtonPress:
            try:
                pos = event.pos()
                _DagEventFilter.LAST_CLICK[id(obj)] = (pos.x(), pos.y())
            except Exception:
                pass
            # Start live-geometry polling for the duration of this drag, so a
            # backdrop resize/move updates the overlay in real time on Nuke
            # versions (e.g. 15.1) that withhold knobChanged + DAG paints until
            # the mouse is released. Cheap: only runs while a button is held and
            # only when there is at least one reference to track.
            try:
                if event.button() == Qt.LeftButton and _get_ref_nodes():
                    _begin_drag_poll()
            except Exception:
                pass

        # Never consume events: let Nuke handle them normally.
        return False


# ---------------------------------------------------------------------------
# Disk helpers
# ---------------------------------------------------------------------------

def _script_dir_or_none():
    """Return the directory of the saved .nk, or None if unsaved."""
    script_path = nuke.root().name()
    if not script_path or script_path == 'Root':
        return None
    script_dir = os.path.dirname(script_path)
    if not script_dir or not os.path.isdir(script_dir):
        return None
    return script_dir


def _resolve_storage_dir_or_warn():
    """Resolve <script_dir>/nuke_ref_images/ or pop a warning dialog."""
    script_dir = _script_dir_or_none()
    if script_dir is None:
        nuke.message(
            'NukeRef: please save your Nuke script first.\n\n'
            'Reference images are stored alongside the .nk file.'
        )
        return None

    target = os.path.join(script_dir, 'nuke_ref_images')
    try:
        os.makedirs(target, exist_ok=True)
    except OSError as err:
        nuke.message('NukeRef: could not create {}: {}'.format(target, err))
        return None
    return target


def _unique_filename(directory, prefix='ref'):
    ts = int(time.time() * 1000)
    candidate = os.path.join(directory, '{}_{}.png'.format(prefix, ts))
    counter = 0
    while os.path.exists(candidate):
        counter += 1
        candidate = os.path.join(
            directory, '{}_{}_{}.png'.format(prefix, ts, counter)
        )
    return candidate


def _save_qimage_as_png(qimage):
    directory = _resolve_storage_dir_or_warn()
    if directory is None:
        return None
    path = _unique_filename(directory)
    if not qimage.save(path, 'PNG', 100):
        raise IOError('Failed to write reference image to {}'.format(path))
    return path


# ---------------------------------------------------------------------------
# Clipboard helpers
# ---------------------------------------------------------------------------

def _grab_clipboard_payload():
    """Pull image data from the clipboard in one pass."""
    clipboard = QApplication.clipboard()

    image = clipboard.image()
    if image is not None and not image.isNull():
        return ('image', image)

    mime = clipboard.mimeData()
    if mime is not None:
        try:
            has_urls = mime.hasUrls()
        except RuntimeError:
            has_urls = False
        if has_urls:
            try:
                urls = list(mime.urls())
            except RuntimeError:
                urls = []
            for url in urls:
                if not url.isLocalFile():
                    continue
                local = url.toLocalFile()
                if local.lower().endswith(SUPPORTED_EXTENSIONS):
                    return ('path', local)

    return (None, None)


# ---------------------------------------------------------------------------
# DAG widget discovery + coordinate mapping
# ---------------------------------------------------------------------------

def _all_dag_widgets():
    """Every live, visible DAG_Window widget."""
    app = QApplication.instance()
    if app is None:
        return []
    out = []
    for w in app.allWidgets():
        if not _is_alive(w):
            continue
        if w.metaObject().className() != 'DAG_Window':
            continue
        if not w.isVisible():
            continue
        out.append(w)
    return out


def _dag_widget_under_cursor():
    """Visible DAG_Window under the mouse cursor, or fallback to any visible."""
    cursor_pos = QCursor.pos()
    fallback = None
    for w in _all_dag_widgets():
        local = w.mapFromGlobal(cursor_pos)
        if w.rect().contains(local):
            return w
        fallback = w
    return fallback


def _paste_target_coords():
    """
    Decide where the next pasted reference should land in DAG (node) space.

    Priority:
      1) If the cursor is currently over a DAG_Window, use that position
         (covers the macOS-style "hover the graph, hit the shortcut" case).
      2) Otherwise, fall back to the last recorded mouse-click position
         inside any DAG (covers Windows-style "click in graph, then go to
         a menu, then hit the shortcut"). Same model Nuke uses for its
         own node-creation shortcuts.
      3) If neither exists, return None and callers will drop at (0, 0).
    """
    zoom = nuke.zoom()
    center = nuke.center()
    if not zoom or zoom <= 0 or center is None:
        return None

    # Path 1: cursor over DAG right now.
    dag_under = _dag_widget_under_cursor()
    if dag_under is not None:
        cursor_global = QCursor.pos()
        local = dag_under.mapFromGlobal(cursor_global)
        if dag_under.rect().contains(local):
            dx_px = local.x() - dag_under.width() / 2.0
            dy_px = local.y() - dag_under.height() / 2.0
            return (int(center[0] + dx_px / zoom),
                    int(center[1] + dy_px / zoom))

    # Path 2: most recent click inside a DAG. Pick the first DAG that has
    # a remembered click; in practice there is usually only one focused.
    for dag in _all_dag_widgets():
        click = _DagEventFilter.LAST_CLICK.get(id(dag))
        if click is None:
            continue
        cx, cy = click
        dx_px = cx - dag.width() / 2.0
        dy_px = cy - dag.height() / 2.0
        return (int(center[0] + dx_px / zoom),
                int(center[1] + dy_px / zoom))

    return None


# Kept for backwards compatibility with anything that still imports it.
def _cursor_to_dag_coords():
    return _paste_target_coords()


def _dag_to_widget_rect(dag, x_node, y_node, w_node, h_node):
    """Map a DAG-space rect to widget pixel coordinates inside `dag`."""
    zoom = nuke.zoom()
    center = nuke.center()
    if not zoom or zoom <= 0 or center is None:
        return None

    half_w = dag.width() / 2.0
    half_h = dag.height() / 2.0
    px = (x_node - center[0]) * zoom + half_w
    py = (y_node - center[1]) * zoom + half_h
    return QRectF(px, py, w_node * zoom, h_node * zoom)


# ---------------------------------------------------------------------------
# Mip-pyramid pixmap cache
# ---------------------------------------------------------------------------
#
# Painting a 4K QPixmap into a 400px rect 30 times a second is what kills the
# overlay. Qt has to downsample 4K -> 400px every frame, with smoothing on.
#
# Instead, for each source PNG we keep multiple pre-scaled copies (a "mip
# pyramid") at fixed widths: 4096, 2048, 1024, 512, 256, 128, 64. At paint
# time we pick the smallest level whose width is >= the on-screen width, so
# Qt does at most a minor downscale (which is fast). When the on-screen size
# changes by less than ~10% from a level, we even skip SmoothPixmapTransform.
#
# Levels are computed lazily on first use, so users don't pay the upfront
# cost when opening a script with many refs they aren't looking at yet.

# Cache structure: _PIXMAP_CACHE[path] = {
#   'native': QPixmap,        # full-resolution, decoded once
#   'levels': {w: QPixmap},   # width-keyed downscaled copies
# }
_MIP_LEVELS = (4096, 2048, 1024, 512, 256, 128, 64)


def _get_native_pixmap(path):
    """Decode the source file once and remember it."""
    if not path:
        return None
    entry = _PIXMAP_CACHE.get(path)
    if entry is not None:
        return entry['native']
    if not os.path.isfile(path):
        return None
    pix = QPixmap(path)
    if pix.isNull():
        return None
    _PIXMAP_CACHE[path] = {'native': pix, 'levels': {}}
    return pix


def _pick_mip_level(native_w, on_screen_w):
    """
    Choose the mip width to use for a given on-screen size.

    Pick the smallest level whose width is >= on_screen_w, so we always
    downscale (which is cheap and looks good) and never upscale (which
    blurs). Cap at the native width.
    """
    target = max(1, int(on_screen_w))
    candidates = [w for w in _MIP_LEVELS if w >= target and w <= native_w]
    if candidates:
        return min(candidates)
    # On-screen is bigger than every preset level -> use the native pixmap.
    return native_w


def _get_pixmap_for_size(path, on_screen_w):
    """
    Return a QPixmap roughly matching on_screen_w in width.

    Uses the mip cache. Generates the requested level on demand the first
    time it's asked for, then reuses it for subsequent frames.

    Returns (pixmap, exact_size_match):
        pixmap          - the QPixmap to blit
        exact_size_match - True if the chosen level's width is within 10%
                           of on_screen_w (signal to skip smooth scaling)
    """
    native = _get_native_pixmap(path)
    if native is None:
        return (None, False)

    native_w = native.width()
    if native_w <= 0:
        return (None, False)

    level_w = _pick_mip_level(native_w, on_screen_w)

    # Native fits the bill (target bigger than top mip, or path's native
    # width is smaller than the smallest mip level larger than target).
    if level_w == native_w:
        ratio = abs(level_w - on_screen_w) / max(on_screen_w, 1.0)
        return (native, ratio < 0.10)

    entry = _PIXMAP_CACHE[path]
    cached = entry['levels'].get(level_w)
    if cached is None:
        # First time we need this level for this image. Scale by width and
        # let Qt compute the matching height to preserve aspect.
        cached = native.scaledToWidth(level_w, Qt.SmoothTransformation)
        entry['levels'][level_w] = cached

    ratio = abs(level_w - on_screen_w) / max(on_screen_w, 1.0)
    return (cached, ratio < 0.10)


def _purge_pixmap_cache():
    _PIXMAP_CACHE.clear()


# ---------------------------------------------------------------------------
# Background mip-level pre-generation
# ---------------------------------------------------------------------------
#
# Synchronously building a 4K -> 128px mip the first time it's needed creates
# a hiccup right when many small refs appear at once (typical when zooming
# out). To avoid that, every time we add or load a reference we kick off a
# QRunnable that builds all the cheap mip levels (<= 1024px) up front in
# a background thread. The biggest levels (2048, 4096) we still build on
# demand because they're rarely the right pick anyway.
#
# QPixmap operations are GUI-thread-only, so the worker uses QImage for the
# scaling (which is thread-safe), then hands the result to the GUI thread
# via QTimer.singleShot(0, ...) to convert to QPixmap and install in the
# cache. That trampoline is the only thread-safe way to publish a QPixmap
# from a worker thread.

_PREWARM_LEVELS = (1024, 512, 256, 128, 64)
_PREWARMED_PATHS = set()  # paths whose cheap levels we've already kicked off


class _MipPrewarmJob(QRunnable):
    """Loads a source image and pre-scales it down to common small sizes."""

    def __init__(self, path):
        super(_MipPrewarmJob, self).__init__()
        self._path = path
        self.setAutoDelete(True)

    def run(self):
        path = self._path
        if not os.path.isfile(path):
            return
        # Decode in the worker thread so the GUI thread never has to wait
        # on disk I/O for big PNGs.
        src = QImage(path)
        if src.isNull():
            return
        native_w = src.width()
        if native_w <= 0:
            return

        # Pre-scale to the requested mip levels using QImage (thread-safe).
        # Skip levels at or above native_w -- those would be the native image.
        scaled = {}
        for level_w in _PREWARM_LEVELS:
            if level_w >= native_w:
                continue
            try:
                img = src.scaledToWidth(
                    level_w,
                    Qt.SmoothTransformation,
                )
            except Exception:
                continue
            if not img.isNull():
                scaled[level_w] = img

        # Hand the result back to the GUI thread for QPixmap conversion +
        # cache install. Capture by default args so the closure doesn't
        # share state with subsequent jobs.
        def _publish(path=path, src_img=src, scaled_imgs=scaled):
            entry = _PIXMAP_CACHE.get(path)
            if entry is None:
                # Convert source to QPixmap once; it becomes the cache 'native'.
                native_pix = QPixmap.fromImage(src_img)
                if native_pix.isNull():
                    return
                entry = {'native': native_pix, 'levels': {}}
                _PIXMAP_CACHE[path] = entry
            for level_w, img in scaled_imgs.items():
                if level_w in entry['levels']:
                    continue
                pix = QPixmap.fromImage(img)
                if not pix.isNull():
                    entry['levels'][level_w] = pix

        QTimer.singleShot(0, _publish)


def _prewarm_mips(path):
    """Schedule background mip generation for a path (idempotent)."""
    if not path or path in _PREWARMED_PATHS:
        return
    _PREWARMED_PATHS.add(path)
    QThreadPool.globalInstance().start(_MipPrewarmJob(path))


# ---------------------------------------------------------------------------
# Native icon (feeds the mini-map and is a fallback)
# ---------------------------------------------------------------------------

def _refresh_native_icon(backdrop):
    """
    Re-set the BackdropNode's custom icon so the mini-map shows the image.

    scale = bdwidth / native_width; matches the Qt overlay's geometry so
    the two render paths line up visually in the main DAG.
    """
    if REF_PATH_KNOB not in backdrop.knobs():
        return
    if REF_NATIVE_W_KNOB not in backdrop.knobs():
        return
    path = backdrop[REF_PATH_KNOB].value()
    if not path or not os.path.isfile(path):
        return

    native_w = backdrop[REF_NATIVE_W_KNOB].value()
    if not native_w or native_w <= 0:
        return
    scale = float(backdrop['bdwidth'].value()) / float(native_w)
    if scale <= 0:
        return

    try:
        backdrop.setCustomIcon(path, scale, 0, 0)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Overlay widget
# ---------------------------------------------------------------------------

class _RefOverlay(QWidget):
    """Transparent overlay glued to a DAG_Window. Paints references in Qt."""

    def __init__(self, dag_widget):
        # Top-level window owned by the DAG's window -- NOT a child widget.
        # A translucent *child* over Nuke's GPU-painted DAG doesn't composite:
        # its "transparent" pixels come out solid black and black out the whole
        # node graph (only opaque draws like the image survive). A top-level
        # frameless window is composited by the OS (DWM on Windows), so its
        # transparent areas correctly show the DAG behind it. It stays
        # click-through, so selecting / moving / resizing backdrops still
        # reaches Nuke underneath.
        super(_RefOverlay, self).__init__(dag_widget.window())
        self._dag = dag_widget

        # NOTE: no WindowStaysOnTopHint. It would force the overlay above
        # Nuke's own dialogs (e.g. the "new layer" popup from a Shuffle),
        # making them unreachable. As a Tool window owned by the DAG's window
        # it already floats above that window's content (the DAG) without
        # outranking sibling dialogs.
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self._sync_geometry()
        self.show()
        self.raise_()

    def _sync_geometry(self):
        """Glue the overlay window to the DAG's on-screen rect.

        As a top-level window our geometry is in *global* screen coordinates,
        so we must follow the DAG as the Nuke window moves, resizes, docks, or
        its tab is switched. Returns False (and hides us) when the DAG is gone
        or not currently visible.
        """
        dag = self._dag
        if not _is_alive(dag):
            return False
        try:
            if not dag.isVisible():
                if self.isVisible():
                    self.hide()
                return False
            top_left = dag.mapToGlobal(QPoint(0, 0))
            target = QRect(
                top_left.x(), top_left.y(), dag.width(), dag.height()
            )
        except RuntimeError:
            # Dag died between the liveness check and the access.
            return False
        if self.geometry() != target:
            self.setGeometry(target)
        if not self.isVisible():
            self.show()
            self.raise_()
        return True

    def paintEvent(self, event):
        # Don't re-sync geometry here: setGeometry() inside paintEvent can
        # re-enter the paint pipeline. Geometry is kept current by the event
        # filter (DAG resize/move/show/hide) and the geometry timer.
        if not _is_alive(self._dag):
            return

        painter = QPainter(self)

        # Wipe our own backing surface to fully transparent every frame.
        # Without this, on Windows the translucent child overlay never gets
        # auto-cleared: every pan/zoom/drag stamps another copy of the image
        # on top of the last one, smearing refs into a "spiral" of repeats.
        # It also leaves the surface opaque-black before any ref exists,
        # which is why the DAG looks all black at startup. Clearing here
        # fixes both, and must happen *before* any early return below.
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(self.rect(), Qt.transparent)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

        refs = []
        for bd in _get_ref_nodes():
            try:
                path = bd[REF_PATH_KNOB].value()
            except Exception:
                continue
            if not path:
                continue
            refs.append((bd, path))
        if not refs:
            painter.end()
            return

        now = time.time()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

        overlay_rect = QRectF(self.rect())

        for bd, path in refs:
            try:
                full_name = bd.fullName()
                # During an interactive resize the bdwidth/bdheight knobs are
                # stale (Nuke commits them only on mouse release); the drag-poll
                # timer publishes the live size here so we rescale in real time.
                live = _DRAG_LIVE.get(full_name)
                if live is not None:
                    x, y, w, h = live
                else:
                    x = int(bd['xpos'].value())
                    y = int(bd['ypos'].value())
                    w = int(bd['bdwidth'].value())
                    h = int(bd['bdheight'].value())
            except Exception:
                continue
            if w <= 0 or h <= 0:
                continue

            dst = _dag_to_widget_rect(self._dag, x, y, w, h)
            if dst is None:
                continue
            if not dst.intersects(overlay_rect):
                continue

            on_screen_w = dst.width()
            pix, close_match = _get_pixmap_for_size(path, on_screen_w)
            if pix is None:
                continue

            painter.setRenderHint(
                QPainter.SmoothPixmapTransform, not close_match
            )

            last_ts = _LAST_RESIZE_TS.get(full_name)
            dim_active = (
                last_ts is not None and (now - last_ts) < RESIZE_DIM_WINDOW_S
            )
            painter.setOpacity(RESIZE_DIM_OPACITY if dim_active else 1.0)

            # Clip the draw to the visible overlay rect ourselves rather
            # than passing the full dst into drawPixmap. At extreme zoom
            # dst can be tens or hundreds of thousands of pixels across,
            # and Qt's raster engine (especially on Windows) is known to
            # drop draws when the destination exceeds the surface by too
            # much. Computing the clipped dest + matching source ourselves
            # keeps Qt comfortable at any zoom level.
            visible = dst.intersected(overlay_rect)
            if visible.isEmpty():
                continue

            pix_w = pix.width()
            pix_h = pix.height()
            if pix_w <= 0 or pix_h <= 0:
                continue
            dst_w = dst.width()
            dst_h = dst.height()
            if dst_w <= 0 or dst_h <= 0:
                continue

            sx = (visible.left() - dst.left()) / dst_w * pix_w
            sy = (visible.top() - dst.top()) / dst_h * pix_h
            sw = visible.width() / dst_w * pix_w
            sh = visible.height() / dst_h * pix_h
            src = QRectF(sx, sy, sw, sh)
            painter.drawPixmap(visible, pix, src)

            # Corner handles, only while the backdrop is selected. Selecting
            # a node repaints the DAG (visual highlight), which the event
            # filter forwards to us, so they appear/disappear immediately.
            try:
                selected = bd['selected'].value()
            except Exception:
                selected = False
            if selected:
                self._paint_decorations(painter, dst, overlay_rect)

        painter.end()

    def _paint_decorations(self, painter, dst, overlay_rect):
        """Draw a small handle at each of the four corners of one reference."""
        if dst.intersected(overlay_rect).isEmpty():
            return
        # Too small on screen to bother -- keeps a zoomed-out graph clean.
        if dst.width() < 44 or dst.height() < 44:
            return

        painter.setOpacity(1.0)
        painter.setPen(_HANDLE_EDGE)
        painter.setBrush(_HANDLE_FILL)

        left, right = dst.left(), dst.right()
        top, bottom = dst.top(), dst.bottom()
        half = HANDLE_SIZE_PX / 2.0
        for hx, hy in ((left, top), (right, top), (left, bottom), (right, bottom)):
            if not (overlay_rect.left() - half <= hx <= overlay_rect.right() + half):
                continue
            if not (overlay_rect.top() - half <= hy <= overlay_rect.bottom() + half):
                continue
            painter.drawRect(QRectF(
                hx - half, hy - half,
                float(HANDLE_SIZE_PX), float(HANDLE_SIZE_PX),
            ))


# ---------------------------------------------------------------------------
# Overlay lifecycle: bootstrap, monitor, cleanup
# ---------------------------------------------------------------------------

def _ensure_overlays():
    """Maintain one _RefOverlay per live DAG_Window, plus its event filter."""
    global _DAG_FILTER
    if _DAG_FILTER is None:
        _DAG_FILTER = _DagEventFilter()

    live_dags = _all_dag_widgets()

    # Drop overlays only when their DAG is actually destroyed -- NOT merely
    # hidden (e.g. its tab switched away). A hidden DAG keeps its overlay,
    # which hides itself via _sync_geometry and reappears instantly when the
    # tab comes back, instead of waiting for the next 2s cleanup to rebuild it.
    for dag_id in list(_OVERLAYS.keys()):
        ov = _OVERLAYS[dag_id]
        if not _is_alive(ov) or not _is_alive(ov._dag):
            try:
                if _is_alive(ov):
                    ov.deleteLater()
            except Exception:
                pass
            del _OVERLAYS[dag_id]
            _DIRTY_STATE.pop(dag_id, None)

    # Add overlays for newly-visible DAGs and install the event filter on
    # each DAG. The filter forwards paint/resize events into ov.update(),
    # giving us zero CPU cost in idle. We deliberately do NOT re-raise()
    # existing overlays here: doing it on a timer would shove the overlay back
    # above any Nuke dialog the user just opened. The owned-tool-window
    # relationship keeps it above the DAG on its own.
    for dag in live_dags:
        dag_id = id(dag)
        if dag_id not in _OVERLAYS:
            _OVERLAYS[dag_id] = _RefOverlay(dag)
            _DIRTY_STATE.pop(dag_id, None)
            try:
                dag.installEventFilter(_DAG_FILTER)
            except Exception:
                pass


def _sync_overlay_geometry():
    """Re-glue each overlay window to the DAG's on-screen rect.

    Window moves and dock rearrangements change where the DAG sits on screen
    without firing any event on the DAG widget, so this light timer chases it:
    one mapToGlobal + rect compare per overlay, no Nuke-graph traversal.

    Note: we deliberately do NOT poll node knobs here. Reading xpos/bdwidth/...
    off every ref ~20x/s hammers Nuke's Python API from a timer and was making
    the node graph stutter. Pan/zoom/move repaints already come from the DAG
    paint event filter; resize repaints come from _on_knob_changed.
    """
    for ov in list(_OVERLAYS.values()):
        if _is_alive(ov):
            try:
                ov._sync_geometry()
            except RuntimeError:
                pass


def _slow_cleanup():
    """
    Low-frequency housekeeping (called every 2s, not every frame).

    Watches for new DAG panels appearing (after splitting / docking) and
    expires the resize-dim timestamps so the overlay doesn't keep repainting
    forever after the user lets go of a resize handle.
    """
    try:
        _ensure_overlays()
    except Exception as err:
        nuke.tprint('[NukeRef] cleanup error: {}'.format(err))

    # Any node currently within the dim window forces a quick repaint so
    # the opacity animation finishes cleanly. Once the timestamps expire
    # we stop triggering.
    now = time.time()
    expired_names = []
    needs_repaint = False
    for name, ts in list(_LAST_RESIZE_TS.items()):
        if (now - ts) < RESIZE_DIM_WINDOW_S:
            needs_repaint = True
        else:
            expired_names.append(name)
    for name in expired_names:
        _LAST_RESIZE_TS.pop(name, None)
        needs_repaint = True

    if needs_repaint:
        for ov in _OVERLAYS.values():
            if _is_alive(ov):
                try:
                    ov.update()
                except RuntimeError:
                    pass


# ---------------------------------------------------------------------------
# Live resize / move: aspect lock, native icon refresh, overlay repaint
# ---------------------------------------------------------------------------

def _repaint_overlays():
    """Schedule a repaint on every live overlay."""
    for ov in list(_OVERLAYS.values()):
        if _is_alive(ov):
            try:
                ov.update()
            except RuntimeError:
                pass


def _aspect_height(node, bdwidth):
    """Aspect-locked height (source ratio) for a given width, or None if the
    node is missing its native-size knobs."""
    if REF_NATIVE_W_KNOB not in node.knobs():
        return None
    if REF_NATIVE_H_KNOB not in node.knobs():
        return None
    nw = float(node[REF_NATIVE_W_KNOB].value())
    nh = float(node[REF_NATIVE_H_KNOB].value())
    if nw <= 0 or nh <= 0:
        return None
    return int(round(float(bdwidth) * nh / nw))


def _lock_aspect_and_icon(node):
    """Lock bdheight to the source aspect for the current bdwidth and re-issue
    the native icon at the new scale.

    Returns True if bdheight was actually changed.
    """
    target_h = _aspect_height(node, node['bdwidth'].value())
    if target_h is None:
        return False

    changed = False
    if int(node['bdheight'].value()) != target_h:
        node['bdheight'].setValue(target_h)
        changed = True

    # Re-issue the native icon at the new scale, so the mini-map keeps up.
    _refresh_native_icon(node)
    return changed


def _on_knob_changed():
    """
    Fires for every knob change on BackdropNodes. On our refs a bdwidth change
    locks bdheight to the source aspect, re-issues setCustomIcon and repaints
    the overlay.

    On Nuke versions that emit bdwidth continuously during a handle drag this
    alone gives live feedback. On 15.1, where it only fires once on mouse
    release, the live part is driven by the drag-poll timer (_begin_drag_poll)
    and this just settles the final, committed size.
    """
    node = nuke.thisNode()
    if node.Class() != 'BackdropNode':
        return
    if REF_PATH_KNOB not in node.knobs():
        return

    knob = nuke.thisKnob()
    if knob is None or knob.name() != 'bdwidth':
        return

    _lock_aspect_and_icon(node)

    # Tag this node so the housekeeping timer keeps repainting briefly after
    # the drag ends, letting the final size settle cleanly.
    try:
        _LAST_RESIZE_TS[node.fullName()] = time.time()
    except Exception:
        pass

    _repaint_overlays()


# ---------------------------------------------------------------------------
# Live drag poll
# ---------------------------------------------------------------------------
#
# Backdrop resize/move in the DAG is an interactive drag. In Nuke 15.1 the
# bdwidth/bdheight/xpos/ypos knobs update live during that drag, but neither
# knobChanged nor a DAG paint event fires until the mouse is released -- so the
# overlay would only catch up on release. We start this short-lived ~60Hz timer
# on every left-button press over a DAG (only when refs exist) and let it read
# the live knob values, re-lock aspect and repaint until the button comes up.

def _begin_drag_poll():
    """Start polling live ref geometry for the duration of a mouse drag."""
    global _RESIZE_POLL_TIMER
    if _RESIZE_POLL_TIMER is None:
        _RESIZE_POLL_TIMER = QTimer()
        _RESIZE_POLL_TIMER.setInterval(_RESIZE_POLL_INTERVAL_MS)
        _RESIZE_POLL_TIMER.timeout.connect(_poll_drag_geometry)
    if not _RESIZE_POLL_TIMER.isActive():
        _DRAG_LIVE.clear()
        _RESIZE_POLL_TIMER.start()


def _poll_drag_geometry():
    """Publish live ref size to the overlay while the mouse is held; stop on up.

    The knobs are stale mid-drag on Nuke 15.1, but Node.screenWidth() tracks the
    live drag, so we read that, lock the height to the source aspect, stash the
    result in _DRAG_LIVE (consumed by the overlay's paintEvent) and repaint. On
    release we drop the overrides and settle the committed knob size.
    """
    if _RESIZE_POLL_TIMER is None:
        return

    # Drag over the moment no left button is held: drop overrides, settle the
    # final committed size + icon, repaint, and stop polling.
    if not (QApplication.mouseButtons() & Qt.LeftButton):
        _RESIZE_POLL_TIMER.stop()
        _DRAG_LIVE.clear()
        for bd in _get_ref_nodes():
            try:
                _lock_aspect_and_icon(bd)
            except Exception:
                pass
        _repaint_overlays()
        return

    repaint = False
    for bd in _get_ref_nodes():
        try:
            full_name = bd.fullName()
            x = int(bd['xpos'].value())
            y = int(bd['ypos'].value())
            live_w = int(round(bd.screenWidth()))
        except Exception:
            continue
        if live_w <= 0:
            continue

        # screenHeight() is free-aspect and includes the header strip; derive a
        # clean uniformly-scaled height from the source ratio instead.
        live_h = _aspect_height(bd, live_w)
        if live_h is None:
            try:
                live_h = int(round(bd.screenHeight()))
            except Exception:
                continue

        cur = (x, y, live_w, live_h)
        if _DRAG_LIVE.get(full_name) == cur:
            continue
        _DRAG_LIVE[full_name] = cur
        repaint = True

    if repaint:
        _repaint_overlays()


# ---------------------------------------------------------------------------
# Backdrop creation
# ---------------------------------------------------------------------------

def _make_reference_backdrop(image_path, source_image=None):
    if source_image is not None and not source_image.isNull():
        native_w = source_image.width()
        native_h = source_image.height()
    else:
        probe = QImage(image_path)
        if probe.isNull():
            native_w = native_h = DEFAULT_REF_WIDTH
        else:
            native_w = probe.width()
            native_h = probe.height()

    safe_path = image_path.replace('\\', '/')

    display_w = min(native_w, DEFAULT_REF_WIDTH)
    display_h = int(round(display_w * native_h / max(native_w, 1)))

    pos = _paste_target_coords() or (0, 0)
    xpos = int(pos[0] - display_w / 2)
    ypos = int(pos[1] - display_h / 2)

    # note_font_size drives the height of the backdrop's native header -- the
    # strip Nuke lets you click to select / move it. At 1 it's ungrabbable;
    # bumping it gives a real grab zone (independent of any label text). We
    # keep the label empty so the node stays clean; the image is drawn by the
    # overlay, not by a label.
    bd = nuke.nodes.BackdropNode(
        name='BackdropNode_Ref1',
        xpos=xpos,
        ypos=ypos,
        bdwidth=display_w,
        bdheight=display_h,
        note_font_size=30,
        label='',
        tile_color=0x202020ff,
        z_order=-10,
    )

    path_knob = nuke.String_Knob(REF_PATH_KNOB, 'ref path')
    path_knob.setFlag(nuke.INVISIBLE)
    bd.addKnob(path_knob)
    bd[REF_PATH_KNOB].setValue(safe_path)

    nw_knob = nuke.Int_Knob(REF_NATIVE_W_KNOB, 'native w')
    nw_knob.setFlag(nuke.INVISIBLE)
    bd.addKnob(nw_knob)
    bd[REF_NATIVE_W_KNOB].setValue(int(native_w))

    nh_knob = nuke.Int_Knob(REF_NATIVE_H_KNOB, 'native h')
    nh_knob.setFlag(nuke.INVISIBLE)
    bd.addKnob(nh_knob)
    bd[REF_NATIVE_H_KNOB].setValue(int(native_h))

    # Native icon for the mini-map.
    _refresh_native_icon(bd)

    # Kick off background mip generation so subsequent zoom-out doesn't
    # stall on the first paint that needs small levels.
    _prewarm_mips(safe_path)

    for n in nuke.allNodes():
        n['selected'].setValue(False)
    bd['selected'].setValue(True)

    return bd


# ---------------------------------------------------------------------------
# Public commands
# ---------------------------------------------------------------------------

def paste_reference():
    if _script_dir_or_none() is None:
        kind, _ = _grab_clipboard_payload()
        if kind is not None:
            nuke.message(
                'NukeRef: please save your Nuke script first.\n\n'
                'Reference images are stored alongside the .nk file.'
            )
            return
        try:
            nuke.nodePaste('%clipboard%')
        except Exception:
            pass
        return

    kind, value = _grab_clipboard_payload()

    if kind == 'image':
        try:
            path = _save_qimage_as_png(value)
        except Exception as err:
            nuke.message('NukeRef: could not save image: {}'.format(err))
            return
        if path is None:
            return
        _make_reference_backdrop(path, source_image=value)
        return

    if kind == 'path':
        _make_reference_backdrop(value)
        return

    try:
        nuke.nodePaste('%clipboard%')
    except Exception:
        pass


def _upgrade_ref_grab_zone(backdrop):
    """Bring an existing ref in line with current refs.

    Bump note_font_size so the header strip is grabbable (it's ungrabbable at
    the old default of 1), and clear any label so the node stays clean -- older
    refs were stamped with the filename as a label.
    """
    try:
        if float(backdrop['note_font_size'].value()) < 20:
            backdrop['note_font_size'].setValue(30)
        if backdrop['label'].value():
            backdrop['label'].setValue('')
    except Exception:
        pass


def refresh_references():
    """Force overlay rebuild + native icon refresh on every ref."""
    _purge_pixmap_cache()
    _PREWARMED_PATHS.clear()
    _ensure_overlays()
    for bd in nuke.allNodes('BackdropNode'):
        if REF_PATH_KNOB in bd.knobs():
            _upgrade_ref_grab_zone(bd)
            _refresh_native_icon(bd)
            try:
                _prewarm_mips(bd[REF_PATH_KNOB].value())
            except Exception:
                pass
    for ov in _OVERLAYS.values():
        if _is_alive(ov):
            ov.update()
    nuke.tprint('[NukeRef] References refreshed.')


def _on_script_load():
    """Re-apply native icons and pre-warm mip caches after a script opens."""
    for bd in nuke.allNodes('BackdropNode'):
        if REF_PATH_KNOB in bd.knobs():
            _upgrade_ref_grab_zone(bd)
            _refresh_native_icon(bd)
            try:
                _prewarm_mips(bd[REF_PATH_KNOB].value())
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

def install():
    global _INSTALL_TIMER, _GEO_TIMER

    menu = nuke.menu('Node Graph')
    for item in ('Paste Reference', 'Refresh References'):
        try:
            menu.removeItem(item)
        except Exception:
            pass

    menu.addCommand(
        'Paste Reference',
        'import nuke_ref; nuke_ref.paste_reference()',
        'ctrl+v',
    )
    menu.addCommand(
        'Refresh References',
        'import nuke_ref; nuke_ref.refresh_references()',
    )

    nuke.addKnobChanged(_on_knob_changed, nodeClass='BackdropNode')
    nuke.addOnScriptLoad(_on_script_load)

    # Node-lifecycle callbacks invalidate the ref-nodes cache, so the next
    # paint sees added/removed refs without scanning the whole graph each
    # frame. We register for BackdropNode only; other classes never have
    # our REF_PATH_KNOB anyway.
    nuke.addOnUserCreate(_invalidate_ref_cache, nodeClass='BackdropNode')
    nuke.addOnCreate(_invalidate_ref_cache, nodeClass='BackdropNode')
    nuke.addOnDestroy(_invalidate_ref_cache, nodeClass='BackdropNode')

    # Bring overlays + DAG event filters up immediately so the first paste
    # works without waiting for the housekeeping timer to tick.
    try:
        _ensure_overlays()
    except Exception as err:
        nuke.tprint('[NukeRef] initial _ensure_overlays failed: {}'.format(err))

    # Slow housekeeping loop. Runs every 2 seconds, far cheaper than the
    # old 30 Hz tick: it only re-walks the widget tree to catch newly
    # opened DAG panels and expires resize-dim timestamps. All real paints
    # are now event-driven via _DagEventFilter.
    if _INSTALL_TIMER is None:
        _INSTALL_TIMER = QTimer()
        _INSTALL_TIMER.setInterval(2000)
        _INSTALL_TIMER.timeout.connect(_slow_cleanup)
        _INSTALL_TIMER.start()

    # Fast, lightweight geometry follower. The overlay is a top-level window
    # now, so it has to chase the DAG when the Nuke window is moved/resized or
    # docking changes -- none of which fire events on the DAG widget itself.
    if _GEO_TIMER is None:
        _GEO_TIMER = QTimer()
        _GEO_TIMER.setInterval(120)
        _GEO_TIMER.timeout.connect(_sync_overlay_geometry)
        _GEO_TIMER.start()

    nuke.tprint('[NukeRef] Installed (Ctrl+V to paste reference).')
