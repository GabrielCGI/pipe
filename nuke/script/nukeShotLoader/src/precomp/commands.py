"""Menu commands of the precomp system."""

import os

import nuke

from ..scene.utils import no_undo
from . import engine, nodes, spec

TOOLSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "toolsets")


def refresh():
    states = engine.sync()
    print(engine.report(states) or "[precomp] No PrecompWrite in the script")


def upgrade():
    report = nodes.upgrade_scene()
    engine.sync()
    nuke.message("Script upgraded:\n\n" + "\n".join(report) if report
                 else "Nothing to upgrade in this script (no v1 precomp, Prism tabs up to date).")


def upgrade_prism_tabs():
    """On script load (GUI): the Prism tab of the Compo / Precomp Writes
    upgraded in place (nodes.upgrade_prism_tabs). Not undoable, and an
    unmodified script stays unmodified: the change is saved with the next
    save (and redone at each load until then)."""
    was_modified = nuke.modified()
    with no_undo():
        changed = nodes.upgrade_prism_tabs()
    for name in changed:
        print(f"[precomp] {name}: Shot Loader Prism tab")
    if changed and not was_modified:
        nuke.modified(False)


def lock_version_display():
    """knobChanged of the Writes (GUI): the version of the Prism tab can't be
    typed over. Nuke doesn't save the READ_ONLY flag with the script: set
    when the panel opens."""
    knob = nuke.thisKnob()
    if knob is None or knob.name() != "showPanel":
        return
    version = nuke.thisNode().knob(spec.VERSION_DISPLAY)
    if version is not None and not version.getFlag(nuke.READ_ONLY):
        version.setFlag(nuke.READ_ONLY)


def insert_precomp():
    """Paste the v2 PrecompWrite + switch after the selected node."""
    nuke.nodePaste(os.path.join(TOOLSETS, "WritePrecomp.nk"))
    engine.sync()


def insert_compo_write():
    nuke.nodePaste(os.path.join(TOOLSETS, "WriteCompo.nk"))
