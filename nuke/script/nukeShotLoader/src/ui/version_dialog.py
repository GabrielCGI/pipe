""""Render as previous version..." of a PrecompWrite / Compo Write: which
version, which frames. The render itself: precomp.engine.render_into_version()
/ scene.render_ops.render_compo_into_version()."""

import os
import re

from ..precomp.engine import frame_spans
from . import widgets as w
from .qt import QtWidgets
from .styles import STYLESHEET

_TOKEN_RE = re.compile(r"^(\d+)(?:-(\d+))?$")


def parse_frames(text: str):
    """'1001-1003 1050, 1060' -> [1001, 1002, 1003, 1050, 1060]. ValueError
    on anything else."""
    frames = set()
    for token in re.split(r"[\s,]+", text.strip()):
        if not token:
            continue
        m = _TOKEN_RE.match(token)
        if not m or int(m.group(2) or m.group(1)) < int(m.group(1)):
            raise ValueError(f"'{token}' is not a frame or a range (1001-1010)")
        frames.update(range(int(m.group(1)), int(m.group(2) or m.group(1)) + 1))
    if not frames:
        raise ValueError("Enter the frames to render (e.g. 1012 1040-1045).")
    return sorted(frames)


def format_frames(frames) -> str:
    """[1001, 1002, 1003, 1050] -> '1001-1003 1050'."""
    return " ".join(str(a) if a == b else f"{a}-{b}" for a, b in frame_spans(frames))


def version_name(rendered) -> str:
    """The version folder's own name ('v038', or 'v0038' with a 4-digit padding)."""
    return os.path.basename(os.path.dirname(rendered.path)) or f"v{rendered.version:03d}"


class PreviousVersionDialog(QtWidgets.QDialog):
    """`versions`: engine.rendered_versions() / render_ops.compo_versions(),
    newest first. Only those rendered from the current state of the script
    (`current`) can be picked; `state_checked` False (a compo: no manifest)
    leaves that out of the explanation. choose() returns (RenderedVersion,
    frames), None when cancelled."""

    def __init__(self, name, versions, parent=None, state_checked=True):
        super().__init__(parent)
        self.versions = list(versions)
        self.choice = None
        self.setWindowTitle(f"Render {name} as previous version")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setStyleSheet(STYLESHEET)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        intro = QtWidgets.QLabel(
            f"Renders frames of {name} into one of its versions, in this Nuke session (never on the farm): "
            "to replace frames broken on the farm."
            + ("\nOnly a version rendered from the current state of the script can take new frames."
               if state_checked else ""))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QtWidgets.QFormLayout()
        self.version_box = QtWidgets.QComboBox()
        for rendered in self.versions:
            self.version_box.addItem(self._describe(rendered))
            if not rendered.current:
                self.version_box.model().item(self.version_box.count() - 1).setEnabled(False)
        self.frames_edit = QtWidgets.QLineEdit()
        self.frames_edit.setPlaceholderText("e.g. 1012 1040-1045")
        form.addRow("Version", self.version_box)
        form.addRow("Frames", self.frames_edit)
        layout.addLayout(form)
        self.note = QtWidgets.QLabel("")
        self.note.setObjectName("statusText")
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch()
        self.render_btn = w.button("Render locally", self._accept, "primaryAction")
        buttons.addWidget(self.render_btn)
        buttons.addWidget(w.button("Cancel", self.reject))
        layout.addLayout(buttons)

        self.version_box.currentIndexChanged.connect(self._version_changed)
        self.version_box.setCurrentIndex(next(i for i, v in enumerate(self.versions) if v.current))
        self._version_changed(self.version_box.currentIndex())

    @staticmethod
    def _describe(rendered) -> str:
        head = f"{version_name(rendered)}   {rendered.first}-{rendered.last}"
        if not rendered.current:
            return f"{head}   rendered from another state of the script"
        return f"{head}   " + (f"{len(rendered.missing)} frame(s) missing" if rendered.missing else "complete")

    def _version_changed(self, index):
        rendered = self.versions[index]
        if rendered.missing:
            self.frames_edit.setText(format_frames(rendered.missing))
            self.note.setText("Missing frames filled in; add the broken ones.")
        else:
            self.frames_edit.setText("")
            self.note.setText("Every frame is on disk: enter the broken ones.")

    def _accept(self):
        rendered = self.versions[self.version_box.currentIndex()]
        try:
            frames = parse_frames(self.frames_edit.text())
        except ValueError as e:
            self.note.setText(str(e))
            return
        outside = [f for f in frames if not rendered.first <= f <= rendered.last]
        if outside:
            self.note.setText(f"{version_name(rendered)} covers {rendered.first}-{rendered.last}: "
                              f"{format_frames(outside)} outside.")
            return
        self.choice = (rendered, frames)
        self.accept()

    def choose(self):
        self.exec_()
        return self.choice
