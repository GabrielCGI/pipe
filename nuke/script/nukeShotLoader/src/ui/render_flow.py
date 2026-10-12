"""What a render goes through before Deadline, shared by the Render Manager
and by the Render button of the Writes (write_render.py): v1 precomps
upgrade, sanity check, submission, and what to tell the artist after."""

import os

from ..core.config import Config
from ..precomp import engine
from ..precomp import nodes as precomp_nodes
from ..precomp.engine import Status
from ..sanity import rules as sanity_rules
from ..scene import render_ops
from ..scene.utils import upstream_nodes
from . import sanity_dialog
from .qt import QtCore, QtWidgets

NOT_RENDERABLE = (Status.LEGACY, Status.NO_INPUT, Status.ERROR)


class RenderFlow:
    """`parent`: the widget the dialogs open on. `on_submitted`: called after
    every submission attempt (refresh). `on_upgrade`: upgrades the script's
    v1 precomps (default: upgrade + sync)."""

    def __init__(self, session, parent=None, on_submitted=None, on_upgrade=None):
        self.session = session
        self.parent = parent
        self.on_submitted = on_submitted or (lambda: None)
        self.on_upgrade = on_upgrade or _upgrade_scene
        self.sanity_fixed = False   # a render action is running again after sanity fixes

    # ---- submission -----------------------------------------------------

    def submit(self, states, compos, source, retry):
        """`retry`: the render action itself, run again when the sanity check
        fixed something (precomp states computed before the fix are stale);
        that second run only shows the sanity check if a rule still fails."""
        outcome = self.sanity_check([s.write for s in states] + [c for c in compos if c is not None], source)
        if outcome == sanity_dialog.CANCELLED:
            print(f"[ShotAssetLoader] {source} cancelled: sanity check closed")
            return
        if outcome == sanity_dialog.FIXED:
            print(f"[ShotAssetLoader] {source}: sanity fixes applied, going on from the fixed script")
            QtCore.QTimer.singleShot(0, lambda: self.retry_after_fix(retry))
            return
        root = self.session.project_root
        outcome = render_ops.submit(states, compos, source, root)
        if outcome == render_ops.UNAVAILABLE:
            reply = QtWidgets.QMessageBox.question(
                self.parent, "Deadline unavailable",
                "No Deadline submitter in this Nuke session (e.g. vanilla Nuke without the "
                "pipeline), nothing was changed.\n\nRender locally in this session instead?\n"
                "Precomps first, then the compo, in render order.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                return
            render_ops.submit(states, compos, source, root, local=True)
        elif outcome == render_ops.CANCELLED:
            print(f"[ShotAssetLoader] {source}: nothing submitted, precomps left as they were")
        elif outcome == render_ops.PARTIAL:
            missing = "\n".join(f"  {name}: {why}" for name, why in render_ops.LAST_MISSING[:12])
            QtWidgets.QMessageBox.warning(
                self.parent, "Submission incomplete",
                f"Deadline didn't get every job of this submission. Left out:\n{missing}\n\n"
                "The precomps left out are back as they were (not 'Submitted'). The jobs that did go "
                "are on the farm. Render again what is missing (details in the Script Editor).")
        elif outcome == render_ops.FAILED:
            QtWidgets.QMessageBox.warning(
                self.parent, "Nothing submitted",
                "Deadline took none of the jobs (its answer is in the Script Editor).\n"
                "The precomps were left as they were.")
        self.on_submitted()

    def retry_after_fix(self, retry):
        self.sanity_fixed = True
        try:
            retry()
        finally:
            self.sanity_fixed = False

    def sanity_check(self, writes, source) -> str:
        """Run the sanity rules on what `writes` render (see src/sanity)."""
        session = self.session
        shot_folder = (os.path.join(session.project_root, *Config.SHOTS_PATH.split("/"), session.sequence, session.shot)
                       if session.has_shot else None)
        context = sanity_rules.Context(writes, shot_folder=shot_folder)
        return sanity_dialog.run(sanity_rules.RULES, context, source, self.parent, quiet=self.sanity_fixed)

    # ---- v1 precomps ----------------------------------------------------

    @staticmethod
    def legacy_precomps(roots):
        """v1 precomps a render of the Writes `roots` involves: among them or
        upstream of them."""
        roots = [r for r in roots if r is not None]
        involved = set(roots)
        for root in roots:
            involved |= upstream_nodes(root)
        return [s for s in engine.evaluate() if s.status == Status.LEGACY and s.write in involved]

    def upgrade_before_render(self, roots, source) -> bool:
        """True when the render can go on: no v1 precomp involved, or the
        artist agreed to upgrade the script's precomps first."""
        legacy = self.legacy_precomps(roots)
        if not legacy:
            return True
        names = "\n  ".join(s.name for s in legacy[:10]) + ("\n  ..." if len(legacy) > 10 else "")
        reply = QtWidgets.QMessageBox.question(
            self.parent, "Upgrade Precomps",
            f"This render uses {len(legacy)} precomp(s) still on the v1 setup:\n  {names}\n\n"
            "Upgrade the script's precomps to v2 now, then render?\n"
            "No: nothing is rendered.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply != QtWidgets.QMessageBox.Yes:
            print(f"[ShotAssetLoader] {source} cancelled: v1 precomps not upgraded")
            return False
        self.on_upgrade()
        return True


def _upgrade_scene():
    for line in precomp_nodes.upgrade_scene():
        print(f"[precomp] upgraded {line}")
    engine.sync()
