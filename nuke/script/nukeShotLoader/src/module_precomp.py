# module_precomp.py
import os, json, re, tempfile, hashlib
import nuke

def _atomic_json(path, data):                      # ton pattern actuel, factorisé
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise

def _frame_path(renderpath, frame):
    return re.sub(r"#+", lambda m: str(frame).zfill(len(m.group(0))), renderpath)

# --- hash amont par sérialisation du sous-arbre (indépendant de la frame et de l'env) ---

_IGNORE = {"xpos", "ypos", "selected", "label", "note_font",
           "note_font_size", "note_font_color", "tile_color", "gl_color",
           "postage_stamp", "hide_input", "cached", "bookmark", "dope_sheet",
           "onCreate", "onDestroy", "knobChanged", "updateUI", "autolabel",
           "which_custom", "versions", "version", "indicators", "postage_stamp_frame", "rootNodeUpdated", "panel", "icon",
           # Read node's internal reload counter — increments on every
           # reload / file mtime change / Prism updateNodeUI trigger.
           # Fresh farm session starts near 0, an interactive session with
           # Prism ends up in the hundreds. Doesn't affect what pixels the
           # Read outputs, so must not contribute to the semantic hash.
           # ---
           # Roto/RotoPaint UI-only state — Nuke mutates these when the
           # artist activates the tool (source viewer overlay, feather
           # gauge display, current toolbar preset). None of them affect
           # what the roto renders. Safe to drop globally: no other node
           # class uses these knob names.
           "toolbox", "gauge",
           # Cryptomatte gizmo dynamically populates cryptoLayerChoice
           # (an Enumeration_Knob) from the upstream Read's EXR metadata
           # via knobChanged. In an interactive session the Read has been
           # evaluated so the menu ends up as "{0} CryptoPrimitives
           # CryptoMaterials"; on farm the metadata isn't loaded yet at
           # hash time, so it's just "{0}". The real selection lives in
           # cryptoLayer (kept in the hash), so this UI-only cache is
           # safe to drop. lastSelectedCryptoLayerName is the same family.
           "cryptoLayerChoice", "lastSelectedCryptoLayerName",
           "source_transform_translate", "source_transform_center",
           "source_transform_scale", "source_transform_rotate",
           "source_transform_skew", "source_transform_skewX",
           "source_transform_skewY", "source_transform_skew_order",
           "source_transform_invert_matrix", "source_transform_time_offset",
           "source_transform_time_offset_type", "source_transform_reset",
           }

# Roto and RotoPaint expose a full transform (center/rotate/scale/skew/
# translate/matrix) that Nuke auto-populates the first time the artist
# opens the tool — e.g. `center` gets snapped to the format midpoint,
# scalar knobs get wrapped in single-key curves at the current frame.
# On farm those transforms stay at their as-authored defaults, so the
# two sides hash differently even when the roto shape itself is
# identical. These are the standard Nuke transform-pivot knobs, only
# ignored on Roto/RotoPaint — Transform / Card3D / GodRays still hash
# them because artists use them semantically there.
_ROTO_UI_TRANSFORM_KNOBS = frozenset({
    "center", "rotate", "scale", "skew", "skewX", "skewY", "skew_order",
    "translate", "transform_matrix", "stereo_offset",
})
_IGNORE_BY_CLASS = {
    "Roto": _ROTO_UI_TRANSFORM_KNOBS,
    "RotoPaint": _ROTO_UI_TRANSFORM_KNOBS,
}

_HASH_FRAME_RE = re.compile(r'#+')

_CHANNEL_LAYER_RE = re.compile(
    r'^([A-Za-z_]\w*)\.[A-Za-z_]\w*(?:\s+\1\.[A-Za-z_]\w*)+$'
)

def _normalize_channel_layer(s):
    """Collapse an expanded channel list ('P.x P.y P.z P.red') back to its
    layer name ('P'). Channel_Knob's toScript() flips between the two
    representations based on what the upstream input reports at
    evaluation time, and Link_Knob wrappers (used by Group/Gizmo inputs
    like ILGC_PosProject.position and P_Noise_Advanced.in) inherit the
    same behavior while hiding the underlying knob class from
    isinstance() checks — so we can't filter by knob type alone.
    Normalizing the value string catches every case: the class-based
    skip stays as a fast path, this fold is the safety net that made
    the Render Manager submit hash match a fresh manual mp.upstream_hash()
    call and the farm."""
    m = _CHANNEL_LAYER_RE.match(s)
    if m:
        return m.group(1)
    return s

