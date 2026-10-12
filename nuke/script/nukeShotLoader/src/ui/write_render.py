"""Render buttons of the PrecompWrite / Compo Write (their Prism tab).

Render: its Submit Job box decides, as with Prism's own button:
    ticked     the Render Manager's submission for that one Write, without
               opening the dialog: v1 precomps upgrade, the precomps upstream
               that are live offered along (rendered first, by render order),
               sanity check, then the Deadline submitter.
    unticked   a local render, as before: Prism's local render (for a
               PrecompWrite, on a new version prepared by the precomp
               engine — engine.render_here).

Render as previous version...: always a local render into an existing
version, whatever Submit Job says — to repair frames broken on the farm.

Open In Explorer: the folder of the Write's output.

The Writes get these buttons from the templates (toolsets/) and, in existing
scripts, from precomp.nodes.upgrade_prism_tabs() at script load.
"""

import os

import nuke

from ..core import project
from ..core.session import ShotSession
from ..precomp import engine, manifest, spec
from ..precomp.hashing import is_precomp_write
from ..scene import render_ops
from ..scene.utils import prism_core, script_path, upstream_nodes
from . import version_dialog, widgets
from .qt import QtWidgets
from .render_flow import NOT_RENDERABLE, RenderFlow

INCLUDE, ALONE = "include", "alone"


def submits(write) -> bool:
    """Submit Job ticked: the button goes to the farm."""
    knob = write.knob(spec.SUBMIT_JOB)
    return knob is not None and bool(knob.value())


def render_write(write):
    """The button: farm submission of `write` when its Submit Job box is
    ticked, with the live precomps upstream if the artist wants them (without
    them the upstream renders live inside the job, nothing is cached); a local
    render otherwise."""
    if not submits(write):
        render_local(write)
        return
    path = script_path()
    if path is None:
        nuke.message("Save the script before rendering.")
        return
    session = ShotSession(path)
    session.sequence, session.shot = project.detect_shot_context(path) or (None, None)
    flow = RenderFlow(session, QtWidgets.QApplication.activeWindow(), on_submitted=_refresh_render_manager)
    if flow.upgrade_before_render([write], f"Render {write.name()}"):
        _render(flow, write, None)


def render_local(write):
    """Submit Job unticked: what the button did before. Prism renders locally
    when the box is unticked; a PrecompWrite first gets its new version
    (engine.render_here). Without Prism, or on a Compo Write without the
    box: nuke.execute / Nuke's own Render dialog."""
    if is_precomp_write(write):
        engine.render_here(write)
        _refresh_render_manager()
        return
    plugin = getattr(prism_core(), "appPlugin", None)
    if plugin is not None and write.knob(spec.SUBMIT_JOB) is not None:
        render_ops.refresh_compo_write(write)   # Prism's render takes the version after its highest folder
        plugin.startRender(write)
    else:
        write["Render"].execute()


def render_previous_version(write):
    """"Render as previous version..." button: frames re-rendered into one of
    the Write's versions, in this session — never a farm submission, whatever
    Submit Job says (frames broken on the farm). The same dialog for both: a
    PrecompWrite offers its versions rendered from the current state of the
    script, a Compo Write every version folder next to its output."""
    parent = QtWidgets.QApplication.activeWindow()
    title = f"Render {write.name()} as previous version"
    precomp = is_precomp_write(write)
    if precomp:
        state = engine.evaluate([write])[0]
        if state.status in NOT_RENDERABLE:
            QtWidgets.QMessageBox.warning(parent, title, f"{write.name()} can't be rendered: {state.reason}.")
            return
        versions = engine.rendered_versions(state)
        nothing = (f"No version of {write.name()} was rendered from the current state of the script: "
                   "there are no frames to repair (Render makes a new version).")
    else:
        render_ops.refresh_compo_write(write)   # Prism: the output of this script's shot
        output, shot = render_ops.compo_output(write), _shot_folder()
        if output == "FileNotInPipeline":   # Prism's answer for a script outside its project
            QtWidgets.QMessageBox.warning(
                parent, title, "Prism doesn't find this script in its project: save it in the shot through "
                               "Prism first. Nothing rendered.")
            return
        if output and shot and not output.lower().startswith(shot.lower() + "/"):
            QtWidgets.QMessageBox.warning(
                parent, title, f"{write.name()} writes outside the shot of this script:\n{output}\n\n"
                               "Its versions are not this shot's: nothing rendered (check the script is saved in "
                               "the shot through Prism).")
            return
        versions = render_ops.compo_versions(write)
        nothing = (f"{write.name()} has no version on disk yet ({render_ops.compo_output(write) or 'no output'}): "
                   "there are no frames to repair (Render makes the first one).")
    if not any(v.current for v in versions):
        QtWidgets.QMessageBox.information(parent, title, nothing)
        return
    choice = version_dialog.PreviousVersionDialog(write.name(), versions, parent, state_checked=precomp).choose()
    if choice is None:
        return
    rendered, frames = choice
    print(f"[ShotAssetLoader] {title}: {version_dialog.version_name(rendered)}, "
          f"frames {version_dialog.format_frames(frames)}")
    try:
        if precomp:
            engine.render_into_version(write, rendered, frames)
        else:
            render_ops.render_compo_into_version(write, rendered, frames)
    except ValueError as e:
        QtWidgets.QMessageBox.warning(parent, title, f"Nothing rendered: {e}.")
    except RuntimeError as e:   # the artist cancelled the progress bar
        print(f"[ShotAssetLoader] {title} stopped: {e}")
    _refresh_render_manager()


