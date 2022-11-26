
"""
import sys
sys.path.append("D:/gabriel/assetizer/scripts")

import assetLoader
import importlib
importlib.reload(assetLoader)

"""


import maya.OpenMaya as OpenMaya
from maya import OpenMaya

from maya import OpenMayaUI as omui
import os
import json
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from pathlib import Path

import asset as assetTool
import importlib
importlib.reload(assetTool)
import dic as dic_tool
importlib.reload(dic_tool)



def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)



class AssetLoader(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(AssetLoader, self).__init__(parent)
        self.qtSignal = QtCore.Signal()

        #################################################################
    def create(self):
        self.setWindowTitle("AssetLoader")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(300, 100) # re-size the window

        # LAYOUT
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.comboLayout = QtWidgets.QHBoxLayout(self)
        self.button_layout = QtWidgets.QVBoxLayout(self)

        # WIDGET LIST


        #WIDGET CHECKBOX
        self.use_latest =  QtWidgets.QCheckBox("Use latest version")
        self.use_latest.setChecked(True)


        self.display_label = QtWidgets.QLabel("Asset:")
        self.push_edit_button = QtWidgets.QPushButton("Push edit")
        self.convert_to_maya = QtWidgets.QPushButton("Convert to maya")
        self.set_version = QtWidgets.QPushButton("Set version")

        # ADD WIDGET TO LAYOUT


        self.button_layout.addWidget(self.use_latest)
        self.button_layout.addWidget(self.display_label)
        self.button_layout.addWidget(self.push_edit_button)
        self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.convert_to_maya)

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        #self.push_edit_button.clicked.connect(self.push_edit_clicked)
        #self.set_version.clicked.connect(self.set_version_clicked)
        #sself.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        #self.use_latest.stateChanged.connect(self.use_latest_changed)


try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
