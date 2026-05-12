from typing import TYPE_CHECKING
import hou


major_version = hou.applicationVersion()[0]
if TYPE_CHECKING:
    major_version = hou.applicationVersion()[0]
    if major_version <= 20:
        from PySide2 import QtCore, QtWidgets, QtGui  # type: ignore
    else:
        from PySide6 import QtCore, QtWidgets, QtGui  # type: ignore
else:
    major_version = hou.applicationVersion()[0]
    if major_version <= 20:
        from PySide2 import QtCore, QtWidgets, QtGui  # type: ignore
    else:
        from PySide6 import QtCore, QtWidgets, QtGui  # noqa: F401
