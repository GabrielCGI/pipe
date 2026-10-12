"""Stamps (anchor / wired postage stamps) integration."""

import contextlib
import os
import sys

import nuke

from ..core.config import Config
from .utils import center_under

_UNSET = object()
_stamps_module = _UNSET


def _import_stamps():
    if not Config.ENABLE_STAMPS:
        print("[StampsIntegration] Stamps integration disabled in config")
        return None
    module = sys.modules.get("stamps")
    if module is not None:
        return module
    try:
        from stamps import stamps as module  # packaged layout
        return module
    except ImportError:
        pass
    for path in Config.STAMPS_PATHS:
        if not os.path.exists(path):
            continue
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            import stamps as module
            return module
        except ImportError:
            continue
    print("[StampsIntegration] Stamps module not found - stamp creation will be skipped")
    return None


def stamps_module():
    """The Stamps module, imported lazily (it may register after us)."""
    global _stamps_module
    if _stamps_module is _UNSET:
        _stamps_module = _import_stamps()
    return _stamps_module


@contextlib.contextmanager
def _isolated_selection(*selected):
    """Stamps acts on Nuke's selection: select only `selected` for the
    duration, then restore the artist's selection."""
    original = nuke.selectedNodes()
    for node in original:
        node.setSelected(False)
    for node in selected:
        node.setSelected(True)
    try:
        yield
    finally:
        for node in selected:
            node.setSelected(False)
        for node in original:
            node.setSelected(True)


def create_stamp_pair(source, title: str, anchor_offset: int = Config.ANCHOR_OFFSET) -> list:
    """Anchor under `source` + wired stamp under the anchor.
    Returns the created nodes ([anchor, wired], [anchor] or [])."""
    stamps = stamps_module()
    if stamps is None:
        print("[NukeNodeBuilder] Stamps not available, skipping stamp creation")
        return []
    try:
        with _isolated_selection(source):
            anchor = stamps.anchor(title=title)
            if anchor is not None:
                anchor.setInput(0, source)
                center_under(anchor, source, source.ypos() + anchor_offset)
        if anchor is None:
            print(f"[NukeNodeBuilder] Failed to create anchor stamp: {title}")
            return []

        with _isolated_selection():
            wired = stamps.wired(anchor=anchor) if hasattr(stamps, "wired") else None
            if wired:
                center_under(wired, anchor, anchor.ypos() + Config.WIRED_OFFSET)
        if not wired:
            print(f"[NukeNodeBuilder] Created anchor stamp only: {title}")
            return [anchor]
        print(f"[NukeNodeBuilder] Created anchor + wired stamp: {title}")
        return [anchor, wired]
    except Exception as e:
        print(f"[NukeNodeBuilder] Error creating stamp {title}: {e}")
        return []


def anchor_title(source):
    """Title of the anchor stamp fed by `source`, None without one."""
    try:
        for node in source.dependent(nuke.INPUTS, forceEvaluate=False):
            identifier, title = node.knob("identifier"), node.knob("title")
            if identifier is not None and title is not None and identifier.value() == "anchor":
                return title.value() or None
    except Exception:
        pass
    return None


@contextlib.contextmanager
def _suppress_nuke_message():
    """Route nuke.message to the console — the Stamps plugin pops
    "No Anchor Stamps with title ... found" from its reconnect buttons."""
    original = nuke.message
    nuke.message = lambda msg: print(f"[reconnect_stamps] suppressed nuke.message: {msg}")
    try:
        yield
    finally:
        nuke.message = original


def reconnect_postage_stamps(silent: bool = False):
    """Press `reconnect_by_title_similar` on every PostageStamp so existing
    wired stamps latch onto freshly created anchors of the same title.

    silent: console report only (no popups). Returns (executed, skipped)."""
    postage_stamps = nuke.allNodes("PostageStamp")
    if not postage_stamps:
        if not silent:
            nuke.message("No PostageStamp found in the script.")
        return [], []

    executed, skipped = [], []
    for node in postage_stamps:
        knob = node.knob("reconnect_by_title_similar")
        if knob is None:
            skipped.append(f"{node.name()} (no knob)")
            continue
        try:
            if silent:
                with _suppress_nuke_message():
                    knob.execute()
            else:
                knob.execute()
            executed.append(node.name())
        except Exception as e:
            nuke.warning(f"Error on '{node.name()}': {e}")
            skipped.append(f"{node.name()} (error: {e})")

    print(f"[reconnect_stamps] {len(executed)} executed, {len(skipped)} skipped "
          f"(total {len(postage_stamps)})")
    if not silent:
        lines = ["=== Reconnect PostageStamps ===", "",
                 f"Total PostageStamps : {len(postage_stamps)}",
                 f"Executed            : {len(executed)}",
                 f"Skipped             : {len(skipped)}"]
        if executed:
            lines += ["", "Executed:"] + [f"  - {n}" for n in executed]
        if skipped:
            lines += ["", "Skipped:"] + [f"  - {n}" for n in skipped]
        nuke.message("\n".join(lines))
    return executed, skipped
