"""Dialog stylesheet. Widget variants are selected through objectName."""

GREY_TEXT = "#6a6a6a"

STYLESHEET = """
QDialog { background-color: #1e1e1e; color: #e8e8e8; }
QLabel { color: #d8d8d8; }

QFrame#projectTitle {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-left: 4px solid #5a8cff;
    border-radius: 6px;
}
QFrame#projectTitle QLabel { background: transparent; color: #f0f0f0; }

QFrame#headerBanner {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
}
QLabel#bannerText { background: transparent; color: #e8e8e8; font-size: 13px; }

QGroupBox {
    background-color: #252526;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    margin-top: 16px;
    padding: 12px 10px 10px 10px;
    color: #e8e8e8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #9a9a9a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.6px;
}

QLabel#filterLabel {
    color: #9a9a9a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    padding-right: 6px;
}

QPushButton {
    background-color: #2d2d30;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px 14px;
    color: #e8e8e8;
    font-size: 12px;
}
QPushButton:hover { background-color: #38383b; border-color: #505054; }
QPushButton:pressed { background-color: #1e1e1e; }
QPushButton:disabled { color: #5a5a5a; background-color: #232325; }

QPushButton#filterPill {
    border-radius: 3px;
    padding: 5px 14px;
    background-color: #2a2a2c;
    border: 1px solid #3a3a3a;
}
QPushButton#filterPill:hover { border-color: #5a8cff; color: #ffffff; }
QPushButton#filterPill:checked {
    background-color: #2c4870;
    border-color: #5a8cff;
    color: #ffffff;
    font-weight: 600;
}

/* Action button variants */
QPushButton#primaryAction, QPushButton#secondaryAction, QPushButton#updateAction,
QPushButton#warningAction, QPushButton#dangerAction, QPushButton#selectedAction,
QPushButton#duplicateAction { font-weight: 600; padding: 8px 18px; }

QPushButton#primaryAction { background-color: #2f5a3a; border: 1px solid #4a7a4a; color: #eaf5ea; }
QPushButton#primaryAction:hover { background-color: #3a6a45; border-color: #5fa860; }

QPushButton#secondaryAction { background-color: #3a3a5a; border: 1px solid #4f4f7a; color: #e8e8f5; }
QPushButton#secondaryAction:hover { background-color: #45456a; border-color: #6868a0; }


QPushButton#warningAction { background-color: #5a4a2a; border: 1px solid #7a653a; color: #f4e8d4; }
QPushButton#warningAction:hover { background-color: #6a5530; border-color: #9a7e4a; }

QPushButton#updateAction { background-color: #6a4a30; border: 1px solid #8a623a; color: #f5dec0; }
QPushButton#updateAction:hover { background-color: #7a5538; border-color: #a87a4a; }

QPushButton#dangerAction { background-color: #6a2f2f; border: 1px solid #8a3a3a; color: #f5d6d6; }
QPushButton#dangerAction:hover { background-color: #7a3838; border-color: #a64a4a; }

QPushButton#selectedAction { background-color: #2a5a5a; border: 1px solid #3a7a7a; color: #d6f5f5; }
QPushButton#selectedAction:hover { background-color: #35706a; border-color: #4aa8a0; }

QPushButton#duplicateAction { background-color: #4a3560; border: 1px solid #6a4f8a; color: #e6d6f5; }
QPushButton#duplicateAction:hover { background-color: #573f74; border-color: #8a68b0; }

QPushButton#primaryAction:disabled, QPushButton#updateAction:disabled,
QPushButton#selectedAction:disabled {
    background-color: #2a2a2c;
    border: 1px solid #3a3a3a;
    color: #5a5a5a;
}

/* Render Manager Force Live toggle, same family as the action buttons:
   light grey, then dark grey and sunken while the force is on */
QPushButton#forceLiveButton {
    background-color: #4a4a4e;
    border: 1px solid #66666a;
    border-radius: 4px;
    padding: 0 8px;
    color: #f0f0f0;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#forceLiveButton:hover { background-color: #55555a; border-color: #7e7e84; }
QPushButton#forceLiveButton:checked {
    background-color: #232325;
    border: 1px solid #1a1a1c;
    border-top: 2px solid #111112;
    color: #a8a8ac;
}
QPushButton#forceLiveButton:checked:hover { background-color: #2c2c2f; }
QPushButton#forceLiveButton:disabled { background-color: #2a2a2c; border: 1px solid #3a3a3a; color: #5a5a5a; }

/* Sanity check dialog */
QProgressBar#sanityBar { background-color: #2a2a2c; border: 1px solid #3a3a3a; border-radius: 5px; }
QProgressBar#sanityBar::chunk { background-color: #5a8cff; border-radius: 4px; }
QLabel#sanityRule { font-size: 13px; padding: 3px 2px; color: #8a8a8a; }
QLabel#sanityRule[state="running"] { color: #8fb4ff; font-weight: 600; }
QLabel#sanityRule[state="passed"] { color: #8ac68a; }
QLabel#sanityRule[state="failed"] { color: #f08a8a; font-weight: 600; }
QLabel#sanityHelp { color: #b8b8b8; }

/* Per-row icon buttons: hide (trash), recover, freeze */
QPushButton#hideButton, QPushButton#recoverButton, QPushButton#freezeButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 0;
}
QPushButton#hideButton { color: #9a6a6a; }
QPushButton#hideButton:hover { background-color: #3a2a2a; border-color: #7a3a3a; color: #f5d6d6; }
QPushButton#recoverButton { color: #6a9a6a; }
QPushButton#recoverButton:hover { background-color: #2a3a2a; border-color: #4a7a4a; color: #d6f5d6; }
QPushButton#freezeButton { color: #6a90a8; }
QPushButton#freezeButton:hover { background-color: #23343f; border-color: #3f6a80; color: #cfe6f2; }
QPushButton#freezeButton:disabled { color: #4a4a4a; background-color: transparent; border-color: transparent; }
QPushButton#freezeButton[frozen="true"] { color: #6ac3e0; background-color: #1b2f3b; border-color: #3f6a80; }
QPushButton#freezeButton[frozen="true"]:hover { background-color: #23414f; color: #a8ddef; }

QTableWidget {
    background-color: #1f1f20;
    alternate-background-color: #25252a;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    gridline-color: #2e2e30;
    color: #e8e8e8;
    selection-background-color: #2c4870;
    selection-color: #ffffff;
}
QTableWidget::item { padding: 6px 4px; }
QTableWidget::item:selected { background-color: #2c4870; color: #ffffff; }
QHeaderView { background-color: #252526; }
QHeaderView::section {
    background-color: #2a2a2c;
    border: none;
    border-right: 1px solid #353537;
    border-bottom: 1px solid #353537;
    padding: 9px 6px;
    color: #9a9a9a;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.3px;
}

QComboBox, QLineEdit {
    background-color: #2d2d30;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    padding: 4px 7px;
    color: #e8e8e8;
}
QComboBox:hover, QLineEdit:hover { border-color: #4a4a4d; }
QLineEdit:focus, QComboBox:focus { border-color: #5a8cff; }
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background-color: #2d2d30;
    border: 1px solid #3a3a3a;
    selection-background-color: #2c4870;
    color: #e8e8e8;
    padding: 2px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #4a4a4d;
    border-radius: 3px;
    background-color: #2d2d30;
}
QCheckBox::indicator:checked { background-color: #5a8cff; border-color: #5a8cff; }
QCheckBox::indicator:hover { border-color: #5a8cff; }

QScrollBar:vertical { background-color: transparent; width: 10px; border: none; margin: 2px; }
QScrollBar::handle:vertical { background-color: #3a3a3d; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #50505a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: transparent; height: 10px; border: none; margin: 2px; }
QScrollBar::handle:horizontal { background-color: #3a3a3d; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #50505a; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QMenu { background-color: #252526; border: 1px solid #3a3a3a; color: #e8e8e8; padding: 4px; }
QMenu::item { padding: 6px 18px; border-radius: 3px; }
QMenu::item:selected { background-color: #2c4870; color: #ffffff; }

/* Tab headers are checkable QPushButtons: QTabBar's selected-tab vertical
   shift clips bold text in Nuke 15's PySide2 and can't be styled away. */
QPushButton#tabHeader {
    background-color: #2a2a2c;
    color: #9a9a9a;
    border: 1px solid #3a3a3a;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 9px 22px;
    margin: 0;
    font-weight: bold;
    font-size: 11px;
}
QPushButton#tabHeader:hover { background-color: #38383b; color: #e8e8e8; }
QPushButton#tabHeader:checked { background-color: #1e1e1e; color: #ffffff; border-color: #5a8cff; }

QPlainTextEdit#logView {
    background-color: #141416;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    color: #d8d8d8;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    padding: 8px;
    selection-background-color: #2c4870;
    selection-color: #ffffff;
}

QFrame#statusBar { background-color: #202021; border-top: 1px solid #2a2a2a; }
QLabel#statusText { color: #7d7d7d; font-size: 10px; letter-spacing: 0.4px; }
QProgressBar#tickBar { background-color: #2a2a2a; border: none; border-radius: 3px; }
QProgressBar#tickBar::chunk { background-color: #5a8cff; border-radius: 3px; }

/* `outline: none` + NoFocus: Nuke's palette paints a lasting orange focus
   ring that reads as "still paused". */
QPushButton#pauseToggle {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 0;
    outline: none;
}
QPushButton#pauseToggle:hover { background-color: #2d2d30; border-color: #3a3a3a; }
QPushButton#pauseToggle:checked { background-color: #2d2d30; border-color: #5a8cff; }
QPushButton#pauseToggle:!checked { background-color: transparent; border-color: transparent; }
QPushButton#pauseToggle:focus { outline: none; }
"""
