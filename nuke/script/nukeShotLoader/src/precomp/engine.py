"""Evaluate precomp states, route switches, prepare renders.

    evaluate()          -> PrecompState per PrecompWrite (read-only)
    sync()              evaluate + route every switch (cache when valid, else live)
    force_live()        next version + ignore earlier renders (Render Manager)
    cancel_force_live() back to the previous version while not rendered yet
    prepare_renders()   bump versions, write manifests, route switches to the
                        renders about to be produced (farm submit)
    finalize_manifests() re-hash after the script save, fix manifests if needed
    discard_renders()   undo prepare_renders() for the renders never started
    render_locally()    former Render button of a PrecompWrite (GUI: ui/write_render.py)
    render_here()       a render of one PrecompWrite in this session
    rendered_versions() its versions on disk
    render_into_version() frames re-rendered into one of them (repair)
"""

import contextlib
import datetime
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import nuke

from ..scene.utils import no_undo, prism_core, undo_group
from . import manifest, nodes, spec
from .hashing import ContentHasher

_busy = 0
_upstream_ids = frozenset()


class Status:
    CACHED = "cached"
    LIVE = "live"
    RENDERING = "rendering"   # frames of the current hash partially on disk
    NO_INPUT = "no_input"
    LEGACY = "legacy"
    ERROR = "error"


@dataclass
class PrecompState:
    write: object
    switch: object = None
    status: str = Status.LIVE
    reason: str = ""
    hash: Optional[str] = None
    needed: Optional[Tuple[int, int]] = None
    cache: Optional[manifest.CacheEntry] = None
    pending: Optional[manifest.Pending] = None
    forced: bool = False      # Force Live on, its version not rendered nor submitted yet

    @property
    def name(self) -> str:
        return self.write.fullName()

    @property
    def needs_render(self) -> bool:
        return self.status in (Status.LIVE, Status.RENDERING)

    @property
    def node_label(self) -> str:
        """State without progress numbers, for the switch node (changes only
        on transitions, so a render landing frame by frame doesn't keep
        rewriting the script)."""
        if self.status == Status.CACHED:
            return f"Cached v{self.cache.version:03d}"
        if self.status == Status.RENDERING:
            verb = "Rendering" if self.pending.present else "Submitted"
            return f"{verb} v{self.pending.version:03d}"
        if self.status == Status.LIVE and self.forced:
            return "Live (forced)"
        return {Status.LIVE: "Live", Status.NO_INPUT: "No input",
                Status.LEGACY: "Legacy", Status.ERROR: "Error"}[self.status]

    @property
    def label(self) -> str:
        """node_label + frame progress, for the Render Manager table."""
        if self.status == Status.RENDERING:
            return f"{self.node_label} ({self.pending.present}/{self.pending.needed})"
        return self.node_label


@contextlib.contextmanager
def busy():
    """Scope of our own automatic knob changes: ignored by the GUI watcher
    and kept out of the undo history."""
    global _busy
    _busy += 1
    try:
        with no_undo():
            yield
    finally:
        _busy -= 1


def is_busy() -> bool:
    return _busy > 0


def upstream_ids() -> frozenset:
    """ids of the nodes upstream of any precomp at the last evaluation."""
    return _upstream_ids


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(writes: Optional[Iterable] = None) -> List[PrecompState]:
    global _upstream_ids
    full_scan = writes is None
    writes = list(nodes.iter_precomp_writes()) if full_scan else list(writes)
    hasher = ContentHasher()
    listing = manifest.DiskListing()
    states = [_evaluate_one(write, hasher, listing) for write in writes]
    if full_scan:
        _upstream_ids = frozenset(hasher.visited_ids)
    return states


