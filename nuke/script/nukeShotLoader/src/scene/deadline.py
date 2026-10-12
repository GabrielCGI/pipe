"""The Deadline submitter of this Nuke session: lookup, defaults, and
whether a run of it really sent jobs to the farm."""

import configparser
import os
import sys
import threading

import nuke

from ..core.config import Config
from ..core import project

SENT, CANCELLED, FAILED = "sent", "cancelled", "failed"
_SUBMITTER_MODULE = "SubmitNukeToDeadline"


def find_submitter():
    """Deadline's Nuke client entry point, None when Deadline isn't set up in
    this session. DeadlineNukeClient.main() imports SubmitNukeToDeadline from
    the repository, where the Illogic fork (Writes grouped by render_order so
    siblings render in parallel) is deployed under that stock name."""
    try:
        import DeadlineNukeClient  # type: ignore
        return DeadlineNukeClient.main
    except ImportError:
        pass
    try:
        item = nuke.menu("Nuke").findItem("Thinkbox/Submit Nuke To Deadline")
    except RuntimeError:  # no menus outside the GUI
        item = None
    if item is None:
        print("[ShotAssetLoader] No Deadline submitter in this Nuke session")
        return None
    return item.invoke


def prime_sticky(project_root: str):
    """Pre-fill the submitter with the project pool/group + studio defaults.

    The submitter reads the sticky .ini at startup, then lets hidden root
    knobs from previous submissions override it — so both are written
    (root knobs only when they already exist)."""
    pool, group = project.deadline_pool(project_root)
    values = dict(Config.DEADLINE_STICKY)
    if group:
        values = {"Group": group, **values}
    if pool:
        values = {"Pool": pool, **values}

    sticky_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Thinkbox", "Deadline10",
                               "settings", "nuke_py_submission.ini")
    try:
        os.makedirs(os.path.dirname(sticky_path), exist_ok=True)
        config = configparser.ConfigParser()
        if os.path.isfile(sticky_path):
            config.read(sticky_path)
        if not config.has_section("Sticky"):
            config.add_section("Sticky")
        for key, value in values.items():
            config.set("Sticky", key, value)
        with open(sticky_path, "w") as fh:
            config.write(fh)
        print(f"[ShotAssetLoader] Deadline sticky primed (pool={pool} group={group}) at {sticky_path}")
    except Exception as e:
        print(f"[ShotAssetLoader] Could not prime Deadline sticky: {e}")

    root = nuke.root()
    updated = []
    for name, value in values.items():
        knob = root.knob(name)
        if knob is None:
            continue
        try:
            knob.setValue(value)
            updated.append(name)
        except Exception as e:
            print(f"[ShotAssetLoader] Could not update root knob {name}: {e}")
    if updated:
        print(f"[ShotAssetLoader] Root sticky knobs overridden: {', '.join(updated)}")


# ---------------------------------------------------------------------------
# Did the submitter submit?
# ---------------------------------------------------------------------------

# What the last run_submitter() saw: one (Write full name, taken by Deadline,
# Deadline's answer when not) per job the submitter sent, and the error that
# stopped the submitter if one did.
LAST_JOBS = []
LAST_ERROR = None


def run_submitter(submitter, keep_selected=None) -> str:
    """Run the (modal) submitter. SENT, CANCELLED (the artist closed its
    dialog or refused one of its questions, or it gave up before showing it)
    or FAILED (Deadline took none of the jobs). LAST_JOBS / LAST_ERROR tell
    which Writes got a job.

    The studio submitter only sends the selected Writes, checked in its loop
    just before each job: `keep_selected` (the Writes to send) are selected
    again after each job, whatever touched the selection meanwhile.

    The submitter returns nothing either way and writes its sticky settings
    on Cancel too, so its run is observed (see _SubmissionProbe). A submitter
    that can't be observed counts as SENT: wrongly dropping the version of
    jobs that are on the farm would be worse than a stale 'Submitted'."""
    global LAST_JOBS, LAST_ERROR
    LAST_ERROR = None
    with _SubmissionProbe(keep_selected) as probe:
        try:
            submitter()
        except Exception as e:
            LAST_ERROR = f"{type(e).__name__}: {e}"
            print(f"[ShotAssetLoader] Deadline submitter failed: {LAST_ERROR}")
    LAST_JOBS = list(probe.jobs)
    for name, taken, answer in LAST_JOBS:
        print(f"[ShotAssetLoader]   job {name or '?'}: " + ("taken by Deadline" if taken else f"REFUSED — {answer}"))
    outcome = probe.outcome
    print(f"[ShotAssetLoader] Deadline submitter: {outcome} ({probe.summary})")
    return outcome


