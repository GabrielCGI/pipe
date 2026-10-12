"""Sanity check dialog: runs the rules one by one before a submission.

A rule without issue passes and the next one starts. A rule with issues
stops the run and lists the nodes: Fix applies the rule's fix, checks the
rule again and goes on; Close cancels the submission.
"""

import traceback

from ..scene.utils import undo_group
from .qt import QtCore, QtWidgets
from .styles import STYLESHEET

PASSED, FIXED, CANCELLED = "passed", "fixed", "cancelled"
_STEPS = 1000            # progress bar resolution per rule
_CLOSE_DELAY_MS = 300    # the final "all passed" stays readable
_STATE_TEXT = {"pending": "•", "running": "…", "passed": "✓", "failed": "✕"}


class _Closed(Exception):
    """The dialog was closed while a rule was being checked."""


def check_rule(rule, context, progress=None):
    """Issues of `rule`; a rule that can't run reports none (a broken rule
    must not block every render)."""
    try:
        return rule.check(context, progress)
    except _Closed:
        raise
    except Exception as e:
        print(f"[sanity] rule '{rule.title}' could not run: {e}")
        traceback.print_exc()
        return []


class SanityCheckDialog(QtWidgets.QDialog):
    """`outcome` after the run: PASSED (nothing to fix), FIXED (at least one
    fix changed the script: what was computed before is stale) or CANCELLED."""

    def __init__(self, rules, context, source="", parent=None):
        super().__init__(parent)
        self.rules, self.context = list(rules), context
        self.outcome = CANCELLED
        self._index, self._issues, self._fixed_any, self._closed = 0, [], False, False
        self.setWindowTitle("Sanity Check")
        self.setModal(True)
        self.setMinimumSize(760, 520)
        self.setStyleSheet(STYLESHEET)
        self._build_ui(source)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self, source):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        header = QtWidgets.QFrame()
        header.setObjectName("projectTitle")
        header_layout = QtWidgets.QVBoxLayout(header)
        header_layout.setContentsMargins(18, 12, 18, 12)
        title = QtWidgets.QLabel(
            '<span style="font-size:10px; color:#8a8a8a; letter-spacing:2.5px; font-weight:600;">'
            'SANITY CHECK</span><br>'
            f'<span style="font-size:18px; color:#f0f0f0; font-weight:700;">{source or "Render"}</span>')
        title.setTextFormat(QtCore.Qt.RichText)
        header_layout.addWidget(title)
        layout.addWidget(header)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setObjectName("sanityBar")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setRange(0, max(1, len(self.rules)) * _STEPS)
        layout.addWidget(self.progress)
        self.status = QtWidgets.QLabel("")
        self.status.setObjectName("statusText")
        layout.addWidget(self.status)

        rules_box = QtWidgets.QGroupBox("RULES")
        rules_layout = QtWidgets.QVBoxLayout(rules_box)
        rules_layout.setContentsMargins(10, 6, 10, 8)
        rules_layout.setSpacing(4)
        self.rule_rows = []
        for _ in self.rules:
            row = QtWidgets.QLabel()
            row.setObjectName("sanityRule")
            rules_layout.addWidget(row)
            self.rule_rows.append(row)
            self._set_state(len(self.rule_rows) - 1, "pending")
        layout.addWidget(rules_box)

        issues_box = QtWidgets.QGroupBox("ISSUES")
        issues_layout = QtWidgets.QVBoxLayout(issues_box)
        issues_layout.setContentsMargins(10, 6, 10, 8)
        self.help = QtWidgets.QLabel("")
        self.help.setWordWrap(True)
        self.help.setObjectName("sanityHelp")
        issues_layout.addWidget(self.help)
        self.issues_view = QtWidgets.QPlainTextEdit()
        self.issues_view.setReadOnly(True)
        self.issues_view.setObjectName("logView")
        issues_layout.addWidget(self.issues_view)
        layout.addWidget(issues_box, stretch=1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        self.fix_btn = QtWidgets.QPushButton("Fix")
        self.fix_btn.setObjectName("primaryAction")
        self.fix_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.fix_btn.clicked.connect(self._on_fix)
        self.fix_btn.setVisible(False)
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.close_btn.setToolTip("Close the sanity check: nothing is submitted.")
        self.close_btn.clicked.connect(self.reject)
        buttons.addWidget(self.fix_btn)
        buttons.addWidget(self.close_btn)
        layout.addLayout(buttons)

    def _set_state(self, index, state, note=""):
        row = self.rule_rows[index]
        row.setText(f"{_STATE_TEXT[state]}   {self.rules[index].title}" + (f"   —   {note}" if note else ""))
        row.setProperty("state", state)
        row.style().unpolish(row)  # re-evaluate the [state=...] rules
        row.style().polish(row)

    def _set_progress(self, fraction=0.0, text=""):
        self.progress.setValue(int((self._index + fraction) * _STEPS))
        self.status.setText(text)
        QtWidgets.QApplication.processEvents()

    def _rule_progress(self, done, total, text):
        """Progress of the running rule, from its check() or fix()."""
        self._set_progress(done / float(max(1, total)), text)

    def _check_progress(self, done, total, text):
        """Same during a check, which Close interrupts between two steps."""
        self._rule_progress(done, total, text)
        if self._closed:
            raise _Closed()

    def done(self, result):
        self._closed = True
        super().done(result)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def start(self):
        self._index = 0
        QtCore.QTimer.singleShot(0, self._check_current)

    def _check_current(self):
        if self._closed:
            return
        if self._index >= len(self.rules):
            return self._finish()
        rule = self.rules[self._index]
        self._set_state(self._index, "running")
        self._set_progress(0.0, f"Checking: {rule.title}")
        try:
            self._issues = check_rule(rule, self.context, self._check_progress)
        except _Closed:
            return
        if self._issues:
            return self._show_issues(rule)
        self._set_state(self._index, "passed")
        self._index += 1
        self._set_progress(0.0, "")
        QtCore.QTimer.singleShot(0, self._check_current)

    def _show_issues(self, rule, failures=()):
        count = len(self._issues)
        self._set_state(self._index, "failed", f"{count} node(s)")
        self.status.setText(f"{rule.title}: {count} node(s) to fix")
        self.help.setText(rule.fix_help)
        lines = [f"{issue.node.fullName()}\n      {issue.detail}" for issue in self._issues]
        if failures:
            lines = ["Fix failed:"] + [f"  {line}" for line in failures] + [""] + lines
        self.issues_view.setPlainText("\n".join(lines))
        self.fix_btn.setText(rule.fix_label)
        self.fix_btn.setVisible(True)
        self.fix_btn.setEnabled(True)
        self.close_btn.setEnabled(True)

    def _on_fix(self):
        rule = self.rules[self._index]
        self.fix_btn.setEnabled(False)
        self.close_btn.setEnabled(False)
        self._set_state(self._index, "running", "fixing")
        try:
            with undo_group(f"Sanity check: {rule.title}"):
                failures = rule.fix(self._issues, self.context, self._rule_progress)
        except Exception as e:
            traceback.print_exc()
            failures = [f"{type(e).__name__}: {e}"]
        self._fixed_any = True
        self.context.refresh()
        self._issues = check_rule(rule, self.context, self._rule_progress)
        if self._issues:  # not everything could be fixed: Fix again or Close
            return self._show_issues(rule, failures)
        self.fix_btn.setVisible(False)
        self.close_btn.setEnabled(True)
        self.help.setText("")
        self.issues_view.clear()
        self._set_state(self._index, "passed", "fixed")
        self._index += 1
        self._set_progress(0.0, "")
        QtCore.QTimer.singleShot(0, self._check_current)

    def _finish(self):
        self.outcome = FIXED if self._fixed_any else PASSED
        self.progress.setValue(self.progress.maximum())
        self.status.setText("All checks passed.")
        QtCore.QTimer.singleShot(_CLOSE_DELAY_MS, self.accept)


def run(rules, context, source="", parent=None, quiet=False) -> str:
    """Run the sanity check modally. Returns PASSED, FIXED or CANCELLED.
    `quiet`: the dialog only shows up when a rule has issues (the check of
    a script the dialog just fixed)."""
    if quiet and not any(check_rule(rule, context) for rule in rules):
        return PASSED
    dialog = SanityCheckDialog(rules, context, source, parent)
    dialog.start()
    dialog.exec_()
    return dialog.outcome
