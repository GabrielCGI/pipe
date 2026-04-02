"""
ui/version_panel.py — Version selection mode (latest auto / manual per shot).
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QRadioButton,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.scanner import ShotEntry, VersionEntry


class VersionPanel(QGroupBox):
    """
    Two modes:
    - "Latest" (default): auto-picks the highest vNNN for each shot/task.
    - "Manual": shows a table with per-shot QComboBoxes to override the version.
    """

    MODE_LATEST = "latest"
    MODE_MANUAL = "manual"

    def __init__(self, parent=None) -> None:
        super().__init__("Version", parent)
        self._shot_overrides: Dict[str, Dict[str, str]] = {}  # full_name -> task -> version_str
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mode(self) -> str:
        return self.MODE_LATEST if self._radio_latest.isChecked() else self.MODE_MANUAL

    def get_version_for(self, shot: ShotEntry, task: str) -> Optional[str]:
        """
        Return the version_str to use for this shot/task.
        In "latest" mode always returns None (caller picks highest automatically).
        In "manual" mode returns the user-selected version_str or None (→ latest).
        """
        if self.mode() == self.MODE_LATEST:
            return None
        overrides = self._shot_overrides.get(shot.full_name, {})
        return overrides.get(task)

    def populate(self, shots: List[ShotEntry], tasks: List[str]) -> None:
        """
        Rebuild the manual-override table for the given shots and tasks.
        Only relevant when mode is "manual".
        """
        self._shot_overrides.clear()
        self._manual_tree.clear()

        for shot in shots:
            item = QTreeWidgetItem()
            item.setText(0, shot.display_name)
            item.setData(0, Qt.UserRole, shot)

            for col_idx, task in enumerate(tasks, start=1):
                versions = shot.versions_by_task.get(task, [])
                if not versions:
                    item.setText(col_idx, "—")
                    continue

                combo = QComboBox()
                combo.addItem("Latest (auto)", None)
                for v in reversed(versions):  # newest first
                    combo.addItem(v.version_str, v.version_str)
                combo.setProperty("shot_key", shot.full_name)
                combo.setProperty("task", task)
                combo.currentIndexChanged.connect(self._on_combo_changed)
                self._manual_tree.setItemWidget(item, col_idx, combo)

            self._manual_tree.addTopLevelItem(item)

        # Adjust columns
        self._manual_tree.setColumnCount(1 + len(tasks))
        headers = ["Shot"] + tasks
        self._manual_tree.setHeaderLabels(headers)
        for i in range(self._manual_tree.columnCount()):
            self._manual_tree.resizeColumnToContents(i)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Mode radio buttons
        mode_row = QHBoxLayout()
        self._radio_latest = QRadioButton("Latest version (auto)")
        self._radio_manual = QRadioButton("Manual per shot")
        self._radio_latest.setChecked(True)
        self._radio_latest.toggled.connect(self._on_mode_toggled)
        mode_row.addWidget(self._radio_latest)
        mode_row.addWidget(self._radio_manual)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Manual override table (hidden by default)
        self._manual_tree = QTreeWidget()
        self._manual_tree.setColumnCount(1)
        self._manual_tree.setHeaderLabels(["Shot"])
        self._manual_tree.setVisible(False)
        layout.addWidget(self._manual_tree)

        self._hint_label = QLabel(
            "Automatically selects the highest version number available for each shot."
        )
        self._hint_label.setStyleSheet("color: #888; font-size: 11px;")
        self._hint_label.setWordWrap(True)
        layout.addWidget(self._hint_label)

    def _on_mode_toggled(self, checked: bool) -> None:
        is_manual = not checked  # radio_latest toggled
        self._manual_tree.setVisible(is_manual)
        if is_manual:
            self._hint_label.setText(
                "Select a specific version per shot. \"Latest (auto)\" uses the highest available."
            )
        else:
            self._hint_label.setText(
                "Automatically selects the highest version number available for each shot."
            )

    def _on_combo_changed(self) -> None:
        combo: QComboBox = self.sender()
        shot_key = combo.property("shot_key")
        task = combo.property("task")
        version_str = combo.currentData()
        if shot_key and task:
            if shot_key not in self._shot_overrides:
                self._shot_overrides[shot_key] = {}
            if version_str is None:
                self._shot_overrides[shot_key].pop(task, None)
            else:
                self._shot_overrides[shot_key][task] = version_str
