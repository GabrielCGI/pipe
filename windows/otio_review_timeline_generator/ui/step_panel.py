"""
ui/step_panel.py — Pipeline step (task) selector.

Populated dynamically from PrismProject.departments_shot.
Supports single-step mode (radio buttons) or multi-step (checkboxes).
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.project import PrismProject, Department


class StepPanel(QGroupBox):
    """
    Lets the user select one or more pipeline tasks to include in the OTIO timeline.
    Emits *selection_changed* whenever the selection changes.
    """

    selection_changed = Signal(list)  # list[str] — canonical task names

    def __init__(self, parent=None) -> None:
        super().__init__("Pipeline Steps", parent)
        self._checkboxes: List[QCheckBox] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, project: PrismProject) -> None:
        """Rebuild the task list from the project's departments."""
        self._clear_checkboxes()
        for dept in project.departments_shot:
            for task in dept.default_tasks:
                if "storyboard" in task.lower():
                    continue
                self._add_task(task, dept)
        # Pre-select Compositing/Compo if available, otherwise the first task
        compo_cb = next(
            (cb for cb in self._checkboxes if "compo" in cb.text().lower()), None
        )
        if compo_cb:
            compo_cb.setChecked(True)
        elif self._checkboxes:
            self._checkboxes[0].setChecked(True)

    def get_selected_tasks(self) -> List[str]:
        """Return canonical task names that are currently checked."""
        return [cb.text() for cb in self._checkboxes if cb.isChecked()]

    def set_selected_tasks(self, tasks: List[str]) -> None:
        for cb in self._checkboxes:
            cb.setChecked(cb.text() in tasks)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)

        # Scrollable area for the checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setSpacing(2)
        self._container_layout.addStretch()

        scroll.setWidget(self._container)
        outer.addWidget(scroll)

        # Helper: select all / none
        btn_row = QHBoxLayout()
        all_btn = QPushButton("All")
        none_btn = QPushButton("None")
        all_btn.setFixedWidth(50)
        none_btn.setFixedWidth(50)
        all_btn.clicked.connect(self._select_all)
        none_btn.clicked.connect(self._select_none)
        btn_row.addWidget(all_btn)
        btn_row.addWidget(none_btn)
        btn_row.addStretch()
        outer.addLayout(btn_row)

        self._placeholder = QLabel("Load a project to see pipeline steps.")
        self._placeholder.setStyleSheet("color: #888;")
        self._container_layout.insertWidget(0, self._placeholder)

    def _clear_checkboxes(self) -> None:
        for cb in self._checkboxes:
            cb.deleteLater()
        self._checkboxes.clear()
        self._placeholder.hide()

    def _add_task(self, task: str, dept: Department) -> None:
        cb = QCheckBox(task)
        tooltip = f"Department: {dept.name}  |  Abbreviation: {dept.abbreviation}"
        if dept.color:
            tooltip += f"  |  Color: {dept.color}"
        cb.setToolTip(tooltip)
        cb.stateChanged.connect(self._on_state_changed)
        # Insert before the stretch spacer
        self._container_layout.insertWidget(
            self._container_layout.count() - 1, cb
        )
        self._checkboxes.append(cb)

    def _on_state_changed(self) -> None:
        self.selection_changed.emit(self.get_selected_tasks())

    def _select_all(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _select_none(self) -> None:
        for cb in self._checkboxes:
            cb.setChecked(False)
