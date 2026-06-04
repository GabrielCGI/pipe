"""
EXR Layer Builder — Group node pour definir les layers d'export Photoshop.

Photoshop lit les layers EXR par ordre alphabetique. Ce tool cree un Group
avec des AddChannels internes, nommes _###_NomDescriptif pour controler
l'ordre d'affichage dans PS.

Prerequis : le dossier contenant ce module doit etre dans le nuke plugin path
(via init.py / menu.py ou nuke.pluginAddPath).

Usage dans le Script Editor Nuke :
    import export_layers
    export_layers.run()
"""

import nuke
import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Prefixes principaux (pas de 10, descendant = haut du stack PS en premier)
MAIN_PREFIXES = list(range(100, 0, -10))  # [100, 90, 80, ..., 10]

PREFIX_STRINGS = ["_{:03d}_".format(v) for v in MAIN_PREFIXES]
# ["_100_", "_090_", "_080_", ..., "_010_"]

PRESET_NAMES = ["BG", "FG", "MG", "CHARS", "VOLUME", "Custom"]

DEFAULT_NUM_LAYERS = 3

# Default presets for the first layers
_DEFAULT_PRESETS = ["BG", "FG", "MG"]

# Common preamble for callback scripts: import + hot-reload
_SCRIPT_PREAMBLE = (
    "import importlib, export_layers; importlib.reload(export_layers)\n"
)

# knobChanged script stored on the Group node — delegates to module function
KNOB_CHANGED_SCRIPT = (
    _SCRIPT_PREAMBLE
    + "export_layers._on_knob_changed(nuke.thisNode(), nuke.thisKnob())\n"
)

BUILD_SCRIPT = (
    _SCRIPT_PREAMBLE
    + "export_layers._rebuild_from_ui(nuke.thisNode())"
)

ADD_SCRIPT = (
    _SCRIPT_PREAMBLE
    + "export_layers._add_one_layer(nuke.thisNode())"
)

