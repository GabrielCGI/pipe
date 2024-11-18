import maya.cmds as cmds
# Retrieve the version of Maya currently in use
maya_version = cmds.about(version=True)

if maya_version.startswith("2022"):
    # Using PySide2 for Maya 2022
    from PySide2 import QtGui
elif maya_version.startswith("2025"):
    # Using PySide6 for Maya 2025
    # Note: QAction and QShortcut have moved from QtWidgets to QtGui in PySide6
    from PySide6 import QtGui

import os

iconDir = os.path.dirname(__file__)

editIcon = QtGui.QIcon(iconDir + '\\edit.png')
editorIcon = QtGui.QIcon(iconDir + '\\editor.png')
newTabIcon = QtGui.QIcon(iconDir + '\\newTab.png')
selectAllIcon = QtGui.QIcon(iconDir + '\\selectAll.png')
showAllIcon = QtGui.QIcon(iconDir + '\\showAll.png')
newSelSetIcon = QtGui.QIcon(iconDir + '\\newSelSet.png')
spaceSwitchIcon = QtGui.QIcon(iconDir + '\\spaceSwitch.png')
resetSelIcon = QtGui.QIcon(iconDir + '\\reset.png')
refreshIcon = QtGui.QIcon(iconDir + '\\refresh.png')