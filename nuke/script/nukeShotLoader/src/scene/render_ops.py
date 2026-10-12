"""Render Manager scene operations: Write discovery, render order and the
Deadline submission pipeline. Precomp caching lives in src/precomp."""

import contextlib
import getpass
import json
import os
import re
import time
from typing import List, Set, Tuple

import nuke

from ..precomp import engine, manifest
from ..precomp.hashing import is_precomp_write
from . import deadline
from .render_order import distribute_write_render_order, order_from_upstream
from .utils import execute_button, no_undo, prism_core, select_only, silent_popups, upstream_nodes

# submit() outcomes
SUBMITTED, RENDERED, CANCELLED, FAILED, UNAVAILABLE = "submitted", "rendered", "cancelled", "failed", "unavailable"
PARTIAL = "partial"
# After a PARTIAL submit(): (Write name, why it has no job) for each Write left out.
LAST_MISSING = []


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def scan_writes() -> Tuple[List, List]:
    """(precomp writes, compo writes). Precomps are identified by the gizmo
    tag (survives renames), compo writes by 'Compo' in their name. Groups
    are searched so precomps wrapped in a studio gizmo are found too."""
    precomps, compos = [], []
    for node in nuke.allNodes("Write", recurseGroups=True):
        if is_precomp_write(node):
            precomps.append(node)
        elif "Compo" in node.name():
            compos.append(node)
    return precomps, compos


def find_compo_write():
    _, compos = scan_writes()
    return compos[0] if compos else None


def in_stream(nodes, compo_write, action: str, keep_without_compo: bool = False) -> List:
    """Drop precomps that don't feed the Compo Write ('Out of stream')."""
    if compo_write is None and keep_without_compo:
        return list(nodes)
    upstream = upstream_nodes(compo_write)
    kept = []
    for node in nodes:
        if compo_write is None or node not in upstream:
            print(f"[ShotAssetLoader]   {node.name()}: Out of stream (skipped from {action})")
        else:
            kept.append(node)
    return kept


def out_of_stream(nodes, compo_write) -> List:
    """Precomps that don't feed the Compo Write (all of them without one)."""
    upstream = upstream_nodes(compo_write)
    return [n for n in nodes if compo_write is None or n not in upstream]


# ---------------------------------------------------------------------------
# Render order
# ---------------------------------------------------------------------------

def distribute_render_orders(compo_write):
    """Precomps render before the comp: topological render_order upstream
    of the Compo Write."""
    if compo_write is None:
        print("[ShotAssetLoader] No Compo Write found in the scene — skipping render_order distribution")
        return
    try:
        distribute_write_render_order(compo_write)
    except Exception as e:
        print(f"[ShotAssetLoader] distribute_write_render_order failed: {e}")


def order_out_of_stream(precomp_writes, compo_write) -> Set[str]:
    """fullNames of the precomps not feeding the Compo Write, whose
    render_order the distribution from the compo skipped: computed from
    their own upstream instead (after every Write they read). Call after
    distribute_render_orders()."""
    out = out_of_stream(precomp_writes, compo_write)
    if out:
        order_from_upstream(out)
    return {node.fullName() for node in out}


def refresh_compo_write(node) -> str:
    """Point the Compo Write at a new version: the one after its last real
    version (rendered, or submitted to the farm) — a render never goes into
    a version in use, nor skips one. Returns the output set.

    Prism's `refresh` computes it, but Prism marks a Write "rendering" when
    a render of it starts and only its own afterRender hook clears that:
    while marked, every refresh returns that render's path and leaves
    `fileName` alone. The mark is cleared first; the unused version folders
    above the last real one are released (release_unused_versions); the
    result is checked against the folders on disk (without Prism: the path
    is moved to that version, Prism's naming kept)."""
    if node is None:
        return ""
    plugin = getattr(prism_core(), "appPlugin", None)
    if plugin is None:
        print(f"[ShotAssetLoader] Prism not loaded — {node.name()} output checked on disk only")
    else:
        try:
            plugin.finishedRendering(node)
        except Exception as e:
            print(f"[ShotAssetLoader] {node.name()}: Prism's rendering mark not cleared ({e})")
    output = compo_output(node)
    if _VERSION_DIR_RE.match(os.path.basename(os.path.dirname(output))):
        for name in release_unused_versions(os.path.dirname(os.path.dirname(output))):
            print(f"[ShotAssetLoader] {node.name()}: unused version folder {name} released")
    if plugin is not None:
        execute_button(node, 'refresh', warn_missing=True)
    return ensure_next_version(node)


