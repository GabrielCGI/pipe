"""Small helpers around the Nuke API shared by the scene modules."""

import contextlib
from typing import Iterable, Optional, Set, Tuple

import nuke

_no_undo_depth = 0
_undo_group_depth = 0


@contextlib.contextmanager
def no_undo():
    """Keep automatic changes (routing, status labels, render order) out of
    the artist's undo history: otherwise Ctrl+Z could revert our change
    instead of the artist's own edit. Re-entrant."""
    global _no_undo_depth
    if _no_undo_depth == 0:
        nuke.Undo.disable()
    _no_undo_depth += 1
    try:
        yield
    finally:
        _no_undo_depth -= 1
        if _no_undo_depth == 0:
            nuke.Undo.enable()


@contextlib.contextmanager
def undo_group(name: str):
    """One Ctrl+Z for a whole artist action (load, update, duplicate,
    upgrade, force live...). Nested groups merge into the outermost one."""
    global _undo_group_depth
    undo = None
    if _undo_group_depth == 0:
        undo = nuke.Undo()
        undo.begin(name)
    _undo_group_depth += 1
    try:
        yield
    finally:
        _undo_group_depth -= 1
        if undo is not None:
            undo.end()


_popup_timers = []   # keeps the GUI timers alive until they stop


@contextlib.contextmanager
def silent_popups(label: str, linger_ms: int = 2000):
    """Run Nuke code that reports through popups, without them: nuke.message
    goes to the console, nuke.ask answers yes, and in the GUI the message
    boxes Nuke itself opens (e.g. the Camera3 reload_link confirmation) get
    their default answer right away — text logged — during the block and
    `linger_ms` after it. Any other dialog (ours, the Deadline submitter)
    is left alone."""
    original_message, original_ask = nuke.message, getattr(nuke, "ask", None)
    nuke.message = lambda msg: print(f"[ShotAssetLoader] {label}: {msg}")
    nuke.ask = lambda msg: print(f"[ShotAssetLoader] {label}: '{msg}' answered yes") or True
    timer = _start_popup_closer(label) if getattr(nuke, "GUI", False) else None
    try:
        yield
    finally:
        nuke.message, nuke.ask = original_message, original_ask
        if timer is not None:
            from ..ui.qt import QtCore  # GUI only: scene stays importable without Qt
            QtCore.QTimer.singleShot(linger_ms, lambda: _stop_popup_closer(timer))


_NUKE_POPUP_TITLE = "Nuke"


def _start_popup_closer(label):
    from ..ui.qt import QtCore, QtWidgets
    app = QtWidgets.QApplication.instance()
    already_open = app.activeModalWidget()

    def close_popup():
        widget = app.activeModalWidget()
        if widget is None or widget is already_open:
            return
        # Nuke's own popups are QMessageBoxes titled "Nuke".
        if not isinstance(widget, QtWidgets.QMessageBox) or widget.windowTitle() != _NUKE_POPUP_TITLE:
            return
        print(f"[ShotAssetLoader] {label}: popup closed automatically: {widget.text()}")
        default = widget.defaultButton()
        if default is not None:
            default.click()
        else:
            widget.accept()

    timer = QtCore.QTimer()
    timer.setInterval(30)  # fires inside the dialog's own event loop too
    timer.timeout.connect(close_popup)
    timer.start()
    _popup_timers.append(timer)
    return timer


def _stop_popup_closer(timer):
    timer.stop()
    if timer in _popup_timers:
        _popup_timers.remove(timer)


def script_path() -> Optional[str]:
    """Saved script path, None for an unsaved script (root name "Root")."""
    try:
        name = nuke.root().name()
    except Exception:
        return None
    return None if not name or name == "Root" else name


def scene_frame_range() -> Optional[Tuple[int, int]]:
    try:
        root = nuke.root()
        return int(root['first_frame'].value()), int(root['last_frame'].value())
    except Exception:
        return None


def scene_fps() -> Optional[float]:
    try:
        return float(nuke.root()['fps'].value())
    except Exception:
        return None


def scene_format() -> Optional[Tuple[int, int]]:
    try:
        fmt = nuke.root()['format'].value()
        return (fmt.width(), fmt.height()) if fmt is not None else None
    except Exception:
        return None


def knob_value(node, name: str, default=None):
    knob = node.knob(name)
    if knob is None:
        return default
    try:
        return knob.value()
    except Exception:
        return default


def set_knob(node, name: str, value) -> bool:
    """Set a knob only when it exists and differs — avoids dirtying the
    script (and waking knobChanged callbacks) on every auto-refresh."""
    knob = node.knob(name)
    if knob is None:
        return False
    if knob.value() == value:
        return False
    knob.setValue(value)
    return True


def prism_core():
    """Prism's `pcore` global, None when Prism isn't loaded (vanilla Nuke)."""
    import __main__
    return getattr(__main__, "pcore", None)


def execute_button(node, name: str, log_prefix: str = "[ShotAssetLoader]", warn_missing=False) -> bool:
    """Press a Python button knob; failures are logged, never raised."""
    knob = node.knob(name)
    if knob is None:
        if warn_missing:
            print(f"{log_prefix} No '{name}' knob on {node.name()} — skipping")
        return False
    try:
        knob.execute()
        print(f"{log_prefix} {name} on {node.name()}")
        return True
    except Exception as e:
        print(f"{log_prefix} {name} failed on {node.name()}: {e}")
        return False


def upstream_nodes(root) -> Set:
    """Every node strictly upstream of `root` that its render goes through
    (input traversal). A disabled node only passes its input 0 through (B of
    a Merge): what feeds its other inputs is out of the stream."""
    if root is None:
        return set()
    seen = set()
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            count = current.inputs()
        except Exception:
            continue
        if current is not root and _disabled(current):
            count = min(count, 1)
        for i in range(count):
            try:
                node = current.input(i)
            except Exception:
                continue
            if node is not None and node not in seen:
                seen.add(node)
                stack.append(node)
    return seen


def _disabled(node) -> bool:
    try:
        knob = node.knob("disable")
        return knob is not None and bool(knob.value())
    except Exception:
        return False


def select_only(nodes: Iterable) -> list:
    """Deselect the whole script (groups included), select `nodes`."""
    for node in nuke.allNodes(recurseGroups=True):
        try:
            node.setSelected(False)
        except Exception:
            pass
    names = []
    for node in nodes:
        try:
            node.setSelected(True)
            names.append(node.name())
        except Exception:
            pass
    return names


def center_under(node, reference, y: int):
    """Place `node` horizontally centred under `reference` at height `y`
    (plain xpos alignment is off whenever the two widths differ)."""
    center_x = reference.xpos() + reference.screenWidth() / 2
    node.setXYpos(int(center_x - node.screenWidth() / 2), y)
