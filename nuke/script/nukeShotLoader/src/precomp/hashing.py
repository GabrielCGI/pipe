"""Upstream content hash of a PrecompWrite.

Merkle hash: hash(node) = H(knob signature, hash of each input, hashes of
the nodes its expressions reference, hash of its internals for plain
Groups). Consequences:
  * node names don't matter (renames never invalidate a cache), clones
    are told apart by their inputs, no sort order to get wrong;
  * expression links are found by parsing the knob text, not with
    Node.dependencies(EXPRESSIONS) whose answer depends on what Nuke has
    already evaluated;
  * Dots, PrecompWrites and precomp switches are transparent: a precomp
    depends on the *content* upstream of another precomp, not on which
    cache version it currently reads.

Knob values come from toScript(), folded by a few normalizations for
values Nuke rewrites on its own (format names, resolved colorspaces,
single-key curves created by opening a tool...).
"""

import hashlib
import re
from typing import Dict, List, Optional

import nuke

from . import spec

# UI-only / state-only knobs: never part of a node's content.
IGNORED_KNOBS = frozenset({
    "name", "xpos", "ypos", "selected", "label", "note_font", "note_font_size", "note_font_color",
    "tile_color", "gl_color", "postage_stamp", "postage_stamp_frame", "hide_input", "cached",
    "bookmark", "dope_sheet", "onCreate", "onDestroy", "knobChanged", "updateUI", "autolabel",
    "indicators", "rootNodeUpdated", "panel", "icon", "help", "lifetimeStart", "lifetimeEnd",
    "useLifetime", "lock_connections", "window", "gsv", "mapsize", "show_group_view",
    "group_view_position",
    "version",                                   # Read reload counter
    spec.VERSION_DISPLAY,                        # Writes' Prism tab: version shown
    spec.LEGACY_WHICH, "versions",               # v1 precomp knobs
    "toolbox", "gauge",                          # Roto/RotoPaint tool state
    "cryptoLayerChoice", "lastSelectedCryptoLayerName",  # Cryptomatte UI cache
    "scene_graph",                               # ReadGeo panel expand state
    "source_transform_translate", "source_transform_center", "source_transform_scale",
    "source_transform_rotate", "source_transform_skew", "source_transform_skewX",
    "source_transform_skewY", "source_transform_skew_order", "source_transform_invert_matrix",
    "source_transform_time_offset", "source_transform_time_offset_type", "source_transform_reset",
})
# Transform pivots Nuke auto-fills the first time a Roto is opened.
_ROTO_UI = frozenset({"center", "rotate", "scale", "skew", "skewX", "skewY", "skew_order",
                      "translate", "transform_matrix", "stereo_offset"})
_IGNORE_BY_CLASS = {"Roto": _ROTO_UI, "RotoPaint": _ROTO_UI}
# Colorspace knobs Nuke 15 derives from `colorspace` / `raw` (both hashed),
# and only in the GUI, whenever it gets to the node: a fresh load leaves them
# at scene_linear, a session that viewed the Read has its transform there.
# Hashed, they made a render's hash depend on the session it was submitted
# from (cache Live again after a reopen, SQ0010-SH0010). Pinned to their
# fresh-load value, not ignored: hashes computed before stay as they were.
_DERIVED_COLORSPACE = {"in_colorspace": "scene_linear", "out_colorspace": "scene_linear"}
_PINNED_BY_CLASS = {"Read": _DERIVED_COLORSPACE,
                    "Write": dict(_DERIVED_COLORSPACE, ocioColorspace="scene_linear")}

_SKIP_KNOB_TYPES = tuple(getattr(nuke, name) for name in (
    "Tab_Knob", "Text_Knob", "PyScript_Knob", "PyCustom_Knob", "Help_Knob",
    "BeginTabGroup_Knob", "EndTabGroup_Knob", "Obsolete_Knob", "Channel_Knob", "ChannelMask_Knob",
) if hasattr(nuke, name))

# PrecompWrite settings that change the cached pixels.
_WRITE_SETTINGS = ("channels", "file_type", "datatype", "compression", "dw_compression_level",
                   "raw", "colorspace", "premultiplied", "interleave", "first_part")
_ROOT_SETTINGS = ("format", "colorManagement", "OCIO_config", "customOCIOConfigPath",
                  "workingSpaceLUT", "floatLut", "logLut", "int8Lut", "int16Lut")

# ---- value normalizations --------------------------------------------------