# In a Compo version folder: Prism's file, written whenever a Write gets its
# path for a render — also by the temporary Write of every flipbook (Prism
# puts its knobs on any Write created, identifier = the scene's task), e.g.
# the scene thumbnail of each Prism Save Version. Alone, it marks a version
# folder nothing was rendered into.
PRISM_VERSION_INFO = "versioninfo.json"
# Written in the version folder of a Compo Write submitted to the farm: in
# use although no frame is there yet.
SUBMITTED_MARKER = "shotloader_submitted.json"


def release_unused_versions(root) -> List[str]:
    """Remove the version folders above the last one in use that hold
    nothing but Prism's versioninfo.json (or nothing): "the version after
    the highest one" is then the one after the last real version, for Prism
    as for us. Returns the folder names removed."""
    removed = []
    for _, folder in manifest.version_folders(root):   # newest first
        try:
            names = set(os.listdir(folder))
        except OSError:
            break
        if not names <= {PRISM_VERSION_INFO}:
            break
        try:
            for name in names:
                os.remove(os.path.join(folder, name))
            os.rmdir(folder)
        except OSError as e:
            print(f"[ShotAssetLoader] {folder} not released: {e}")
            break
        removed.append(os.path.basename(folder))
    return removed


def mark_submitted(compos, scene: str):
    """The version folders of Compo Writes just submitted: in use from now on."""
    for compo in compos:
        folder = os.path.dirname(compo_output(compo))
        if not _VERSION_DIR_RE.match(os.path.basename(folder)):
            continue
        try:
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, SUBMITTED_MARKER), "w", encoding="utf-8") as fh:
                json.dump({"scene": scene, "write": compo.fullName(), "user": getpass.getuser(),
                           "submitted": time.strftime("%Y-%m-%dT%H:%M:%S")}, fh, indent=1)
        except OSError as e:
            print(f"[ShotAssetLoader] {compo.name()}: submission not marked in {folder} ({e})")


_VERSION_DIR_RE = re.compile(r"^v(\d+)$")


def ensure_next_version(node) -> str:
    """The Compo Write's output in the version after the highest version
    folder next to it (moved there when it isn't). Returns the output."""
    output = compo_output(node)
    folder = os.path.dirname(output)
    token = os.path.basename(folder)
    match = _VERSION_DIR_RE.match(token)
    if not match:
        print(f"[ShotAssetLoader] {node.name()}: no version in its output ({output or 'empty'}), left as is")
        return output
    wanted = max((v for v, _ in manifest.version_folders(os.path.dirname(folder))), default=0) + 1
    if int(match.group(1)) == wanted:
        return output
    new_token = "v" + str(wanted).zfill(len(match.group(1)))
    new_output = "/".join((os.path.dirname(folder).replace("\\", "/"), new_token,
                           os.path.basename(output).replace(token, new_token)))
    (node.knob("fileName") or node["file"]).setValue(new_output)
    print(f"[ShotAssetLoader] {node.name()}: output {token} -> {new_token} (the version after the highest one on disk)")
    return new_output


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

