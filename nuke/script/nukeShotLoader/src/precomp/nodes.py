"""Precomp nodes: discovery, v2 switch construction and routing, v1 upgrade.

v2 layout (the switch's input 0 is the PrecompWrite, which passes its
input through since `reading` is off):

    upstream -> PrecompWrite -> SW_Precomp -> downstream
                                  ├─ Input ────────┐
                                  ├─ CacheRead ─── Switch (which: 0 live, 1 cache) -> Output
"""

import os
import re
from typing import Iterator, List, Tuple

import nuke

from ..scene.utils import set_knob, undo_group
from . import spec
from .hashing import is_precomp_write

FrameRange = Tuple[int, int]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def iter_precomp_writes() -> Iterator:
    return (n for n in nuke.allNodes("Write", recurseGroups=True) if is_precomp_write(n))


def is_legacy_write(write) -> bool:
    return write.knob(spec.WRITE_MARKER) is None


def _dependents(node) -> List:
    try:
        return list(node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False))
    except Exception:
        return []


def find_switch(write):
    """(switch, is_legacy) fed by `write` (through Dots), or (None, False).
    Only our own switch groups count (v2 marker / v1 `which_custom` knob):
    an artist's plain Switch downstream of a precomp is never touched."""
    pending, seen = [write], set()
    while pending:
        node = pending.pop()
        for dep in _dependents(node):
            if id(dep) in seen:
                continue
            seen.add(id(dep))
            if dep.knob(spec.SWITCH_MARKER) is not None:
                return dep, False
            if dep.knob(spec.LEGACY_WHICH) is not None:
                return dep, True
            if dep.Class() == "Dot":
                pending.append(dep)
    return None, False


def _hidden_knob(write, name, knob_class):
    if write.knob(name) is None:
        knob = knob_class(name, name)
        knob.setFlag(nuke.INVISIBLE)
        write.addKnob(knob)
    return write[name]


def set_live_from(write, version: int):
    """Mark the version "Force Live" moved the precomp to (see spec.LIVE_FROM)."""
    _hidden_knob(write, spec.LIVE_FROM, nuke.Int_Knob).setValue(int(version))


def set_force_undo(write, text: str):
    _hidden_knob(write, spec.FORCE_UNDO, nuke.String_Knob).setValue(text)


def frame_range(write) -> FrameRange:
    """Frames the Write renders: its own range with `use_limit`, else the script's."""
    use_limit = write.knob("use_limit")
    if use_limit is not None and use_limit.value():
        return int(write["first"].value()), int(write["last"].value())
    root = nuke.root()
    return int(root["first_frame"].value()), int(root["last_frame"].value())


def version_root(write) -> str:
    """Folder holding the v### folders (the `folderpath` knob of the Prism template)."""
    knob = write.knob("folderpath")
    folder = knob.value() if knob is not None else ""
    if not folder:
        folder = os.path.dirname(os.path.dirname(render_path(write)))
    return folder.replace("\\", "/").rstrip("/")


def render_path(write) -> str:
    knob = write.knob("renderpath") or write.knob("file")
    return (knob.value() or "").replace("\\", "/")


# ---------------------------------------------------------------------------
# Switch
# ---------------------------------------------------------------------------

def build_switch_internals(group):
    """(Re)create the switch group's content and knobs."""
    group.begin()
    try:
        for node in list(nuke.allNodes()):
            nuke.delete(node)
        live = nuke.nodes.Input(name=spec.INNER_INPUT, xpos=0, ypos=0)
        read = nuke.nodes.Read(name=spec.CACHE_READ, xpos=-150, ypos=0)
        read["disable"].setValue(True)
        read["on_error"].setValue("error")
        switch = nuke.nodes.Switch(name=spec.INNER_SWITCH, xpos=0, ypos=100)
        switch.setInput(spec.CACHE, read)
        switch.setInput(spec.LIVE, live)
        switch["which"].setExpression(f"parent.{spec.WHICH}")
        nuke.nodes.Output(name=spec.INNER_OUTPUT, xpos=0, ypos=200).setInput(0, switch)
    finally:
        group.end()

    if group.knob("precomp") is None:
        group.addKnob(nuke.Tab_Knob("precomp", "Precomp"))
    if group.knob(spec.SWITCH_MARKER) is None:
        marker = nuke.Int_Knob(spec.SWITCH_MARKER, "")
        marker.setFlag(nuke.INVISIBLE)
        group.addKnob(marker)
    group[spec.SWITCH_MARKER].setValue(spec.SCHEMA)
    if group.knob(spec.WHICH) is None:
        which = nuke.Int_Knob(spec.WHICH, "which")
        which.setTooltip("0 = live upstream, 1 = cached render. Set by the Render Manager.")
        group.addKnob(which)
    group[spec.WHICH].setValue(spec.LIVE)
    if group.knob(spec.STATUS_KNOB) is None:
        group.addKnob(nuke.Text_Knob(spec.STATUS_KNOB, "status", "Live"))
    if group.knob(spec.CACHE_FILE_KNOB) is None:
        cache_file = nuke.String_Knob(spec.CACHE_FILE_KNOB, "cache")
        cache_file.setEnabled(False)
        group.addKnob(cache_file)


