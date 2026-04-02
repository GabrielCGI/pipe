"""
ui/output_panel.py — Output path, FPS, timeline name and format selector.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from config import DEFAULT_FPS


class OutputPanel(QGroupBox):
    """Controls for the OTIO export output."""

    output_changed = Signal(str)  # emitted when output path changes

    def __init__(self, parent=None) -> None:
        super().__init__("Output", parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_output_path(self) -> Path:
        return Path(self._path_edit.text().strip())

    def get_fps(self) -> float:
        return self._fps_spin.value()

    def get_timeline_name(self) -> str:
        return self._name_edit.text().strip() or "Review"

    def set_fps(self, fps: float) -> None:
        self._fps_spin.setValue(fps)

    def set_output_path(self, path: str) -> None:
        self._path_edit.setText(path)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        form = QFormLayout(self)

        # Timeline name
        self._name_edit = QLineEdit("Review")
        form.addRow("Timeline name:", self._name_edit)

        # FPS
        self._fps_spin = QDoubleSpinBox()
        self._fps_spin.setRange(1.0, 240.0)
        self._fps_spin.setDecimals(3)
        self._fps_spin.setValue(DEFAULT_FPS)
        self._fps_spin.setSingleStep(1.0)
        form.addRow("FPS:", self._fps_spin)

        # Output path
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Select output .otio file…")
        self._path_edit.textChanged.connect(self.output_changed)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse_btn)
        form.addRow("Output file:", path_row)

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save OTIO Timeline",
            "",
            "OpenTimelineIO (*.otio);;All files (*.*)",
        )
        if path:
            if not path.endswith(".otio"):
                path += ".otio"
            self._path_edit.setText(path)