def submit(precomp_states, compos, source: str, project_root: str, local: bool = False) -> str:
    """Farm submission (or, with `local`, a render in this session).

    SUBMITTED: jobs are on the farm (RENDERED for a local render).
    CANCELLED / FAILED: the artist left the Deadline submitter without
    submitting / Deadline took no job — the precomps are put back as they
    were (no new version, nothing 'Submitted').
    UNAVAILABLE: no Deadline submitter in this session, nothing touched."""
    compos = [c for c in compos if c is not None]
    if local:
        with engine.busy():
            prepared, targets = _prepare(precomp_states, compos)
            render_locally(targets)
        engine.discard_renders(prepared)   # render stopped before some precomps: their versions released
        engine.sync()
        return RENDERED
    submitter = deadline.find_submitter()
    if submitter is None:
        return UNAVAILABLE
    prepared, targets = prepare_farm_render(precomp_states, compos)
    with engine.busy():
        names = select_only(targets)
        print(f"[ShotAssetLoader] Selected for submit: {', '.join(names) or '(none)'}")
        print(f"[ShotAssetLoader] {source} -> Submit Nuke To Deadline")
        deadline.prime_sticky(project_root)
        sent = deadline.run_submitter(submitter, keep_selected=targets)
    missing = _missing_jobs(targets) if sent == deadline.SENT else []
    sent_names = {t.fullName() for t in targets} - {name for name, _ in missing}
    if sent == deadline.SENT:
        mark_submitted([c for c in compos if c.fullName() in sent_names], nuke.root().name())
    unsent = [p for p in prepared if sent != deadline.SENT or p.state.write.fullName() not in sent_names]
    for item in engine.discard_renders(unsent):
        print(f"[precomp] {item.state.name}: v{item.version:03d} kept, frames already in {item.folder}")
    engine.sync()  # GUI: back to what is on disk now (the new renders don't exist yet)
    LAST_MISSING[:] = missing
    if missing:
        print("[ShotAssetLoader] Submission INCOMPLETE — no job for: "
              + "; ".join(f"{name} ({why})" for name, why in missing))
        return PARTIAL
    return {deadline.SENT: SUBMITTED, deadline.FAILED: FAILED}.get(sent, CANCELLED)


def _missing_jobs(targets) -> list:
    """(Write name, why) for the Writes the submitter didn't get a job for."""
    if not deadline.LAST_JOBS:   # the submitter stopped before its first job, or sent none we saw
        if not deadline.LAST_ERROR:
            return []
        return [(t.name(), f"not sent by the submitter ({deadline.LAST_ERROR})") for t in targets]
    answers = {}
    for name, taken, answer in deadline.LAST_JOBS:
        answers[name] = "" if taken or answers.get(name) == "" else answer
    if not any(name for name, _, _ in deadline.LAST_JOBS):
        return []   # jobs not attributable to Writes: nothing to tell
    missing = []
    for target in targets:
        answer = answers.get(target.fullName())
        if answer == "":
            continue
        why = (f"refused by Deadline: {answer}" if answer
               else f"not sent by the submitter{' (' + deadline.LAST_ERROR + ')' if deadline.LAST_ERROR else ''}")
        missing.append((target.name(), why))
    return missing


def prepare_farm_render(precomp_states, compos, save=None) -> Tuple[List, List]:
    """Put the script in the state the farm must render, and save it.

    The precomps to render get a new version and a manifest, and their
    switches are routed to the frames that render will produce, so every
    farm task (precomps first by render_order, then the compo) renders
    exactly that saved state — nothing is decided on the farm. `save`
    defaults to save_script_version. Returns (prepared precomp renders —
    what engine.discard_renders() undoes —, Writes to submit)."""
    compos = [c for c in compos if c is not None]
    with engine.busy():
        # Before the thumbnail: Prism's thumbnail of a viewer showing the
        # Compo Write creates the folder of the version after the highest one
        # — the one set here, not one more.
        outputs = {compo: refresh_compo_write(compo) for compo in compos}
    with engine.busy(), scene_thumbnail():
        prepared, targets = _prepare(precomp_states, compos, refresh=False)
        (save or save_script_version)()
        engine.finalize_manifests(prepared)
        _keep_outputs(outputs)
    return prepared, targets


