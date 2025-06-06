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