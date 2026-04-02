"""
ui/shot_panel.py — Shot list with multi-selection, filter, and per-shot status.

Selection model:
  - Shots are INCLUDED or EXCLUDED (stored as item background colour).
  - Click a row to select it (Qt selection highlight).
  - Space / Enter  : include or exclude all currently highlighted rows.
  - Ctrl+A         : highlight all visible rows.
  - "All" button   : include all visible shots.
  - "None" button  : exclude all visible shots.
  - Included rows  : bright text (#dcdcdc).
  - Excluded rows  : dim text (#555), italic.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from core.scanner import ShotEntry


# Column indices
COL_SHOT = 0
COL_SEQUENCE = 1
COL_FRAMES = 2
COL_STATUS = 3

_COLOR_INCLUDED = QColor("#dcdcdc")
_COLOR_EXCLUDED = QColor("#555555")
_COLOR_STATUS_OK = QColor("#6fcf97")
_COLOR_STATUS_WARN = QColor("#f2c94c")


class ShotPanel(QGroupBox):
    """
    Displays shots from the scanned project.

    Rows can be individually included/excluded for the OTIO export.
    Multi-selection (Shift/Ctrl + click) + Space to bulk-toggle.
    """

    selection_changed = Signal(list)  # list[ShotEntry] — included shots

    def __init__(self, parent=None) -> None:
        super().__init__("Shots", parent)
        self._shots: List[ShotEntry] = []
        self._items: Dict[str, QTreeWidgetItem] = {}  # full_name -> item
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, shots: List[ShotEntry]) -> None:
        """Fill the tree with *shots*. All start as excluded."""
        self._shots = shots
        self._items.clear()
        self._tree.clear()

        for shot in shots:
            item = QTreeWidgetItem()
            item.setText(COL_SHOT, shot.shot)
            item.setText(COL_SEQUENCE, shot.sequence)
            frame_in, frame_out = shot.frame_range
            item.setText(COL_FRAMES, f"{frame_in} – {frame_out}")
            item.setText(COL_STATUS, "—")
            item.setData(COL_SHOT, Qt.UserRole, shot)
            item.setData(COL_SHOT, Qt.UserRole + 1, False)  # included = False
            self._items[shot.full_name] = item
            self._tree.addTopLevelItem(item)
            self._apply_row_style(item, included=False)

        self._tree.sortByColumn(COL_SHOT, Qt.AscendingOrder)
        self._apply_filter(self._filter_edit.text())
        self._update_count()

    def update_shot_status(self, shot: ShotEntry, status: str, ok: bool = True) -> None:
        """Update the status column for a specific shot after scanning."""
        item = self._items.get(shot.full_name)
        if item is None:
            return
        item.setText(COL_STATUS, status)
        included = item.data(COL_SHOT, Qt.UserRole + 1)
        if included:
            color = _COLOR_STATUS_OK if ok else _COLOR_STATUS_WARN
        else:
            color = _COLOR_EXCLUDED
        item.setForeground(COL_STATUS, QBrush(color))

    def update_shot_frames(self, shot: ShotEntry, frame_in: int, frame_out: int) -> None:
        """Update the Frames column with actual media frame range after scanning."""
        item = self._items.get(shot.full_name)
        if item is None:
            return
        item.setText(COL_FRAMES, f"{frame_in} – {frame_out}")

    def get_selected_shots(self) -> List[ShotEntry]:
        """Return ShotEntry objects that are included and visible."""
        selected = []
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.isHidden():
                continue
            if item.data(COL_SHOT, Qt.UserRole + 1):
                shot = item.data(COL_SHOT, Qt.UserRole)
                if shot:
                    selected.append(shot)
        return selected

    def shot_count(self) -> int:
        return len(self._shots)

    # ------------------------------------------------------------------
    # Private — UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Filter:"))
        self._filter_edit = QLineEdit()
        self._filter_edit.setPlaceholderText("shot name… (# = any digit)")
        self._filter_edit.textChanged.connect(self._apply_filter)
        filter_row.addWidget(self._filter_edit, 1)

        all_btn = QPushButton("All")
        none_btn = QPushButton("None")
        all_btn.setFixedWidth(50)
        none_btn.setFixedWidth(50)
        all_btn.setToolTip("Include all visible shots")
        none_btn.setToolTip("Exclude all visible shots")
        all_btn.clicked.connect(self._include_all)
        none_btn.clicked.connect(self._exclude_all)
        filter_row.addWidget(all_btn)
        filter_row.addWidget(none_btn)
        layout.addLayout(filter_row)

        # Tree — multi-selection, no checkboxes
        self._tree = QTreeWidget()
        self._tree.setColumnCount(4)
        self._tree.setHeaderLabels(["Shot", "Sequence", "Frames", "Status"])
        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tree.header().setSectionResizeMode(COL_SHOT, QHeaderView.Interactive)
        self._tree.setColumnWidth(COL_SHOT, 130)
        self._tree.setColumnWidth(COL_SEQUENCE, 150)
        self._tree.setColumnWidth(COL_FRAMES, 120)
        self._tree.setColumnWidth(COL_STATUS, 150)
        self._tree.setSortingEnabled(True)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.keyPressEvent = self._on_key_press
        layout.addWidget(self._tree)

        # Hint + count
        hint = QLabel("Space / Enter: include or exclude selected shots  ·  Double-click to toggle  ·  Shift/Ctrl+click to multi-select")
        hint.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(hint)

        self._count_label = QLabel("0 shots")
        self._count_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self._count_label)

    # ------------------------------------------------------------------
    # Private — interaction
    # ------------------------------------------------------------------

    def _on_double_click(self, item: QTreeWidgetItem, col: int) -> None:
        self._toggle_items([item])

    def _on_key_press(self, event) -> None:
        """Space or Enter = toggle included/excluded on selected rows."""
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            selected = self._tree.selectedItems()
            if selected:
                self._toggle_items(selected)
        else:
            QTreeWidget.keyPressEvent(self._tree, event)

    def _toggle_items(self, items: List[QTreeWidgetItem]) -> None:
        """Toggle include/exclude on a list of items.

        If ANY item in the list is currently excluded, include all.
        Otherwise exclude all (so a mixed selection always moves to included first).
        """
        any_excluded = any(
            not item.data(COL_SHOT, Qt.UserRole + 1) for item in items
        )
        new_state = True if any_excluded else False
        for item in items:
            item.setData(COL_SHOT, Qt.UserRole + 1, new_state)
            self._apply_row_style(item, included=new_state)
        self.selection_changed.emit(self.get_selected_shots())
        self._update_count()

    def _include_all(self) -> None:
        self._set_all_included(True)

    def _exclude_all(self) -> None:
        self._set_all_included(False)

    def _set_all_included(self, state: bool) -> None:
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if not item.isHidden():
                item.setData(COL_SHOT, Qt.UserRole + 1, state)
                self._apply_row_style(item, included=state)
        self.selection_changed.emit(self.get_selected_shots())
        self._update_count()

    # ------------------------------------------------------------------
    # Private — visual style
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_row_style(item: QTreeWidgetItem, included: bool) -> None:
        """Apply bright/dim style to all text columns based on include state."""
        color = _COLOR_INCLUDED if included else _COLOR_EXCLUDED
        brush = QBrush(color)
        font = item.font(COL_SHOT)
        font.setItalic(not included)
        for col in range(item.columnCount()):
            item.setForeground(col, brush)
            item.setFont(col, font)

    # ------------------------------------------------------------------
    # Private — filter
    # ------------------------------------------------------------------

    def _apply_filter(self, text: str) -> None:
        pattern = self._build_filter_regex(text)
        changed = False
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if pattern is None:
                visible = True
            else:
                visible = (
                    pattern.search(item.text(COL_SHOT)) is not None
                    or pattern.search(item.text(COL_SEQUENCE)) is not None
                )
            item.setHidden(not visible)
            if not visible and item.data(COL_SHOT, Qt.UserRole + 1):
                item.setData(COL_SHOT, Qt.UserRole + 1, False)
                self._apply_row_style(item, included=False)
                changed = True
        self._update_count()
        if changed:
            self.selection_changed.emit(self.get_selected_shots())

    @staticmethod
    def _build_filter_regex(text: str):
        """
        Build a regex from the filter text.
        '#' matches any single digit.
        Example: 'SH0##' matches 'SH010', 'SH020', 'SH099'...
        """
        if not text:
            return None
        escaped = re.escape(text)
        escaped = escaped.replace(r"\#", r"\d")
        return re.compile(escaped, re.IGNORECASE)

    # ------------------------------------------------------------------
    # Private — count
    # ------------------------------------------------------------------

    def _update_count(self) -> None:
        visible = 0
        included = 0
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if not item.isHidden():
                visible += 1
                if item.data(COL_SHOT, Qt.UserRole + 1):
                    included += 1
        total = self._tree.topLevelItemCount()
        self._count_label.setText(f"{included} included / {visible} visible / {total} total")
