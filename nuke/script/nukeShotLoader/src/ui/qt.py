"""Qt binding shim: PySide6 on Nuke 16+, PySide2 on Nuke 15 and earlier."""


def _load_bindings():
    try:
        import nuke
        prefer_pyside6 = nuke.NUKE_VERSION_MAJOR >= 16
    except Exception:
        prefer_pyside6 = True  # outside Nuke: take whatever is installed

    if prefer_pyside6:
        try:
            from PySide6 import QtCore, QtGui, QtWidgets
            return QtCore, QtGui, QtWidgets, "PySide6"
        except ImportError:
            pass
    from PySide2 import QtCore, QtGui, QtWidgets
    return QtCore, QtGui, QtWidgets, "PySide2"


QtCore, QtGui, QtWidgets, PYSIDE_VERSION = _load_bindings()
