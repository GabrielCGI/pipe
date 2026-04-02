"""
ui/log_panel.py — Colour-coded log / status panel.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class LogPanel(QGroupBox):
    """
    A read-only, colour-coded log area.

    Usage:
        log.info("Scanning shots...")
        log.success("Timeline exported: /path/review.otio")
        log.warning("Shot sq010/sh030: no media found")
        log.error("Failed to load project")
        log.clear()
    """

    def __init__(self, parent=None) -> None:
        super().__init__("Log", parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def info(self, message: str) -> None:
        self._append(message, "#cccccc")

    def success(self, message: str) -> None:
        self._append(f"[OK] {message}", "#6fcf97")

    def warning(self, message: str) -> None:
        self._append(f"[WARN] {message}", "#f2c94c")

    def error(self, message: str) -> None:
        self._append(f"[ERR] {message}", "#eb5757")

    def clear(self) -> None:
        self._text.clear()

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumBlockCount(2000)
        self._text.setStyleSheet(
            "QPlainTextEdit { background: #1e1e1e; color: #cccccc; "
            "font-family: monospace; font-size: 11px; }"
        )

        copy_btn = QPushButton("Copy")
        copy_btn.setFixedWidth(60)
        copy_btn.clicked.connect(self._copy_to_clipboard)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(clear_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._text)
        layout.addLayout(btn_layout)

    def _append(self, message: str, color_hex: str) -> None:
        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color_hex))
        cursor.insertText(message + "\n", fmt)

        self._text.setTextCursor(cursor)
        self._text.ensureCursorVisible()

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self._text.toPlainText())
