
"""
import sys
sys.path.append("D:/gabriel/assetizer/scripts")

import ABC_pipelineExport
import importlib
importlib.reload(ABC_pipelineExport)

"""

import json

from PySide2 import QtCore, QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui
import os
import importlib
import abcPipelineExport_pymel as ppExp
importlib.reload(ppExp)

import pymel.core as pm


def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)




class ABC_pipelineExport(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(ABC_pipelineExport, self).__init__(parent)
        self.qtSignal = QtCore.Signal()

        #################################################################
    def create(self):
        self.setWindowTitle("ABC_pipelineExport")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(300, 500) # re-size the window

        #ADD MAYA CALLBACK FRO SELECTION CHANGED

        # LAYOUT
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.comboLayout = QtWidgets.QHBoxLayout(self)
        self.button_layout = QtWidgets.QVBoxLayout(self)
        self.range_layout =  QtWidgets.QHBoxLayout(self)

        # WIDGET LIST

        self.char_Qlist = QtWidgets.QListWidget()
        self.char_Qlist.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.populate_char_list()

        onlyInt = QtGui.QIntValidator()
        self.start_input = QtWidgets.QLineEdit(self)
        self.start_input.setValidator(onlyInt)
        self.start_input.setText(str(int(pm.playbackOptions(min=True, query=True))))
        self.end_input = QtWidgets.QLineEdit(self)
        self.end_input.setText(str(int(pm.playbackOptions(max=True, query=True))))
        self.end_input.setValidator(onlyInt)
        #WIDGET CHECKBOX

        self.display_label = QtWidgets.QLabel("Start/End:")
        self.export_button = QtWidgets.QPushButton("Export selected")

        # ADD WIDGET TO LAYOUT

        self.comboLayout.addWidget(self.char_Qlist)

        self.range_layout.addWidget(self.display_label)
        self.range_layout.addWidget(self.start_input )
        self.range_layout.addWidget(self.end_input)

        self.button_layout.addWidget(self.export_button)

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.range_layout)
        self.mainLayout.addLayout(self.button_layout)

        self.export_button.clicked.connect(self.export_button_clicked)

    def populate_char_list(self):
        self.char_Qlist.clear()
        char_list = ppExp.list_char_in_scene()
        for char in char_list:
            item = QtWidgets.QListWidgetItem()
            item.setText(char.name+"_"+char.version)
            item.setData(QtCore.Qt.UserRole,char)
            self.char_Qlist.addItem(item)

    def export_button_clicked(self):
        scene_name = pm.system.sceneName()
        abc_dir = os.path.join(os.path.dirname(os.path.dirname(scene_name)),"abc")
        if not os.path.isdir(abc_dir):
            abc_dir = os.path.dirname(abc_dir)

        export_dir = QtWidgets.QFileDialog.getExistingDirectory(self,abc_dir)
        if not export_dir:
            return
        start = self.start_input.text()
        end = self.end_input.text()

        items = self.char_Qlist.selectedItems()
        for item in items:
            char = item.data(QtCore.Qt.UserRole)
            ppExp.exportAbc(char, export_dir, start, end)

        #CONNECT WIDGET
        #self.push_edit_button.clicked.connect(self.push_edit_clicked)
        #self.set_version.clicked.connect(self.set_version_clicked)




try:
    ui.deleteLater()
except:
    pass
ui = ABC_pipelineExport()
ui.create()
ui.show()