def _keep_outputs(outputs):
    """The saved script must render where refresh_compo_write pointed the
    Compo Writes: put back (and saved again) when the save changed them."""
    moved = [compo for compo, output in outputs.items() if output and compo_output(compo) != output]
    for compo in moved:
        print(f"[ShotAssetLoader] {compo.name()}: output changed by the save ({compo_output(compo)}), "
              f"set back to {outputs[compo]}")
        (compo.knob("fileName") or compo["file"]).setValue(outputs[compo])
    if moved:
        try:
            nuke.scriptSaveAs(nuke.root().name(), overwrite=1)
        except Exception as e:
            print(f"[ShotAssetLoader] Script save failed: {e}")


@contextlib.contextmanager
def scene_thumbnail():
    """Prism's scene thumbnail, taken now and served to the saves made inside
    the block.

    When Prism saves a version it renders the viewer's input for the
    thumbnail. A submission saves with the precomp switches routed to
    renders that don't exist yet, so that render fails on their CacheRead
    ("Flipbook render failed"). The script is still in its live state when
    the block starts: the thumbnail is rendered here instead."""
    plugin = getattr(prism_core(), "appPlugin", None)
    capture = getattr(plugin, "captureViewportThumbnail", None)
    if capture is None:
        yield
        return
    pixmap = None
    try:
        if prism_core().getConfig("globals", "capture_viewport", config="user", dft=True):
            with silent_popups("scene thumbnail", linger_ms=0), _no_prism_write_knobs():
                pixmap = capture()
    except Exception as e:
        print(f"[ShotAssetLoader] Scene thumbnail not captured: {e}")
    plugin.captureViewportThumbnail = lambda: pixmap
    try:
        yield
    finally:
        try:
            del plugin.captureViewportThumbnail   # back to Prism's own method
        except AttributeError:
            pass


@contextlib.contextmanager
def _no_prism_write_knobs():
    """Prism's switch (read at each node creation) that keeps it from putting
    its knobs on the temporary Write of the thumbnail's flipbook — whose
    render would otherwise create an unused Compo version folder."""
    previous = os.environ.get("PRISM_NUKE_WRITE_ADD_KNOBS")
    os.environ["PRISM_NUKE_WRITE_ADD_KNOBS"] = "0"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PRISM_NUKE_WRITE_ADD_KNOBS", None)
        else:
            os.environ["PRISM_NUKE_WRITE_ADD_KNOBS"] = previous


def _prepare(precomp_states, compos, refresh=True):
    """(prepared precomp renders, Writes to render)."""
    prepared = engine.prepare_renders(precomp_states)
    for compo in compos if refresh else ():
        refresh_compo_write(compo)
    compo = compos[0] if compos else find_compo_write()
    distribute_render_orders(compo)
    order_out_of_stream(scan_writes()[0], compo)
    return prepared, [p.state.write for p in prepared] + list(compos)


def render_locally(writes):
    """Render `writes` in this session, in render_order (precomps before the
    compo that reads them). Stops at the first failure."""
    for write in sorted(writes, key=lambda w: (int(w["render_order"].value()), w.name())):
        first, last = _frame_range(write)
        print(f"[ShotAssetLoader] Local render {write.name()} {first}-{last}")
        try:
            nuke.execute(write, first, last)
        except Exception as e:  # includes the artist cancelling the progress bar
            print(f"[ShotAssetLoader] Local render of {write.name()} stopped: {e}")
            return False
    return True


def _frame_range(write):
    if write.knob("use_limit") is not None and write["use_limit"].value():
        return int(write["first"].value()), int(write["last"].value())
    root = nuke.root()
    return int(root["first_frame"].value()), int(root["last_frame"].value())


# ---------------------------------------------------------------------------
# Compo versions ("Render as previous version...")
# ---------------------------------------------------------------------------

_FRAME_FILE_RE = re.compile(r"^(.*?)(\d+)\.([A-Za-z0-9]+)$")


def compo_output(write) -> str:
    """The Compo Write's output pattern (Prism's `fileName`, else `file`)."""
    knob = write.knob("fileName") or write.knob("file")
    return (knob.value() or "").replace("\\", "/") if knob is not None else ""


