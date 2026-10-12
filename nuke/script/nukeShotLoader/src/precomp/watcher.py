"""GUI only: re-sync the precomp switches shortly after the artist edits a
node upstream of a precomp (or rewires the graph), so a switch reading a
stale cache flips to live right away. Runs on the main thread from Qt's
event loop, never during a render or an expression evaluation."""

import nuke

from . import engine, spec
from .hashing import IGNORED_KNOBS

_DEBOUNCE_MS = 400
# Knob changes that never alter an image: what the content hash ignores,
# plus panel events.
_IGNORED = IGNORED_KNOBS | {"showPanel", "hidePanel", "reload"}

_timer = None
_installed = False


def install():
    global _installed
    if _installed or not nuke.GUI:
        return
    nuke.addKnobChanged(_on_knob_changed)
    nuke.addOnScriptLoad(schedule)
    _installed = True


def schedule(delay_ms: int = _DEBOUNCE_MS):
    global _timer
    from ..ui.qt import QtCore
    if _timer is None:
        _timer = QtCore.QTimer()
        _timer.setSingleShot(True)
        _timer.timeout.connect(_run)
    _timer.start(delay_ms)


def _on_knob_changed():
    if engine.is_busy():
        return
    try:
        knob, node = nuke.thisKnob(), nuke.thisNode()
        if knob is None or node is None or knob.name() in _IGNORED:
            return
        if knob.name() in ("inputChange", spec.LIVE_FROM) or id(node) in engine.upstream_ids():
            schedule()
    except Exception:
        pass  # a callback must never break the artist's edit


def _run():
    if nuke.executing() or engine.is_busy():   # rendering, or a submission in progress
        schedule(2000)
        return
    try:
        engine.sync()
    except Exception as e:
        print(f"[precomp] background sync failed: {e}")