def route(switch, write, cache) -> bool:
    """Point the switch at `cache` (a manifest.CacheEntry) or at the live
    upstream (None). Only knobs whose value changes are touched. Returns
    True when the routing changed."""
    read = switch.node(spec.CACHE_READ)
    which = spec.CACHE if cache is not None else spec.LIVE
    changed = set_knob(switch, spec.WHICH, which)
    path = _nuke_sequence_path(cache.path) if cache is not None else ""
    if read is not None:
        if cache is not None:
            file_changed = set_knob(read, "file", path)
            for name, value in (("first", cache.first), ("last", cache.last),
                                ("origfirst", cache.first), ("origlast", cache.last)):
                set_knob(read, name, value)
            _match_colorspace(read, write)
            enabled = set_knob(read, "disable", False)
            if file_changed or enabled or changed:
                read["reload"].execute()  # drop "file missing" errors cached by the Read
            changed |= file_changed
        else:
            set_knob(read, "disable", True)
    set_knob(switch, spec.CACHE_FILE_KNOB, path)
    return changed


def _nuke_sequence_path(path: str) -> str:
    """'x.####.exr' -> 'x.%04d.exr', the form a Read's file knob stores
    (comparing against the '#' form would look like a change every time)."""
    return re.sub(r"#+", lambda m: f"%0{len(m.group(0))}d", path)


def set_status(switch, label: str, detail: str, cached: bool):
    """DAG label + tile color + status line. Callers pass state-level text
    (no frame counts) so the node only changes on real transitions."""
    set_knob(switch, "label", label)
    set_knob(switch, "tile_color", spec.TILE_COLORS["cached" if cached else "live"])
    set_knob(switch, spec.STATUS_KNOB, f"{label} — {detail}" if detail else label)


def _match_colorspace(read, write):
    """Read the cache back the way the Write encoded it."""
    raw = bool(write["raw"].value()) if write.knob("raw") is not None else False
    set_knob(read, "raw", raw)
    if not raw and write.knob("colorspace") is not None:
        try:
            set_knob(read, "colorspace", write["colorspace"].value())
        except Exception:
            pass


# ---------------------------------------------------------------------------
# v1 -> v2 upgrade
# ---------------------------------------------------------------------------

def _references_legacy(script: str) -> bool:
    return any(name in (script or "") for name in spec.LEGACY_SCRIPTS)


def upgrade_write(write):
    """Turn a v1 PrecompWrite into a v2 one: no read-back, no render hooks,
    the Shot Loader's Prism tab (upgrade_prism_tab)."""
    set_knob(write, "reading", False)
    set_knob(write, "postage_stamp", False)  # the thumbnail would compute the whole upstream
    for hook in ("beforeRender", "afterRender"):
        knob = write.knob(hook)
        if knob is not None and _references_legacy(knob.value()):
            knob.setValue("")
    for name in ("hasher", "go_to_latest"):
        knob = write.knob(name)
        if knob is not None:
            write.removeKnob(knob)
    if write.knob("startRender") is not None:
        write["startRender"].setValue(spec.RENDER_BUTTON_SCRIPT)
    upgrade_prism_tab(write)
    if write.knob(spec.WRITE_MARKER) is None:
        marker = nuke.Int_Knob(spec.WRITE_MARKER, "")
        marker.setFlag(nuke.INVISIBLE)
        write.addKnob(marker)
    write[spec.WRITE_MARKER].setValue(spec.SCHEMA)


