"""
ui/project_panel.py — Project root selector with recent-project support.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from core.project import PrismProject, ProjectLoader
from core.exceptions import InvalidProjectError


class ProjectPanel(QGroupBox):
    """
    Lets the user select a Prism project root.
    Emits *project_loaded* with the parsed PrismProject when a valid project is set.
    Emits *project_error* with an error string if loading fails.
    """

    project_loaded = Signal(object)   # PrismProject
    project_error = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__("Project", parent)
        self._current_project: Optional[PrismProject] = None
        self._build_ui()
        self._populate_recents()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def current_project(self) -> Optional[PrismProject]:
        return self._current_project

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Recent projects combo
        recents_row = QHBoxLayout()
        recents_row.addWidget(QLabel("Recent:"))
        self._recents_combo = QComboBox()
        self._recents_combo.setMinimumWidth(200)
        self._recents_combo.currentIndexChanged.connect(self._on_recent_selected)
        recents_row.addWidget(self._recents_combo, 1)
        layout.addLayout(recents_row)

        # Manual path entry
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("Project root folder…")
        self._path_edit.returnPressed.connect(self._load_from_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self._path_edit, 1)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self._status_label)

    def _populate_recents(self) -> None:
        self._recents_combo.blockSignals(True)
        self._recents_combo.clear()
        self._recents_combo.addItem("-- Select recent project --", None)
        try:
            recents = ProjectLoader.discover_from_prism_config()
            for name, path in recents:
                self._recents_combo.addItem(name, str(path))
        except Exception:
            pass
        self._recents_combo.blockSignals(False)

    def _on_recent_selected(self, index: int) -> None:
        path_str = self._recents_combo.itemData(index)
        if path_str:
            self._path_edit.setText(path_str)
            self._load_project(Path(path_str))

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Prism Project Root")
        if folder:
            self._path_edit.setText(folder)
            self._load_project(Path(folder))

    def _load_from_edit(self) -> None:
        text = self._path_edit.text().strip()
        if text:
            self._load_project(Path(text))

    def _load_project(self, path: Path) -> None:
        try:
            project = ProjectLoader.from_path(path)
            self._current_project = project
            self._status_label.setText(
                f"Loaded: {project.name}  |  FPS: {project.fps}"
            )
            self._status_label.setStyleSheet("color: #6fcf97; font-size: 11px;")
            self.project_loaded.emit(project)
        except (InvalidProjectError, Exception) as exc:
            self._current_project = None
            self._status_label.setText(f"Error: {exc}")
            self._status_label.setStyleSheet("color: #eb5757; font-size: 11px;")
            self.project_error.emit(str(exc))