_FRAME_TOKEN_RE = re.compile(r"#+")
_SINGLE_KEY_CURVE_RE = re.compile(r"\{curve x\d+ ([^}]+)\}")
_ROTO_FLAGS_RE = re.compile(r"^(AddMode) \d+ \d+ \d+ \d+ ")
_RESOLVED_COLORSPACE_RE = re.compile(r"\s*\([^)]*\)\s*$")
_FORMAT_KNOBS = frozenset({"format", "full_format", "proxy_format"})
_COLORSPACE_KNOBS = frozenset({"colorspace", "in_colorspace", "out_colorspace"})


def _normalize_format(value):
    """Keep 'w h x y r t pa', drop the format name Nuke attaches depending
    on which addFormat() calls ran first."""
    parts = value.split()
    if len(parts) < 7:
        return value
    try:
        [float(p) for p in parts[:7]]
    except ValueError:
        return value
    return " ".join(parts[:7])


def _first_group(match):
    return match.group(1)


# Called for every knob of every node a precomp depends on: the regexes only
# run when they can match, and with function replacements (a "\1" template
# makes CPython import `re` again on each call, through shiboken's import hook).
def _normalize(name, value):
    if name == "file":
        value = _FRAME_TOKEN_RE.sub(lambda m: "%0{}d".format(len(m.group(0))), value)
    elif name == "curves":
        if value.startswith("AddMode"):
            value = _ROTO_FLAGS_RE.sub(lambda m: m.group(1) + " ", value)
    elif name in _FORMAT_KNOBS:
        value = _normalize_format(value)
    elif name in _COLORSPACE_KNOBS:
        value = _RESOLVED_COLORSPACE_RE.sub("", value)  # 'default (scene_linear)' -> 'default'
    if "{curve x" in value:
        value = _SINGLE_KEY_CURVE_RE.sub(_first_group, value)   # {curve x1001 0} -> 0
    return value


# ---- expression references ------------------------------------------------

_REF_RE = re.compile(r"(?<![\w.$/\\:#-])([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)")
_SCOPES = frozenset({"this", "parent", "root"})   # 'parent.CAM.focal': the node is CAM
_NOT_NODES = frozenset({"topnode", "frame", "nuke", "math", "python", "value", "knob", "expr", "curve",
                        "x", "y", "t"})


def _referenced_names(texts):
    """Candidate node paths in expression/TCL text ('CAM.translate.x' ->
    'CAM.translate', 'CAM'; 'parent.CAM.focal' -> 'CAM'). Unresolvable
    candidates (knobs of the node or of its group) are dropped later."""
    names = set()
    for text in texts:
        for chain in _REF_RE.findall(text):
            parts = chain.split(".")
            while parts and parts[0] in _SCOPES:
                del parts[0]
            if not parts or parts[0] in _NOT_NODES or parts[0].startswith("input"):
                continue
            for end in range(len(parts) - 1, 0, -1):
                names.add(".".join(parts[:end]))
    return names


# ---- node classification --------------------------------------------------

def is_precomp_write(node) -> bool:
    try:
        tag = node.knob("tag")
        return node.Class() == "Write" and tag is not None and (tag.value() or "").strip() == spec.PRECOMP_TAG
    except Exception:
        return False


def is_switch(node) -> bool:
    """v2 switch group or v1 expression switch."""
    return node.knob(spec.SWITCH_MARKER) is not None or node.knob(spec.LEGACY_WHICH) is not None


def _is_transparent(node) -> bool:
    return node.Class() == "Dot" or is_precomp_write(node) or is_switch(node)


# ---- hasher ---------------------------------------------------------------