def _normalize_file_value(s):
    """Fold '####' → '%04d' so a Read's file knob hashes identically
    whether the path was hand-authored with %04d (Prism, alt+up/down)
    or produced by the ShotLoader (which rewrites frame numbers to
    ####). Semantically the same sequence, so it must not invalidate
    the precomp cache when only the placeholder form changes."""
    return _HASH_FRAME_RE.sub(lambda m: "%0{}d".format(len(m.group(0))), s)

_FORMAT_KNOB_NAMES = frozenset({"format", "full_format", "proxy_format"})

def _normalize_format_value(s):
    """Drop the trailing format-name token from a Format_Knob value.
    Nuke stamps a Read's format knob with a registered format name
    whenever a matching addFormat() (same w/h/pixel-aspect) exists at
    evaluation time. Those addFormat() calls trickle in from gizmos as
    the scene loads — e.g. RIV_ReadCleanup and RIV_BrushScatter both
    hardcode 'FORMAT_DELIVERY' (2048x858) in embedded Reformat knobs,
    which registers the name globally the first time either gizmo is
    instantiated. Farm and local end up with a different registration
    order, so the same 2048x858 Read serializes as
    `2048 858 0 0 2048 858 1 ` on one machine and
    `2048 858 0 0 2048 858 1 FORMAT_DELIVERY` on the other. Dimensions
    drive the render; the trailing name is cosmetic. Keep the first
    seven numeric tokens (w h x y r t pa) and drop the rest. Values
    that don't match the seven-numeric-tokens shape (empty, '0', an
    expression) pass through untouched."""
    parts = s.split()
    if len(parts) < 7:
        return s
    try:
        for p in parts[:7]:
            float(p)
    except ValueError:
        return s
    return " ".join(parts[:7])

_SINGLE_KEY_CURVE_RE = re.compile(r'\{curve x\d+ ([^}]+)\}')

def _collapse_single_key_curves(s):
    """Unwrap single-key animation curves back to their scalar value.
    When the artist opens a Roto (and some other nodes) in the tool,
    Nuke silently converts scalar knobs into curves with one key at the
    current frame — e.g. `rotate=0` becomes `rotate={curve x1001 0}`.
    Semantically identical (a single-key curve is a constant), but the
    string differs from what farm serializes for the untouched .nk, so
    it broke the precomp cache. Multi-key curves are left alone; those
    do represent real animation and must still contribute to the hash."""
    return _SINGLE_KEY_CURVE_RE.sub(r'\1', s)

_ROTO_CURVES_FLAGS_RE = re.compile(r'^(AddMode) \d+ \d+ \d+ \d+ ')

def _normalize_roto_curves(s):
    """Strip the four-int flag block that follows `AddMode` in the
    Roto/RotoPaint `curves` knob. Nuke toggles those flags (visibility,
    tool-active markers, etc.) when the artist enters the tool locally;
    farm never touches them, so they drift the hash without changing
    what the curves draw."""
    return _ROTO_CURVES_FLAGS_RE.sub(r'\1 ', s)

def _node_sig(node):
    parts = [node.Class()]
    class_ignore = _IGNORE_BY_CLASS.get(node.Class(), ())
    for name, k in sorted(node.knobs().items()):
        if name in _IGNORE or name in class_ignore:
            continue
        # Skip Channel/ChannelMask knobs, whether studio-tagged via the
        # CHNKNB/CHKNB name suffix or standard-named on a stock/gizmo
        # node (e.g. ILGC_PosProject.position, P_Noise_Advanced.in).
        # Their toScript() compacts/expands a channel layer to either
        # the layer name (e.g. "P") or the explicit channel list
        # ("P.x P.y P.z P.red") depending on what the upstream input
        # reports at evaluation time. That representation drifts
        # between the Render Manager submit path (which evaluates
        # after a Prism save that perturbs the graph state) and both
        # the farm side and a fresh manual mp.upstream_hash() call —
        # both of which see the stable expanded form. Filtering by
        # knob class instead of name catches every case: the earlier
        # name-suffix rule only covered MaskBuddy's aovSelectionCHNKNB.
        try:
            if isinstance(k, (nuke.Channel_Knob, nuke.ChannelMask_Knob)):
                continue
        except Exception:
            pass
        if name.endswith("CHNKNB") or name.endswith("CHKNB"):
            continue
        try:
            value = k.toScript()
            if name == "file":
                value = _normalize_file_value(value)
            elif name == "curves":
                value = _normalize_roto_curves(value)
            elif name in _FORMAT_KNOB_NAMES:
                value = _normalize_format_value(value)
            value = _collapse_single_key_curves(value)
            value = _normalize_channel_layer(value)
            parts.append(name + "=" + value)
        except Exception:
            pass
    return ";".join(parts)