def _evaluate_one(write, hasher, listing) -> PrecompState:
    state = PrecompState(write)
    try:
        state.switch, legacy = nodes.find_switch(write)
        if legacy or nodes.is_legacy_write(write):
            state.status, state.reason = Status.LEGACY, "v1 precomp: run 'Upgrade Precomps'"
            return state
        state.needed = nodes.frame_range(write)
        state.hash = hasher.precomp_hash(write)
        if state.hash is None:
            state.status, state.reason = Status.NO_INPUT, "the PrecompWrite input is not connected"
            return state
        root = nodes.version_root(write)
        state.cache, state.pending = manifest.find_cache(root, state.hash, state.needed, listing)
        if state.cache is not None:
            state.status = Status.CACHED
        elif state.pending is not None:
            state.status = Status.RENDERING
            state.reason = ("render in progress or incomplete" if state.pending.present
                            else "no frame yet: waiting for the farm")
        else:
            state.status, state.reason = Status.LIVE, "no render of the current upstream"
            state.forced = is_force_pending(write)
            if state.forced:
                state.reason = (f"forced live: earlier renders ignored, "
                                f"next render v{_int_knob(write, spec.LIVE_FROM):03d}")
    except Exception as e:
        state.status, state.reason = Status.ERROR, f"{type(e).__name__}: {e}"
    return state


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def apply(states: Iterable[PrecompState]) -> List[PrecompState]:
    """Route each switch: cache when valid, live otherwise (errors included)."""
    states = list(states)
    with busy():
        for state in states:
            if state.switch is None or state.status == Status.LEGACY:
                continue
            nodes.route(state.switch, state.write, state.cache)
            nodes.set_status(state.switch, state.node_label, state.reason, state.cache is not None)
    return states


def sync(writes: Optional[Iterable] = None) -> List[PrecompState]:
    return apply(evaluate(writes))


def is_force_pending(write) -> bool:
    """Force Live is on and its version is exactly the next one to render
    (neither rendered nor submitted yet): it can still be cancelled. A mark
    left by an older force — or carried by a copy-pasted precomp, or kept
    after an identifier change — no longer matches and counts as off."""
    forced = _int_knob(write, spec.LIVE_FROM)
    return (bool(forced) and forced == _int_knob(write, "versions")
            and forced == manifest.next_version(nodes.version_root(write)))


def can_force(state: PrecompState) -> bool:
    """Force Live only matters when a render would otherwise be used: a Live
    precomp has none to ignore (and neither have the precomps downstream)."""
    return state.status in (Status.CACHED, Status.RENDERING)


def force_live(writes: Iterable, log=print) -> List[PrecompState]:
    """Render Manager "Force Live": each precomp moves to its next free
    version and every render made before stops matching — for this precomp
    and the precomps downstream of it — so they go live even when the graph
    itself didn't change (a source file rewritten in place, a gizmo updated
    on disk). The next submit renders into that version. Cancel with
    cancel_force_live() until then (or Ctrl+Z). Live precomps are skipped."""
    writes = list(_v2_writes(writes, log))
    states = {id(s.write): s for s in evaluate(writes)}
    with undo_group("Force precomp live"):
        for write in writes:
            if is_force_pending(write):
                continue
            if not can_force(states[id(write)]):
                log(f"[precomp] {write.fullName()}: already live, no render to ignore — not forced")
                continue
            nodes.set_force_undo(write, f"{_int_knob(write, spec.LIVE_FROM)} {_int_knob(write, 'versions')}")
            version = manifest.next_version(nodes.version_root(write))
            write["versions"].setValue(version)
            nodes.set_live_from(write, version)
            log(f"[precomp] {write.fullName()}: forced live, next render v{version:03d}")
    return sync()


def cancel_force_live(writes: Iterable, log=print) -> List[PrecompState]:
    """Undo a Force Live whose version wasn't rendered nor submitted:
    previous version and caches come back."""
    writes = list(_v2_writes(writes, log))
    with undo_group("Cancel forced precomp"):
        for write in writes:
            if not is_force_pending(write):
                continue
            try:
                live_from, versions = (int(v) for v in (write[spec.FORCE_UNDO].value() or "").split())
            except (KeyError, NameError, TypeError, ValueError):
                live_from, versions = 0, manifest.next_version(nodes.version_root(write)) - 1
            nodes.set_live_from(write, live_from)
            write["versions"].setValue(versions)
            nodes.set_force_undo(write, "")
            log(f"[precomp] {write.fullName()}: force live cancelled, back to v{versions:03d}")
    return sync()


def _v2_writes(writes, log):
    for write in writes:
        if write is None:
            continue
        if nodes.is_legacy_write(write) or write.knob("versions") is None:
            log(f"[precomp] {write.fullName()}: not a v2 precomp, left as is")
            continue
        yield write