class ContentHasher:
    """Hashes precomp upstreams. Knob signatures are memoized for the
    lifetime of the instance: create one per evaluation pass."""

    def __init__(self):
        self._sigs: Dict[int, tuple] = {}
        self.visited_ids = set()
        self.visited_nodes: Dict[int, object] = {}   # every node a hashed render depends on

    # ---- public ---------------------------------------------------------

    def precomp_hash(self, write) -> Optional[str]:
        """Content hash of what `write` renders, None when unconnected."""
        start = write.input(0)
        if start is None:
            return None
        h = hashlib.sha1()
        h.update(_settings_sig(nuke.root(), _ROOT_SETTINGS).encode("utf-8"))
        h.update(_settings_sig(write, _WRITE_SETTINGS).encode("utf-8"))
        h.update(self.node_hash(start).encode("utf-8"))
        h.update(_live_salt(write).encode("utf-8"))
        return h.hexdigest()

    def node_hash(self, root) -> str:
        """Iterative post-order walk (no recursion limit). Hashes are
        memoized per call so an expression cycle is always cut at the same
        place for a given starting node."""
        memo: Dict[int, str] = {}
        on_path = set()
        stack = [(root, False)]
        while stack:
            node, expanded = stack.pop()
            key = id(node)
            if key in memo:
                continue
            if not expanded:
                if key in on_path:
                    continue
                on_path.add(key)
                self.visited_ids.add(key)
                self.visited_nodes[key] = node
                stack.append((node, True))
                for dep in reversed(self._deps(node)):
                    if dep is not None and id(dep) not in memo and id(dep) not in on_path:
                        stack.append((dep, False))
            else:
                on_path.discard(key)
                memo[key] = self._combine(node, memo)
        return memo[id(root)]

    # ---- graph ------------------------------------------------------------

    def _deps(self, node) -> List:
        if _is_transparent(node):
            return [_safe_input(node, 0)]
        deps = [_safe_input(node, i) for i in range(_input_count(node))]
        deps += self._refs(node)
        output = _group_output(node)
        if output is not None:
            deps.append(output)
        return deps

    def _combine(self, node, memo) -> str:
        if _is_transparent(node):
            source = _safe_input(node, 0)
            upstream = memo.get(id(source), "cycle") if source is not None else "none"
            salt = _live_salt(node)
            return hashlib.sha1((upstream + salt).encode("utf-8")).hexdigest() if salt else upstream
        parts = [self._sig(node)[0]]
        for i in range(_input_count(node)):
            source = _safe_input(node, i)
            parts.append("in:" + (memo.get(id(source), "cycle") if source is not None else "-"))
        parts += sorted("x:" + memo.get(id(ref), "cycle") for ref in self._refs(node))
        output = _group_output(node)
        if output is not None:
            parts.append("g:" + memo.get(id(output), "cycle"))
        return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()

    def _refs(self, node) -> List:
        return self._sig(node)[1]

    def _sig(self, node) -> tuple:
        """(knob signature, nodes referenced by its expressions)."""
        key = id(node)
        cached = self._sigs.get(key)
        if cached is not None:
            return cached
        cls = node.Class()
        class_ignore = _IGNORE_BY_CLASS.get(cls, ())
        class_pinned = _PINNED_BY_CLASS.get(cls, {})
        parts, expression_texts = [cls], []
        for name, knob in sorted(node.knobs().items()):
            if name in IGNORED_KNOBS or name in class_ignore or isinstance(knob, _SKIP_KNOB_TYPES):
                continue
            if name in class_pinned:
                parts.append(f"{name}={class_pinned[name]}")
                continue
            try:
                value = knob.toScript()
            except Exception:
                continue
            if ("{" in value or "[" in value) and "." in value:
                expression_texts.append(value)
            parts.append(f"{name}={_normalize(name, value)}")
        refs = self._resolve(node, _referenced_names(expression_texts) | _stamp_anchor(node))
        result = (";".join(parts), refs)
        self._sigs[key] = result
        return result

    @staticmethod
    def _resolve(node, names) -> List:
        if not names:
            return []
        full = node.fullName()
        prefix = full.rsplit(".", 1)[0] + "." if "." in full else ""
        found = {}
        for name in names:
            target = (nuke.toNode(prefix + name) if prefix else None) or nuke.toNode(name)
            if target is not None and target is not node:
                found[id(target)] = target
        return sorted(found.values(), key=lambda n: n.fullName())


def _live_salt(node) -> str:
    """'' unless "Force Live" was used on this PrecompWrite (hashes of
    precomps never forced stay exactly what they were)."""
    knob = node.knob(spec.LIVE_FROM)
    try:
        value = int(knob.value()) if knob is not None else 0
    except (TypeError, ValueError):
        value = 0
    return f"|live_from={value}" if value else ""


def _settings_sig(node, knob_names) -> str:
    parts = []
    for name in knob_names:
        knob = node.knob(name)
        if knob is not None:
            try:
                parts.append(f"{name}={_normalize(name, knob.toScript())}")
            except Exception:
                pass
    return ";".join(parts)


def _stamp_anchor(node) -> set:
    """Stamps wired nodes name their anchor in an `anchor` knob."""
    knob = node.knob("anchor")
    try:
        name = knob.value() if knob is not None else ""
    except Exception:
        name = ""
    return {name} if isinstance(name, str) and name else set()


def _input_count(node) -> int:
    try:
        return node.inputs()
    except Exception:
        return 0


def _safe_input(node, index):
    try:
        return node.input(index)
    except Exception:
        return None


def _group_output(node):
    """Output node of a plain Group (artist-editable internals). Gizmo
    internals come from their .gizmo file and are not hashed."""
    if node.Class() != "Group":
        return None
    try:
        return node.output()
    except Exception:
        return None