def upgrade_switch(switch, write):
    """Rebuild a v1 switch group in place (name, position and downstream
    wiring kept) and delete the Dot chain that fed its live input."""
    former_inputs = [switch.input(i) for i in range(switch.maxInputs())]
    # Disconnected before the rebuild: Nuke keeps a group input that is still
    # connected when its Input node goes away (the v1 second input stayed,
    # empty, on the upgraded switch).
    for i in range(len(former_inputs)):
        switch.setInput(i, None)
    for name in (spec.LEGACY_WHICH, "switch"):  # v1 knob and its tab
        knob = switch.knob(name)
        if knob is not None:
            switch.removeKnob(knob)
    build_switch_internals(switch)
    switch.setInput(0, write)
    for node in former_inputs:
        if node is not None and node is not write:
            _delete_orphan_dots(node)
    return switch


def _delete_orphan_dots(node):
    while node is not None and node.Class() == "Dot" and not _dependents(node):
        upstream = node.input(0)
        nuke.delete(node)
        node = upstream


def upgrade_compo_hooks():
    """Remove v1 render hooks from non-precomp Writes (the compo Write)."""
    changed = []
    for write in nuke.allNodes("Write", recurseGroups=True):
        if is_precomp_write(write):
            continue
        before, after = write.knob("beforeRender"), write.knob("afterRender")
        if before is not None and _references_legacy(before.value()):
            before.setValue(spec.PRISM_COMPO_BEFORE_RENDER)
            changed.append(write.fullName())
        if after is not None and _references_legacy(after.value()):
            after.setValue(spec.PRISM_COMPO_AFTER_RENDER)
            changed.append(write.fullName())
    return sorted(set(changed))


def is_compo_write(node) -> bool:
    """A Compo Write, as the Render Manager finds them ('Compo' in the name)."""
    try:
        return node.Class() == "Write" and not is_precomp_write(node) and "Compo" in node.name()
    except Exception:
        return False


def upgrade_prism_tabs() -> List[str]:
    """upgrade_prism_tab() on the v2 PrecompWrites and the Compo Writes (v1
    PrecompWrites are left to upgrade_scene()). Returns the Writes changed."""
    changed = []
    for write in nuke.allNodes("Write", recurseGroups=True):
        precomp = is_precomp_write(write)
        if (precomp and is_legacy_write(write)) or not (precomp or is_compo_write(write)):
            continue
        if upgrade_prism_tab(write):
            changed.append(write.fullName())
    return sorted(changed)


def upgrade_prism_tab(write) -> bool:
    """The Shot Loader's Prism tab on one Write (src/ui/write_render.py):
    Render (Submit Job ticked: Deadline, unticked: local) and Render as
    previous version... (always local), both shown with the Submit Job box,
    the knobs it doesn't use hidden (values kept), and the read-only info
    block at the bottom (version, output path, Open In Explorer). Only the
    buttons this tool knows are replaced: a custom script stays. True when
    something changed."""
    changed = _add_info_block(write) | _add_prism_after_render(write)
    for name, former, script in (
            ("startRender", spec.FORMER_RENDER_BUTTONS, spec.RENDER_BUTTON_SCRIPT),
            ("startRenderPrevVersion", spec.FORMER_PREVIOUS_VERSION_BUTTONS, spec.PREVIOUS_VERSION_BUTTON_SCRIPT)):
        knob = write.knob(name)
        if knob is not None and (knob.value() or "").strip() in former:
            knob.setValue(script)
            changed = True
    previous = write.knob("startRenderPrevVersion")
    shown = [write.knob(spec.SUBMIT_JOB)]
    if previous is not None and previous.value() == spec.PREVIOUS_VERSION_BUTTON_SCRIPT:
        shown.append(previous)
    for knob in shown:
        changed |= _set_hidden(knob, False)
    tab = _prism_tab_knobs(write)
    for knob in tab:
        if knob.name() in spec.HIDDEN_TAB_KNOBS:
            changed |= _set_hidden(knob, True)
    # A divider left right above another one once the knobs between are hidden.
    visible = [k for k in tab if not k.getFlag(nuke.INVISIBLE)]
    for knob, following in zip(visible, visible[1:]):
        if _is_divider(knob) and _is_divider(following):
            changed |= _set_hidden(knob, True)
    return changed