def output_path(write) -> str:
    """Where a PrecompWrite / Compo Write renders now: the precomp's
    `renderpath`, Prism's `fileName`, else `file` (evaluated)."""
    knob = write.knob("renderpath") or write.knob("fileName") or write.knob("file")
    return (knob.value() or "").replace("\\", "/") if knob is not None else ""


def compo_versions(write) -> List[engine.RenderedVersion]:
    """The versions of a Compo Write on disk (the v### folders next to its
    output, Prism's layout), newest first, with the frames of its current
    range missing in each. No manifest for a compo: all `current`."""
    output = compo_output(write)
    if not output:
        return []
    root, token = os.path.dirname(os.path.dirname(output)), os.path.basename(os.path.dirname(output))
    first, last = _frame_range(write)
    wanted = set(range(first, last + 1))
    found = []
    for version, folder in manifest.version_folders(root):
        name = os.path.basename(folder)
        path, frames = _frame_sequence(folder, _file_extension(write))
        if path is None:   # nothing rendered in it: Prism's naming for that version
            path, frames = os.path.join(folder, os.path.basename(output).replace(token, name)), set()
        found.append(engine.RenderedVersion(version, path.replace("\\", "/"), first, last,
                                            sorted(wanted - frames), True))
    return found


def _file_extension(write) -> str:
    knob = write.knob("file_type")
    return str(knob.value()).lower() if knob is not None and knob.value() else "exr"


def _frame_sequence(folder, extension) -> Tuple:
    """(pattern with ####, frames) of the biggest `extension` sequence in
    `folder`, (None, set()) without one."""
    sequences = {}
    try:
        names = os.listdir(folder)
    except OSError:
        names = []
    for name in names:
        m = _FRAME_FILE_RE.match(name)
        if m and m.group(3).lower() == extension:
            sequences.setdefault((m.group(1), len(m.group(2)), m.group(3)), set()).add(int(m.group(2)))
    if not sequences:
        return None, set()
    (prefix, padding, ext), frames = max(sequences.items(), key=lambda item: len(item[1]))
    return os.path.join(folder, f"{prefix}{'#' * padding}.{ext}"), frames


def render_compo_into_version(write, rendered: engine.RenderedVersion, frames):
    """Render `frames` of the Compo Write in this session into its existing
    version `rendered` (compo_versions()). Its output points there for the
    render, with Prism's beforeRender off (it would point it at a new
    version); both are put back after, and an unmodified script stays so."""
    output = write.knob("fileName") or write["file"]
    hook = write.knob("beforeRender")
    saved_output = output.getText() if hasattr(output, "getText") else output.value()
    saved_hook = hook.value() if hook is not None else None
    was_modified = nuke.modified()
    try:
        with no_undo():
            output.setValue(rendered.path)
            if hook is not None:
                hook.setValue("")
        for first, last in engine.frame_spans(frames):
            nuke.execute(write, first, last)
    finally:
        with no_undo():
            output.setValue(saved_output)
            if hook is not None:
                hook.setValue(saved_hook)
        if not was_modified:
            nuke.modified(False)


def _menu_item(path):
    try:
        return nuke.menu("Nuke").findItem(path)
    except RuntimeError:  # no menus outside the GUI
        return None


def save_script_version():
    """Every farm submit is pinned to a freshly saved .nk: Prism 'Save
    Version' when available, else a plain save."""
    item = _menu_item("Prism/Save Version")
    if item is None:
        print("[ShotAssetLoader] Prism/Save Version not found — saving the current script")
        try:
            # scriptSave() skips "unmodified" scripts, and the modified flag
            # is not tracked outside the GUI: always write the file.
            nuke.scriptSaveAs(nuke.root().name(), overwrite=1)
        except Exception as e:
            print(f"[ShotAssetLoader] Script save failed: {e}")
        return
    try:
        item.invoke()
        print("[ShotAssetLoader] Prism Save Version invoked")
    except Exception as e:
        print(f"[ShotAssetLoader] Prism Save Version failed: {e}")
