"""
ui/step_panel.py — Pipeline step (task) selector.

Populated dynamically from PrismProject.departments_shot. Shown as a collapsible
tree: each pipeline step (department) is a tri-state parent, each task a checkable
child. A trailing "Autres" leaf catches on-disk folders matching no known task.
"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from config import OTHER_STEP
from core.project import PrismProject


class StepPanel(QGroupBox):
    """
    Lets the user select one or more pipeline tasks to include in the OTIO timeline.
    Emits *selection_changed* (list[str] of canonical task names) on every change.
    """

    selection_changed = Signal(list)  # list[str] — canonical task names

    def __init__(self, parent=None) -> None:
        super().__init__("Pipeline Steps", parent)
        self._updating = False
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, project: PrismProject) -> None:
        """Rebuild the step/task tree from the project's departments."""
        self._updating = True
        self._tree.clear()

        for dept in project.departments_shot:
            tasks = list(dept.default_tasks) or [dept.name]
            parent = QTreeWidgetItem(self._tree, [dept.name])
            parent.setFlags(
                parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
            )
            tooltip = f"Department: {dept.name}  |  Abbreviation: {dept.abbreviation}"
            if dept.color:
                tooltip += f"  |  Color: {dept.color}"
            parent.setToolTip(0, tooltip)
            for task in tasks:
                child = QTreeWidgetItem(parent, [task])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setCheckState(0, Qt.Unchecked)
            parent.setExpanded(False)

        # Catch-all bucket for unrecognised folders (allowAdditionalTasks).
        other = QTreeWidgetItem(self._tree, [OTHER_STEP])
        other.setFlags(other.flags() | Qt.ItemIsUserCheckable)
        other.setCheckState(0, Qt.Unchecked)
        other.setToolTip(0, "Folders matching no known task")

        self._updating = False
        self._preselect_default()

    def get_selected_tasks(self) -> List[str]:
        """Return canonical task names of all checked leaf items."""
        tasks: List[str] = []
        for leaf in self._iter_leaves():
            if leaf.checkState(0) == Qt.Checked:
                tasks.append(leaf.text(0))
        return tasks

    def set_selected_tasks(self, tasks: List[str]) -> None:
        wanted = set(tasks)
        self._updating = True
        for leaf in self._iter_leaves():
            leaf.setCheckState(
                0, Qt.Checked if leaf.text(0) in wanted else Qt.Unchecked
            )
        self._updating = False
        self.selection_changed.emit(self.get_selected_tasks())

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(1)
        self._tree.header().setSectionResizeMode(QHeaderView.Stretch)
        self._tree.itemChanged.connect(self._on_item_changed)
        outer.addWidget(self._tree)

        # Helper: select all / none / expand / collapse
        btn_row = QHBoxLayout()
        all_btn = QPushButton("All")
        none_btn = QPushButton("None")
        expand_btn = QPushButton("Expand")
        collapse_btn = QPushButton("Collapse")
        all_btn.setFixedWidth(50)
        none_btn.setFixedWidth(50)
        all_btn.clicked.connect(self._select_all)
        none_btn.clicked.connect(self._select_none)
        expand_btn.clicked.connect(lambda: self._tree.expandAll())
        collapse_btn.clicked.connect(lambda: self._tree.collapseAll())
        btn_row.addWidget(all_btn)
        btn_row.addWidget(none_btn)
        btn_row.addWidget(expand_btn)
        btn_row.addWidget(collapse_btn)
        btn_row.addStretch()
        outer.addLayout(btn_row)

    def _iter_leaves(self):
        """Yield every selectable leaf item (tasks + the 'Autres' bucket)."""
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            top = root.child(i)
            if top.childCount() == 0:
                yield top
            else:
                for j in range(top.childCount()):
                    yield top.child(j)

    def _preselect_default(self) -> None:
        """Check 'Compo' by default (else the first task) and reveal it."""
        leaves = list(self._iter_leaves())
        if not leaves:
            return
        target = next(
            (lf for lf in leaves if lf.text(0).lower() == "compo"), leaves[0]
        )
        self._updating = True
        target.setCheckState(0, Qt.Checked)
        self._updating = False
        if target.parent():
            target.parent().setExpanded(True)
        self.selection_changed.emit(self.get_selected_tasks())

    def _on_item_changed(self, _item: QTreeWidgetItem, _column: int) -> None:
        if self._updating:
            return
        self.selection_changed.emit(self.get_selected_tasks())

    def _set_all(self, state: Qt.CheckState) -> None:
        self._updating = True
        for leaf in self._iter_leaves():
            leaf.setCheckState(0, state)
        self._updating = False
        self.selection_changed.emit(self.get_selected_tasks())

    def _select_all(self) -> None:
        self._set_all(Qt.Checked)

    def _select_none(self) -> None:
        self._set_all(Qt.Unchecked)