def _add_info_block(write) -> bool:
    """Version (locked Int following the output: the precomp's `versions`,
    the version folder of a Compo Write's Prism fileName), output path (live
    label, src/ui/knob_widgets.py) and Open In Explorer, at the bottom of the
    Prism tab. Knobs can only be added at the end of a node: skipped (False)
    when the Prism tab isn't the Write's last tab, or when already there."""
    shown = write.knob(spec.VERSION_DISPLAY)
    if shown is not None:   # typed over before it was locked: follows the output again
        if shown.hasExpression():
            return False
        shown.setExpression(_version_expression(write))
        return True
    if write.knob("tab_prism") is None:
        return False
    tabs = [k.name() for k in write.allKnobs() if k.Class() == "Tab_Knob"]
    if tabs[-1:] != ["tab_prism"]:
        print(f"[precomp] {write.fullName()}: Prism tab not the last one, version / path / Open In Explorer not added")
        return False
    version = nuke.Int_Knob(spec.VERSION_DISPLAY, "version")
    output = nuke.PyCustom_Knob(spec.OUTPUT_DISPLAY, "filepath", spec.OUTPUT_DISPLAY_COMMAND)
    button = nuke.PyScript_Knob(spec.OPEN_BUTTON, "Open In Explorer", spec.OPEN_BUTTON_SCRIPT)
    for knob in (nuke.Text_Knob(spec.INFO_DIVIDER, ""), version, output, button):
        write.addKnob(knob)
    version.setExpression(_version_expression(write))
    # Locked but readable (DISABLED greys it out). Not saved with the script:
    # commands.lock_version_display sets it again whenever the panel opens.
    version.setFlag(nuke.READ_ONLY)
    for knob in (output, button):
        knob.setFlag(nuke.STARTLINE)
    return True


def _version_expression(write) -> str:
    return spec.PRECOMP_VERSION_EXPRESSION if is_precomp_write(write) else spec.COMPO_VERSION_EXPRESSION


def _add_prism_after_render(write) -> bool:
    """A Compo Write with Prism's beforeRender (it marks the Write
    "rendering") and no afterRender gets Prism's (it clears the mark)."""
    if is_precomp_write(write):
        return False
    before, after = write.knob("beforeRender"), write.knob("afterRender")
    if before is None or after is None or before.value() != spec.PRISM_COMPO_BEFORE_RENDER or after.value():
        return False
    after.setValue(spec.PRISM_COMPO_AFTER_RENDER)
    return True


def _prism_tab_knobs(write) -> List:
    knobs, inside = [], False
    for knob in write.allKnobs():
        if knob.Class() == "Tab_Knob":
            inside = knob.name() == "tab_prism"
        elif inside:
            knobs.append(knob)
    return knobs


def _is_divider(knob) -> bool:
    return knob.Class() == "Text_Knob" and not knob.name()


def _set_hidden(knob, hidden: bool) -> bool:
    """True when the knob's visibility changed."""
    if knob is None or bool(knob.getFlag(nuke.INVISIBLE)) == hidden:
        return False
    if hidden:
        knob.setFlag(nuke.INVISIBLE)
    else:
        knob.clearFlag(nuke.INVISIBLE)
    return True


def upgrade_scene() -> List[str]:
    """Upgrade every v1 precomp of the script, and the Prism tab of the
    Writes. Returns a report."""
    report = []
    with undo_group("Upgrade precomps"):
        for write in list(iter_precomp_writes()):
            switch, legacy = find_switch(write)
            if not is_legacy_write(write) and not legacy:
                continue
            upgrade_write(write)
            if legacy and switch.Class() == "Group":
                switch = upgrade_switch(switch, write)
                report.append(f"{write.fullName()} -> {switch.fullName()}")
            elif legacy:
                report.append(f"{write.fullName()}: v1 switch {switch.fullName()} is not a group, "
                              "left as is (rebuild it from the WritePrecomp template)")
            elif switch is None:
                report.append(f"{write.fullName()}: no switch (plain precomp write)")
            else:
                report.append(f"{write.fullName()} -> {switch.fullName()}")
        report += [f"{name}: v1 render hooks removed" for name in upgrade_compo_hooks()]
        report += [f"{name}: Shot Loader Prism tab" for name in upgrade_prism_tabs()]
    return report