def _is_precomp_write(node):
    """True for Write nodes tagged as PrecompWrite by the studio gizmo."""
    try:
        if node.Class() != "Write":
            return False
        if 'tag' not in node.knobs():
            return False
        return (node['tag'].value() or "").strip() == "PrecompWrite"
    except Exception:
        return False

def _skip_from_hash(node):
    """Nodes that should not contribute to upstream_hash — Dots have no
    image effect, and PrecompWrites are cache boundaries we don't want to
    tie the downstream hash to (their version bumps, etc.)."""
    return node is not None and (node.Class() == "Dot" or _is_precomp_write(node))

def _resolve_through_skipped(node):
    """Walk input(0) past any skipped node so downstream connection lists
    refer to the first meaningful ancestor. Without this, inserting or
    removing a Dot would still change the hash via the ins list of the
    node below it."""
    seen = set()
    cur = node
    while cur is not None and _skip_from_hash(cur):
        if cur in seen:
            return None
        seen.add(cur)
        try:
            cur = cur.input(0)
        except Exception:
            return None
    return cur

def _wireless_deps(node):
    """Return the Anchor node(s) a Stamps-gizmo node points to.

    Adrian Pueyo's Stamps have no real graph input to their upstream —
    the link is stored in an 'anchor' knob that names an Anchor node in
    the scene, and dependencies(nuke.INPUTS) doesn't see it. Without
    this the walk stops at each Stamp and never reaches whatever the
    artist wired into the Anchor (a Read, a Camera, etc.), so changes
    upstream of a Stamp never affect upstream_hash."""
    try:
        ak = node.knob("anchor")
    except Exception:
        return []
    if ak is None:
        return []
    try:
        anchor_name = ak.value()
    except Exception:
        return []
    if not anchor_name:
        return []
    anchor = nuke.toNode(anchor_name)
    return [anchor] if anchor is not None else []

def _all_deps(node):
    return list(node.dependencies(nuke.INPUTS)) + _wireless_deps(node)

def _upstream_entries(write_node):
    """Yield the (node, sig, ins_str) tuples that upstream_hash consumes,
    in the exact same order — shared by upstream_hash and the debug dump
    so the two views can't drift.

    Sort by (fullName, sig, ins_str): when two distinct underlying nodes
    share a fullName (rare but observed), sorting by fullName alone leaves
    ties broken by set iteration order, which is id()-based on nuke.Node
    and therefore varies from session to session — causing the same scene
    to hash differently locally vs on farm."""
    start = write_node.input(0)
    if start is None:
        return
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        if n is None or n in seen:
            continue
        seen.add(n)
        for dep in _all_deps(n):
            stack.append(dep)
    entries = []
    for n in seen:
        if _skip_from_hash(n):
            continue
        sig = _node_sig(n)
        resolved = [_resolve_through_skipped(i) for i in _all_deps(n)]
        ins_str = "<" + "|".join((r.fullName() if r is not None else "") for r in resolved) + ">"
        entries.append((n, sig, ins_str))
    entries.sort(key=lambda e: (e[0].fullName(), e[1], e[2]))
    for entry in entries:
        yield entry

def upstream_hash(write_node):
    if write_node.input(0) is None:
        return None
    h = hashlib.sha1()
    for _n, sig, ins_str in _upstream_entries(write_node):
        h.update(sig.encode("utf-8"))
        h.update(ins_str.encode("utf-8"))
    return h.hexdigest()