# ---------------------------------------------------------------------------
# Renders
# ---------------------------------------------------------------------------

@dataclass
class PreparedRender:
    state: PrecompState
    version: int
    folder: str
    path: str
    previous_version: int = 0     # the Write's version knob before
    created_root: bool = False    # the versions folder didn't exist before


def prepare_renders(states: Iterable[PrecompState], route_to_render=True, log=print) -> List[PreparedRender]:
    """For each precomp to render: next free version, manifest, and (farm
    submit) switch routed to the frames that render will produce, so the
    downstream renders of the same job read them."""
    prepared = []
    with busy():
        for state in states:
            if state.hash is None or state.status == Status.LEGACY:
                log(f"[precomp] {state.name}: not renderable ({state.label})")
                continue
            try:
                prepared.append(_prepare_one(state, route_to_render, log))
            except Exception as e:  # e.g. render folder not writable: skip this precomp only
                log(f"[precomp] {state.name}: NOT prepared, left out of the render ({type(e).__name__}: {e})")
                continue
            item = prepared[-1]
            log(f"[precomp] {state.name}: v{item.version:03d} prepared ({state.needed[0]}-{state.needed[1]})")
    return prepared


def _prepare_one(state: PrecompState, route_to_render: bool, log) -> PreparedRender:
    write = state.write
    _prism_refresh(write, log)
    previous = _int_knob(write, "versions")
    version = manifest.next_version(nodes.version_root(write))
    write["versions"].setValue(version)
    path = nodes.render_path(write)
    folder = os.path.dirname(path)
    created_root = not os.path.isdir(os.path.dirname(folder))
    manifest.write_manifest(folder, _manifest_data(state, path))
    if route_to_render and state.switch is not None:
        entry = manifest.CacheEntry(version, folder, path, *state.needed)
        nodes.route(state.switch, write, entry)
        nodes.set_status(state.switch, f"Submitting v{version:03d}", "reads the render being submitted", True)
    return PreparedRender(state, version, folder, path, previous, created_root)


def finalize_manifests(prepared: List[PreparedRender], log=print):
    """Re-hash after the script save (save callbacks may touch knobs) and
    keep the manifests in line with what the GUI will compare against."""
    if not prepared:
        return
    hasher = ContentHasher()
    for item in prepared:
        current = hasher.precomp_hash(item.state.write)
        if current and current != item.state.hash:
            log(f"[precomp] {item.state.name}: upstream hash changed during save, manifest updated")
            item.state.hash = current
            manifest.write_manifest(item.folder, _manifest_data(item.state, item.path))


def discard_renders(prepared: List[PreparedRender], log=print) -> List[PreparedRender]:
    """Undo prepare_renders() for the renders that never started (submission
    cancelled, local render stopped before them): manifest and version
    folder removed, version knob back to what it was — the precomp is as
    before and the next render takes the same version, no gap. A folder
    that holds frames is left alone: those renders are returned. Call
    sync() afterwards to route the switches back."""
    kept = []
    with busy():
        for item in prepared:
            if not manifest.discard_manifest(item.folder):
                kept.append(item)
                continue
            if item.created_root:
                try:
                    os.rmdir(os.path.dirname(item.folder))
                except OSError:
                    pass
            try:
                item.state.write["versions"].setValue(item.previous_version)
            except Exception as e:
                log(f"[precomp] {item.state.name}: version knob not restored ({e})")
            log(f"[precomp] {item.state.name}: v{item.version:03d} released (not rendered nor submitted)")
    return kept


def render_locally(write):
    """Render button of the PrecompWrites made from the earlier v2 template
    (this call is their knob script, until upgrade_prism_tabs() replaces
    it at script load). In the GUI: the Shot Loader's button
    (ui/write_render.py, Submit Job decides farm or local); without GUI:
    render_here()."""
    if getattr(nuke, "GUI", False):
        from ..ui import write_render
        write_render.render_write(write)
        return
    render_here(write)


