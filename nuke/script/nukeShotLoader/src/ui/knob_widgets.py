"""Widgets of the Writes' Prism tab (PyCustom_Knob, built when the panel
opens; see precomp.spec.OUTPUT_DISPLAY_COMMAND)."""

from ..scene.render_ops import output_path
from .qt import QtCore, QtWidgets

_REFRESH_MS = 500


class OutputPath(QtWidgets.QLabel):
    """The Write's output path as it evaluates now, read-only and
    selectable. Prism rewrites it on its own (refresh, render, version up):
    re-read while the panel shows it."""

    def __init__(self, node):
        super().__init__()
        self._node = node
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.setWordWrap(True)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        # Only the height of its lines: the panel would give a custom knob all the room left.
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.updateValue)
        self._timer.start(_REFRESH_MS)
        self.updateValue()

    def makeUI(self):
        return self

    def updateValue(self):
        try:
            text = output_path(self._node)
        except Exception:   # the node was deleted with its panel still around
            self._timer.stop()
            return
        if text != self.text():
            self.setText(text)
            self._fit_height()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_height()

    def _fit_height(self):
        """Exactly the height of the wrapped lines (a path wraps at its slashes)."""
        height = self.heightForWidth(max(self.width(), 1))
        if height > 0 and height != self.height():
            self.setFixedHeight(height)