def upstream_hash_dump(write_node):
    """Debug helper — returns a list of human-readable lines describing
    every entry the hash walks. Use it on both local and farm to diff
    what actually differs when a hash mismatch shows up in the diagnostic."""
    lines = []
    for n, sig, ins_str in _upstream_entries(write_node):
        lines.append(f"{n.fullName()}  ins={ins_str}")
        lines.append(f"  sig={sig}")
    return lines

_CACHED_COLOR = 0x3a5a3aff   # dark green (matches Render Manager table)
_LIVE_COLOR   = 0xaa2c2cff   # dark red   (matches Render Manager table)

def _apply_visuals(node, result):
    # Only write when the value actually differs — this function fires on
    # every `which` evaluation and setValue would otherwise mark the script
    # modified and spam undo history.
    label = "Cached" if result == 0 else "Live"
    color = _CACHED_COLOR if result == 0 else _LIVE_COLOR
    try:
        k = node.knob('label')
        if k is not None and k.value() != label:
            k.setValue(label)
    except Exception:
        pass
    try:
        k = node.knob('tile_color')
        if k is not None and k.value() != color:
            k.setValue(color)
    except Exception:
        pass

def _precomp_write_input(switch_node):
    """Return the PrecompWrite among the switch's inputs, walking through
    Dots. Robust to whichever port the artist wired it on."""
    try:
        n_inputs = switch_node.inputs()
    except Exception:
        n_inputs = 2
    for i in range(n_inputs):
        try:
            n = switch_node.input(i)
        except Exception:
            continue
        seen = set()
        while n is not None and n.Class() == "Dot" and n not in seen:
            seen.add(n)
            try:
                n = n.input(0)
            except Exception:
                n = None
        if n is not None and _is_precomp_write(n):
            return n
    return None

def _write_frame_range(write_node):
    """Return (first, last) for a Write, matching what Nuke actually
    renders. `use_limit=False` means the root range wins even if the
    Write carries stale first/last values."""
    if write_node['use_limit'].value():
        return int(write_node['first'].value()), int(write_node['last'].value())
    return int(nuke.root().firstFrame()), int(nuke.root().lastFrame())

def _all_frames_present(write_node):
    """True when every frame in the Write's render range exists on disk.
    Shared by after_render_precomp.py (deciding whether to publish
    Render_Done=True at task exit) and _compute_which (self-healing a
    render_state.json that Deadline left stuck at False)."""
    try:
        rp = write_node['renderpath'].value()
        first, last = _write_frame_range(write_node)
        return all(os.path.exists(_frame_path(rp, f))
                   for f in range(first, last + 1))
    except Exception:
        return False

def _compute_which(switch_node):
    try:
        src = _precomp_write_input(switch_node)
        if src is None:
            return 1
        folder = os.path.dirname(src['renderpath'].value())

        # 1. rendu complet ?
        state_path = os.path.join(folder, "render_state.json")
        state_says_done = False
        if os.path.exists(state_path):
            try:
                with open(state_path) as f:
                    state_says_done = json.load(f).get("Render_Done") is True
            except Exception:
                pass

        # Self-heal: on parallel farm renders the last task's
        # after_render_precomp.py sometimes checks all_present *before*
        # the network share surfaces frames its peers just wrote — so
        # Render_Done stays False even though the render actually
        # completed. Nothing ever comes back to fix it. If the frames
        # ARE on disk when we look now, promote the state ourselves so
        # the switch doesn't stay Live forever.
        if not state_says_done and _all_frames_present(src):
            try:
                _atomic_json(state_path, {"Render_Done": True})
                state_says_done = True
            except Exception:
                pass

        if not state_says_done:
            return 1

        # 2. la branche amont a-t-elle bougé ? (verifie aussi en farm/terminal
        # car Render_Done n'est pas invalide quand l'amont change en interactif)
        ref = os.path.join(folder, "cache_ref.json")
        if not os.path.exists(ref):
            return 1
        with open(ref) as f:
            if json.load(f).get("ref_hash") != upstream_hash(src):
                return 1
        return 0
    except Exception:
        return 1                                   # tout imprévu -> Live

def precomp_which(switch_node):
    result = _compute_which(switch_node)
    _apply_visuals(switch_node, result)
    return result