def render_here(write):
    """New version + manifest, render in this session, re-sync. The render
    is Prism's local one when Prism is loaded and the Write's Submit Job box
    is unticked (what its Render button always did); nuke.execute otherwise."""
    state = evaluate([write])[0]
    if state.status == Status.LEGACY:
        nuke.message("This precomp uses the v1 setup.\nRun Shot Loader > Upgrade Precomps first.")
        return
    prepared = prepare_renders([state], route_to_render=False)
    if not prepared:
        return
    plugin = getattr(prism_core(), "appPlugin", None)
    submit_job = write.knob(spec.SUBMIT_JOB)
    try:
        if plugin is not None and submit_job is not None and not submit_job.value():
            plugin.startRender(write)
        else:
            nuke.execute(write, *state.needed)
    finally:
        discard_renders(prepared)   # stopped before its first frame: version released
        sync([write])


@dataclass
class RenderedVersion:
    """A version of a precomp on disk (a folder with its manifest)."""
    version: int
    path: str            # file pattern (####)
    first: int
    last: int
    missing: List[int]   # frames of first-last not on disk
    current: bool        # rendered from the current state of the script (its hash)


def rendered_versions(state: PrecompState) -> List[RenderedVersion]:
    """The versions of `state`'s precomp that have a manifest, newest first."""
    listing = manifest.DiskListing()
    found = []
    for version, folder in manifest.version_folders(nodes.version_root(state.write)):
        data = manifest.read_manifest(folder)
        if not data:
            continue
        basename = os.path.basename(str(data.get("renderpath", "")).replace("\\", "/"))
        try:
            first, last = int(data["first"]), int(data["last"])
        except (KeyError, TypeError, ValueError):
            continue
        frames = listing.frames(folder, basename)
        found.append(RenderedVersion(version, os.path.join(folder, basename).replace("\\", "/"), first, last,
                                     sorted(set(range(first, last + 1)) - frames),
                                     bool(state.hash) and data.get("hash") == state.hash))
    return found


def render_into_version(write, rendered: RenderedVersion, frames: Iterable[int]):
    """Render `frames` of `write` in this session into its existing version
    `rendered` (frames broken on the farm). Only for a version rendered from
    the current state of the script: the new frames match the others and
    its manifest stays right. The version knob is put back, then re-sync (an
    unmodified script stays so)."""
    if not rendered.current:
        raise ValueError(f"v{rendered.version:03d} was rendered from another state of the script")
    previous = _int_knob(write, "versions")
    was_modified = nuke.modified()
    try:
        with busy():
            write["versions"].setValue(rendered.version)
        target = nodes.render_path(write)
        if os.path.normcase(os.path.normpath(target)) != os.path.normcase(os.path.normpath(rendered.path)):
            raise ValueError(f"{write.fullName()} now writes {target}, not into v{rendered.version:03d}")
        for first, last in frame_spans(frames):
            nuke.execute(write, first, last)
    finally:
        with busy():
            write["versions"].setValue(previous)
        sync([write])
        if not was_modified:
            nuke.modified(False)


def frame_spans(frames: Iterable[int]) -> List[Tuple[int, int]]:
    """[1001, 1002, 1003, 1050] -> [(1001, 1003), (1050, 1050)]."""
    spans = []
    for frame in sorted(set(frames)):
        if spans and frame == spans[-1][1] + 1:
            spans[-1] = (spans[-1][0], frame)
        else:
            spans.append((frame, frame))
    return spans


def _manifest_data(state: PrecompState, path: str) -> dict:
    return {
        "hash": state.hash,
        "renderpath": path,
        "first": state.needed[0],
        "last": state.needed[1],
        "node": state.name,
        "script": nuke.root().name(),
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def _int_knob(node, name) -> int:
    knob = node.knob(name)
    try:
        return int(knob.value()) if knob is not None else 0
    except (TypeError, ValueError):
        return 0


def _prism_refresh(write, log):
    """Prism `refresh` (getOutputPath) fills the base path the template derives from."""
    knob = write.knob("refresh")
    if knob is None or prism_core() is None:
        return
    try:
        knob.execute()
    except Exception as e:
        log(f"[precomp] {write.name()}: Prism refresh failed: {e}")


def report(states: Iterable[PrecompState]) -> str:
    return "\n".join(f"{s.name:30} {s.label:28} {s.reason}" for s in states)