class _SubmissionProbe:
    """Observes one run of SubmitNukeToDeadline.SubmitToDeadline():

      - its dialog is a nukescripts.PythonPanel shown by showModalDialog(),
        which returns False on Cancel (the dialog comes back after an input
        error: the last answer counts);
      - after OK it can still give up on a nuke.ask() the artist refuses
        (warnings, Writes without a render order);
      - every job then goes through SubmitJob(), which returns
        deadlinecommand's answer — 'JobID=...' when Deadline took the job.
        With 'separate job dependencies' (the studio default) the jobs are
        sent before the submitter returns, otherwise from threads that may
        still be running when it does.
    """

    def __init__(self, keep_selected=None):
        self.keep_selected = list(keep_selected or [])
        self.jobs = []            # (Write full name, taken, Deadline's answer when not)
        self.dialogs = 0          # times the submitter dialog was shown
        self.accepted = False     # last one closed with OK
        self.refused = False      # a question asked after OK was answered No
        self.jobs_started = self.jobs_finished = self.jobs_taken = 0
        self._watching = False    # the dialog hook is in place
        self._patched = []        # (owner, name, original, owner had it)

    def __enter__(self):
        try:
            import nukescripts
            self._watching = self._patch(nukescripts.PythonPanel, "showModalDialog", self._show_dialog)
        except Exception as e:
            print(f"[ShotAssetLoader] Deadline dialog not observable: {e}")
        self._patch(nuke, "ask", self._ask)
        return self

    def __exit__(self, *exc):
        for owner, name, original, own in reversed(self._patched):
            if own:
                setattr(owner, name, original)
            else:
                delattr(owner, name)
        return False

    def _patch(self, owner, name, wrap) -> bool:
        original = getattr(owner, name, None)
        if not callable(original):
            return False
        self._patched.append((owner, name, original, name in vars(owner)))
        setattr(owner, name, wrap(original))
        return True

    def _show_dialog(self, original):
        def showModalDialog(panel, *args, **kwargs):
            self._watch_jobs(sys.modules.get(type(panel).__module__))
            self.dialogs += 1
            answer = original(panel, *args, **kwargs)
            self.accepted, self.refused = bool(answer), False
            return answer
        return showModalDialog

    def _ask(self, original):
        def ask(*args, **kwargs):
            answer = original(*args, **kwargs)
            if self.accepted and not answer:
                self.refused = True
            return answer
        return ask

    def _watch_jobs(self, module):
        """Count the jobs of the module showing the dialog (known once it does)."""
        if module is None or any(owner is module for owner, *_ in self._patched):
            return

        def wrap(original):
            def SubmitJob(*args, **kwargs):
                self.jobs_started += 1
                name = _write_name(list(args) + list(kwargs.values()))
                answer = None
                try:
                    answer = original(*args, **kwargs)
                finally:
                    self.jobs_finished += 1
                    taken = "JobID=" in str(answer or "")
                    self.jobs.append((name, taken, "" if taken else _short_answer(answer)))
                    self._reselect()
                if taken:
                    self.jobs_taken += 1
                return answer
            return SubmitJob
        self._patch(module, "SubmitJob", wrap)

    def _reselect(self):
        if not self.keep_selected or threading.current_thread() is not threading.main_thread():
            return
        for node in self.keep_selected:
            try:
                if not node.isSelected():
                    print(f"[ShotAssetLoader]   {node.name()} was deselected during the submission: selected again")
                    node.setSelected(True)
            except Exception:
                pass

    @property
    def outcome(self) -> str:
        if not self.dialogs:
            # The known submitter always asks before sending anything: it gave
            # up earlier (script not saved, no Write, Deadline unreachable).
            return CANCELLED if self._watching and _SUBMITTER_MODULE in sys.modules else SENT
        if not self.accepted or self.refused:
            return CANCELLED
        if self.jobs_started and self.jobs_finished == self.jobs_started and not self.jobs_taken:
            return FAILED
        return SENT

    @property
    def summary(self) -> str:
        if not self.dialogs:
            return "its dialog was not shown" if self._watching else "not observable"
        if not self.accepted:
            return "dialog cancelled"
        if self.refused:
            return "dialog validated, then a question refused"
        return (f"dialog validated, {self.jobs_taken}/{self.jobs_started} job(s) taken by Deadline"
                + (f", {self.jobs_started - self.jobs_finished} still being sent"
                   if self.jobs_started > self.jobs_finished else ""))


def _write_name(values) -> str:
    """The Write a SubmitJob() call is for: its Node argument (not the Root)."""
    for value in values:
        try:
            if callable(getattr(value, "Class", None)) and value.Class() != "Root" and hasattr(value, "fullName"):
                return value.fullName()
        except Exception:
            continue
    return ""


def _short_answer(answer) -> str:
    lines = [line.strip() for line in str(answer or "no answer").splitlines() if line.strip()]
    errors = [line for line in lines if "error" in line.lower()]
    return (errors or lines or ["no answer"])[0][:200]
