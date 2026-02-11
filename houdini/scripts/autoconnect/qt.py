from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Always pick ONE version for typing (Qt6 going forward)
    from PySide6 import QtCore, QtWidgets, QtGui
else:
    try:
        # Houdini 21+
        from PySide6 import QtCore, QtWidgets, QtGui
    except ImportError:
        # Houdini 20
        from PySide2 import QtCore, QtWidgets, QtGui  # type: ignore