# Template for per-layer delete button (index replaced at creation time)
_DELETE_SCRIPT_TPL = (
    _SCRIPT_PREAMBLE
    + "export_layers._delete_layer(nuke.thisNode(), {idx})"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_prefix(value):
    """Extract the actual prefix from a dropdown value.

    '_100_'          → '_100_'
    '_100_/_091_'    → '_091_'
    """
    if "/" in value:
        return value.split("/")[-1]
    return value


def _get_full_layer_name(grp, index):
    """Return assembled layer name like '_100_BG' for layer at index."""
    prefix = _extract_prefix(grp["prefix_{}".format(index)].value())
    name = grp["name_{}".format(index)].value().strip()
    return "{}{}".format(prefix, name)


def _get_current_layer_count(grp):
    """Return how many layers are currently defined."""
    try:
        return int(grp["_layer_count"].value())
    except (ValueError, NameError):
        return 0


def _collect_layer_defs(grp, count):
    """Collect current (prefix, preset, name) tuples for all layers."""
    defs = []
    for i in range(count):
        try:
            prefix = grp["prefix_{}".format(i)].value()
            preset = grp["preset_{}".format(i)].value()
            name = grp["name_{}".format(i)].value()
            defs.append((prefix, preset, name))
        except NameError:
            break
    return defs


def _prefix_to_int(prefix_str):
    """Extract integer from a prefix string like '_091_' → 91."""
    m = re.match(r"_(\d+)_", prefix_str)
    return int(m.group(1)) if m else 0


def _used_prefix_values(grp, count):
    """Return set of integer prefix values currently in use."""
    used = set()
    for i in range(count):
        try:
            val = _extract_prefix(grp["prefix_{}".format(i)].value())
            used.add(_prefix_to_int(val))
        except NameError:
            pass
    return used


def _int_to_prefix_menu(v):
    """Convert integer to dropdown menu value with submenu for non-round numbers.

    100 → '_100_'       (top-level)
    91  → '_100_/_091_'  (submenu under _100_)
    """
    if v % 10 == 0:
        return "_{:03d}_".format(v)
    # Find parent decade (next higher round number)
    parent = ((v // 10) + 1) * 10
    return "_{:03d}_/_{:03d}_".format(parent, v)


def _find_next_available_prefix(grp, count):
    """Find first main prefix not already used, or generate intercalated."""
    used = _used_prefix_values(grp, count)
    for v in MAIN_PREFIXES:
        if v not in used:
            return "_{:03d}_".format(v)
    # All main prefixes used — find an intercalated slot
    for v in range(99, 0, -1):
        if v not in used:
            return _int_to_prefix_menu(v)
    return "_001_"


def _build_prefix_menu_tcl():
    """Build hierarchical prefix dropdown as a TCL values string.

    Uses the Nuke cascading menu syntax (parent/child) for addUserKnob {68}.
    Structure:
        _100_
        _100_/_099_  (submenu under _100_)
        ...
        _100_/_091_
        _090_
        _090_/_089_
        ...
    """
    items = []
    for tens in range(100, 0, -10):
        items.append("_{:03d}_".format(tens))
        for unit in range(tens - 1, max(tens - 10, 0), -1):
            items.append("_{:03d}_/_{:03d}_".format(tens, unit))
    return " ".join(items)


def _check_duplicates(grp):
    """Check for duplicate layer names, update status knob."""
    count = _get_current_layer_count(grp)
    names = []
    for i in range(count):
        name = grp["name_{}".format(i)].value().strip()
        if not name:
            continue
        names.append(_get_full_layer_name(grp, i))
    seen = set()
    dupes = set()
    for n in names:
        if n in seen:
            dupes.add(n)
        seen.add(n)
    try:
        if dupes:
            grp["status"].setValue(
                '<font color="red">Duplicates : {}</font>'.format(", ".join(sorted(dupes)))
            )
        else:
            grp["status"].setValue(
                '<font color="green">OK — {} layers</font>'.format(len(names))
            )
    except NameError:
        pass


# ---------------------------------------------------------------------------
# Knob management
# ---------------------------------------------------------------------------

def _add_layer_knob_rows(grp, count, start_index=0, defs=None):
    """Add per-layer knob rows to the Group.

    Rows are displayed in reverse order (highest index = top of UI, lowest = bottom)
    to mirror the Photoshop layer stack: _100_ at bottom, _080_ at top.
    """
    # Build rows top-to-bottom = highest index first
    for i in reversed(range(start_index, start_index + count)):
        rel = i - start_index  # relative index into defs

        # Determine defaults
        if defs and rel < len(defs):
            def_prefix, def_preset, def_name = defs[rel]
        else:
            def_prefix = PREFIX_STRINGS[i] if i < len(PREFIX_STRINGS) else PREFIX_STRINGS[-1]
            def_preset = _DEFAULT_PRESETS[i] if i < len(_DEFAULT_PRESETS) else "Custom"
            def_name = def_preset if def_preset != "Custom" else ""

        # Layer header
        header = nuke.Text_Knob("layer_header_{}".format(i), "", "<b>Layer {}</b>".format(i + 1))
        grp.addKnob(header)

        # Prefix dropdown (cascading menu via TCL addUserKnob)
        prefix_values_str = _build_prefix_menu_tcl()
        tcl_cmd = 'addUserKnob {{68 prefix_{idx} l "" M {{{vals}}}}}'.format(
            idx=i, vals=prefix_values_str)
        nuke.tcl('in {} {{{}}}'.format(grp.fullName(), tcl_cmd))
        grp["prefix_{}".format(i)].clearFlag(nuke.STARTLINE)
        if def_prefix:
            try:
                grp["prefix_{}".format(i)].setValue(def_prefix)
            except (RuntimeError, ValueError):
                pass

        # Preset dropdown
        enum_preset = nuke.Enumeration_Knob("preset_{}".format(i), "", PRESET_NAMES)
        enum_preset.clearFlag(nuke.STARTLINE)
        if def_preset in PRESET_NAMES:
            enum_preset.setValue(def_preset)
        grp.addKnob(enum_preset)

        # Name field
        name_knob = nuke.String_Knob("name_{}".format(i), "", def_name)
        name_knob.clearFlag(nuke.STARTLINE)
        grp.addKnob(name_knob)

        # Preview (read-only)
        preview_val = "{}{}".format(_extract_prefix(def_prefix), def_name)
        preview = nuke.Text_Knob("layername_{}".format(i), "", "  <b>{}</b>".format(preview_val))
        preview.clearFlag(nuke.STARTLINE)
        grp.addKnob(preview)

        # Delete button
        del_btn = nuke.PyScript_Knob(
            "delete_{}".format(i), "X", _DELETE_SCRIPT_TPL.format(idx=i))
        del_btn.clearFlag(nuke.STARTLINE)
        grp.addKnob(del_btn)


def _remove_layer_knobs(grp, from_idx, to_idx):
    """Remove all per-layer knobs for indices [from_idx, to_idx)."""
    suffixes = ["layer_header", "prefix", "preset", "name", "layername", "delete"]
    for i in range(from_idx, to_idx):
        for s in suffixes:
            knob_name = "{}_{}".format(s, i)
            try:
                grp.removeKnob(grp[knob_name])
            except (NameError, ValueError):
                pass


def _remove_bottom_knobs(grp):
    """Remove the bottom section knobs (divider, buttons, status)."""
    for name in ("divider2", "add_layer_btn", "status"):
        try:
            grp.removeKnob(grp[name])
        except (NameError, ValueError):
            pass


def _add_bottom_knobs(grp):
    """Add the bottom section knobs."""
    div = nuke.Text_Knob("divider2", "")
    grp.addKnob(div)

    add_btn = nuke.PyScript_Knob("add_layer_btn", "Add Layer", ADD_SCRIPT)
    grp.addKnob(add_btn)

    status = nuke.Text_Knob("status", "")
    status.clearFlag(nuke.STARTLINE)
    grp.addKnob(status)


# ---------------------------------------------------------------------------
# Internal node management
# ---------------------------------------------------------------------------

def _rebuild_internals(grp):
    """Recreate all AddChannels nodes inside the Group."""
    count = _get_current_layer_count(grp)

    # 1. Register all layers globally (must be done outside group context)
    #    Skip layers with empty name (prefix-only like "_070_" is not valid)
    layer_names = []
    for i in range(count):
        name = grp["name_{}".format(i)].value().strip()
        if not name:
            continue
        ln = _get_full_layer_name(grp, i)
        layer_names.append(ln)
        nuke.Layer(ln, [
            "{}.red".format(ln),
            "{}.green".format(ln),
            "{}.blue".format(ln),
            "{}.alpha".format(ln),
        ])

    # 2. Rebuild inside the Group
    grp.begin()

    # Find Input and Output
    input_node = None
    output_node = None
    for node in nuke.allNodes():
        if node.Class() == "Input":
            input_node = node
        elif node.Class() == "Output":
            output_node = node

    # Delete all non-Input/Output nodes
    for node in nuke.allNodes():
        if node.Class() not in ("Input", "Output"):
            nuke.delete(node)

    # Create AddChannels chain
    prev = input_node
    for i, ln in enumerate(layer_names):
        ac = nuke.nodes.AddChannels()
        ac.setName("AC_{}".format(ln))
        ac["channels"].setValue(ln)
        ac["color"].setValue(0)
        if prev:
            ac.setInput(0, prev)
        # Position
        if input_node:
            ac.setXYpos(input_node.xpos(), input_node.ypos() + 80 * (i + 1))
        prev = ac

    # Connect Output
    if output_node and prev:
        output_node.setInput(0, prev)
        if input_node:
            output_node.setXYpos(input_node.xpos(), input_node.ypos() + 80 * (len(layer_names) + 1))

    grp.end()

    # Label is driven by TCL expression set in run()


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

def _on_knob_changed(grp, knob):
    """Dispatch knob changes on the Group."""
    kname = knob.name()

    # Preset changed → auto-fill name
    m = re.match(r"preset_(\d+)", kname)
    if m:
        idx = int(m.group(1))
        preset_val = knob.value()
        if preset_val != "Custom":
            grp["name_{}".format(idx)].setValue(preset_val)
        _update_preview(grp, idx)
        _check_duplicates(grp)
        return

    # Prefix or name changed → update preview
    m = re.match(r"(prefix|name)_(\d+)", kname)
    if m:
        idx = int(m.group(2))
        _update_preview(grp, idx)
        _check_duplicates(grp)
        if "prefix" in kname:
            _reorder_layers(grp)
        return


def _update_preview(grp, index):
    """Update the layername preview Text_Knob for a given layer index."""
    try:
        full = _get_full_layer_name(grp, index)
        grp["layername_{}".format(index)].setValue("  <b>{}</b>".format(full))
    except NameError:
        pass


# ---------------------------------------------------------------------------
# Build / Add actions
# ---------------------------------------------------------------------------

def _rebuild_from_ui(grp):
    """Rebuild everything when user clicks Build Layers."""
    new_count = int(grp["num_layers"].value())
    old_count = _get_current_layer_count(grp)

    # Preserve existing definitions
    defs = _collect_layer_defs(grp, old_count)

    # Remove old layer knobs
    _remove_layer_knobs(grp, 0, old_count)
    _remove_bottom_knobs(grp)

    # Recreate
    _add_layer_knob_rows(grp, new_count, start_index=0, defs=defs)
    _add_bottom_knobs(grp)

    # Update hidden count
    grp["_layer_count"].setValue(str(new_count))

    # Rebuild internals
    _rebuild_internals(grp)
    _check_duplicates(grp)


def _add_one_layer(grp):
    """Add one more layer row."""
    old_count = _get_current_layer_count(grp)
    new_count = old_count + 1

    # Find next available prefix
    next_prefix = _find_next_available_prefix(grp, old_count)

    # Collect existing defs + new layer
    defs = _collect_layer_defs(grp, old_count)
    defs.append((next_prefix, "Custom", ""))

    # Remove all old knobs
    _remove_layer_knobs(grp, 0, old_count)
    _remove_bottom_knobs(grp)

    # Sort by prefix descending (same as _reorder_layers)
    defs.sort(key=lambda d: _prefix_to_int(_extract_prefix(d[0])), reverse=True)

    # Rebuild everything
    _add_layer_knob_rows(grp, new_count, start_index=0, defs=defs)
    _add_bottom_knobs(grp)

    # Update counts
    grp["num_layers"].setValue(new_count)
    grp["_layer_count"].setValue(str(new_count))

    _rebuild_internals(grp)
    _check_duplicates(grp)


def _delete_layer(grp, index):
    """Delete a single layer row and rebuild."""
    count = _get_current_layer_count(grp)
    if count <= 1:
        return  # Don't delete the last layer

    # Collect all defs, remove the one at index
    defs = _collect_layer_defs(grp, count)
    if index < len(defs):
        defs.pop(index)

    new_count = len(defs)

    # Remove all layer knobs and bottom
    _remove_layer_knobs(grp, 0, count)
    _remove_bottom_knobs(grp)

    # Recreate with updated defs
    _add_layer_knob_rows(grp, new_count, start_index=0, defs=defs)
    _add_bottom_knobs(grp)

    grp["num_layers"].setValue(new_count)
    grp["_layer_count"].setValue(str(new_count))

    _rebuild_internals(grp)
    _check_duplicates(grp)


def _reorder_layers(grp):
    """Reorder layers by prefix number (ascending index = ascending prefix).

    After reorder, index 0 has the lowest prefix (_010_) and the highest
    index has the highest prefix (_100_). Since the UI displays in reverse
    order, this puts _100_ at the bottom and the lowest at the top — matching
    the Photoshop layer stack.
    """
    count = _get_current_layer_count(grp)
    defs = _collect_layer_defs(grp, count)

    # Sort descending by prefix number (highest prefix = index 0 = UI bottom)
    defs.sort(key=lambda d: _prefix_to_int(_extract_prefix(d[0])), reverse=True)

    # Remove all and rebuild
    _remove_layer_knobs(grp, 0, count)
    _remove_bottom_knobs(grp)

    _add_layer_knob_rows(grp, count, start_index=0, defs=defs)
    _add_bottom_knobs(grp)

    _rebuild_internals(grp)
    _check_duplicates(grp)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run():
    """Create the EXR Layer Builder Group node."""
    grp = nuke.nodes.Group(name="DMP_EXR_Layers")
    grp["tile_color"].setValue(0x7F7F00FF)  # Olive/yellow
    grp["note_font_size"].setValue(14)
    grp["label"].setValue("[value num_layers] layers")

    # -- Build internal Input/Output first --
    grp.begin()
    inp = nuke.nodes.Input()
    out = nuke.nodes.Output()
    out.setInput(0, inp)
    out.setXYpos(inp.xpos(), inp.ypos() + 80)
    grp.end()

    # -- Add user knobs --
    tab = nuke.Tab_Knob("layers_tab", "Layer Definition")
    grp.addKnob(tab)

    title = nuke.Text_Knob("title", "", "<font size='5'><b>DMP EXR Layer Builder</b></font>")
    grp.addKnob(title)

    num = nuke.Int_Knob("num_layers", "Number of Layers")
    num.setValue(DEFAULT_NUM_LAYERS)
    num.setRange(1, 20)
    grp.addKnob(num)

    build_btn = nuke.PyScript_Knob("build_btn", "Build Layers", BUILD_SCRIPT)
    build_btn.clearFlag(nuke.STARTLINE)
    grp.addKnob(build_btn)

    div1 = nuke.Text_Knob("divider1", "")
    grp.addKnob(div1)

    # Hidden layer count tracker
    lc = nuke.String_Knob("_layer_count", "")
    lc.setValue(str(DEFAULT_NUM_LAYERS))
    lc.setFlag(nuke.INVISIBLE)
    grp.addKnob(lc)

    # Add initial layer rows
    _add_layer_knob_rows(grp, DEFAULT_NUM_LAYERS)

    # Bottom section
    _add_bottom_knobs(grp)

    # Build the initial internal nodes
    _rebuild_internals(grp)
    _check_duplicates(grp)

    # Set knobChanged callback
    grp["knobChanged"].setValue(KNOB_CHANGED_SCRIPT)

    return grp
