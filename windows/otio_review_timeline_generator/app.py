"""
app.py — Entry point for the OTIO Review Timeline Generator.

Usage:
    python app.py
"""

import sys
import os
import traceback

# Ensure the project root is on the Python path so all imports work
# regardless of the working directory from which app.py is launched.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config import APP_NAME
from ui.main_window import MainWindow


def main() -> None:
    try:
        _run()
    except Exception:
        log_path = os.path.join(
            os.environ.get("TEMP", os.path.expanduser("~")),
            "otio_review_error.log",
        )
        with open(log_path, "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()
        input(f"\nCrash log written to: {log_path}\nPress Enter to close...")
        sys.exit(1)


def _run() -> None:
    # Enable high-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Dark palette for a VFX-friendly look
    _apply_dark_palette(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


def _apply_dark_palette(app: QApplication) -> None:
    from PySide6.QtGui import QPalette, QColor

    palette = QPalette()
    dark = QColor(45, 45, 45)
    darker = QColor(30, 30, 30)
    mid = QColor(60, 60, 60)
    text = QColor(220, 220, 220)
    highlight = QColor(47, 128, 237)

    palette.setColor(QPalette.Window, dark)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, darker)
    palette.setColor(QPalette.AlternateBase, dark)
    palette.setColor(QPalette.ToolTipBase, mid)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, mid)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))

    app.setPalette(palette)


if __name__ == "__main__":
    main()