def open_in_explorer(write):
    """"Open In Explorer" button: the folder of the Write's output. While that
    version isn't rendered (Prism shows the next one), the latest version
    on disk; without any, the nearest folder that exists."""
    path = render_ops.output_path(write)
    folder = os.path.dirname(path) if path else ""
    if folder and not os.path.isdir(folder):
        versions = manifest.version_folders(os.path.dirname(folder))   # newest first
        if versions:
            folder = versions[0][1]
    while folder and not os.path.isdir(folder) and os.path.dirname(folder) != folder:
        folder = os.path.dirname(folder)
    if not folder or not os.path.isdir(folder):
        nuke.message(f"No folder on disk for the output of {write.name()}:\n{path or '(empty)'}")
        return
    widgets.open_in_explorer(QtWidgets.QApplication.activeWindow(), [(write.name(), folder)])


def _shot_folder():
    """The shot folder of the saved script (Prism layout: <shot>/Scenefiles/...), None otherwise."""
    path = (script_path() or "").replace("\\", "/")
    return path.split("/Scenefiles/")[0] if "/Scenefiles/" in path else None


def _render(flow, write, upstream_choice):
    """`upstream_choice`: INCLUDE / ALONE, asked when None (and kept for the
    run that follows a sanity fix)."""
    source = f"Render {write.name()}"
    precomp = is_precomp_write(write)
    states = engine.sync()
    own = [s for s in states if s.write == write]   # (node wrappers compare equal, not identical)
    if precomp and (not own or own[0].status in NOT_RENDERABLE):
        reason = own[0].reason if own else "not a precomp of this script"
        QtWidgets.QMessageBox.warning(flow.parent, source, f"{write.name()} can't be rendered: {reason}.")
        return
    upstream = upstream_nodes(write)
    live = [s for s in states if s.write != write and s.write in upstream
            and s.needs_render and s.status not in NOT_RENDERABLE]

    if live and upstream_choice is None:
        upstream_choice = _ask_upstream(flow.parent, write, live)
        if upstream_choice is None:
            print(f"[ShotAssetLoader] {source} cancelled")
            return
    chosen = own + (live if upstream_choice == INCLUDE else [])
    compos = [] if precomp else [write]
    print(f"[ShotAssetLoader] {source}: " + ", ".join([s.name for s in chosen] + [c.name() for c in compos]))
    flow.submit(chosen, compos, source, retry=lambda: _render(flow, write, upstream_choice or ALONE))


def _ask_upstream(parent, write, live):
    names = "\n  ".join(f"{s.name}   ({s.label})" for s in live[:12]) + ("\n  ..." if len(live) > 12 else "")
    buttons = QtWidgets.QMessageBox
    reply = buttons.question(
        parent, f"Render {write.name()}",
        f"{len(live)} precomp(s) upstream of {write.name()} are live (no valid cache):\n  {names}\n\n"
        "Render them too?\n"
        "Yes: they render first (render order), then this Write reads their renders.\n"
        f"No: only {write.name()}; the precomps render live inside its job, nothing is cached.",
        buttons.Yes | buttons.No | buttons.Cancel, buttons.Yes)
    if reply == buttons.Yes:
        return INCLUDE
    if reply == buttons.No:
        return ALONE
    return None


def _refresh_render_manager():
    try:
        from . import main_window
        window = main_window._instance
        if window is not None and window.isVisible():
            window.render_tab.request_refresh()
    except Exception as e:
        print(f"[ShotAssetLoader] Render Manager not refreshed: {e}")
