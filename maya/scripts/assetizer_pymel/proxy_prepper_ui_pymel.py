
"""
import sys
sys.path.append("C:/Users/monti/Documents/gabriel/assetizer")

import assetPublisher_ui
import importlib
importlib.reload(assetPublisher_ui)

"""

from maya import OpenMayaUI as omui
import os
import json
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2 import QtGui
from shiboken2 import wrapInstance
from pathlib import Path
import sys
import importlib
import utils_pymel as utils
import pymel.core as pm
import proxy_prepper_pymel as pp
importlib.reload(pp)
importlib.reload(utils)



def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)



class ProxyPrepper(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(ProxyPrepper, self).__init__(parent)
        self.qtSignal = QtCore.Signal()

        #################################################################
    def create(self):
        self.setWindowTitle("Proxy Prepper")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(300, 100) # re-size the window


        # LAYOUT
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.comboLayout = QtWidgets.QHBoxLayout(self)
        self.button_layout = QtWidgets.QVBoxLayout(self)
        self.reduce_layout = QtWidgets.QHBoxLayout(self)

        # WIDGET LIST
        #self.onlyInt = QtGui.QIntValidator()
        #self.onlyInt.setRange(0,100)
        self.reduce_value = QtWidgets.QSpinBox(self)
        self.reduce_value.setValue(90)
        self.reduce_value.setRange(0,100)
        self.reduce_value.setMaximumWidth(90)
        self.reduce_value.setMinimumWidth(30)
        #self.reduce_value.setValidator(self.onlyInt)
        #self.reduce_value.setText("85")
        self.proxy_baked_texture = QtWidgets.QCheckBox(self)
        self.proxy_baked_texture.setChecked(False)

        #self.dir_image = QtWidgets.QLineEdit(self)
        #self.dir_image.setText(self.get_image_dir())

        #WIDGET CHECKBOX



        self.display_label = QtWidgets.QLabel("Reduce %")
        self.display_label2 = QtWidgets.QLabel("Proxy with textures")
        self.generate_proxy_button = QtWidgets.QPushButton("Generate proxy")
        self.hierarchy = QtWidgets.QPushButton("Generate hierarchy")
        self.bakeTexture_button = QtWidgets.QPushButton("Proxy shader")
        self.generate_lowpoly_button = QtWidgets.QPushButton("Generate Low poly")
        self.hierarchy = QtWidgets.QPushButton("Generate hierarchy")

        # ADD WIDGET TO LAYOUT

        self.reduce_layout.addWidget(self.display_label)
        self.reduce_layout.addWidget(self.reduce_value )
        self.reduce_layout.addWidget(self.display_label2)
        self.reduce_layout.addWidget(self.proxy_baked_texture)
        #self.reduce_layout.addStretch()


        self.button_layout.addWidget(self.hierarchy)
        self.button_layout.addWidget(self.generate_lowpoly_button)
        self.button_layout.addWidget(self.generate_proxy_button)
        self.button_layout.addWidget(self.bakeTexture_button)


        #self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)
        self.mainLayout.addLayout(self.reduce_layout)

        #CONNECT WIDGET
        self.generate_proxy_button.clicked.connect(self.generate_proxy_clicked)
        self.bakeTexture_button.clicked.connect(self.bakeTexture_button_clicked)
        self.generate_lowpoly_button.clicked.connect(self.generate_lowpoly_clicked)
        self.hierarchy.clicked.connect(self.hierarchy_clicked)



    def hierarchy_clicked(self):
        obj = pm.ls(selection=True)
        pp.build_hiearchy(obj)
        self.hierarchy.setStyleSheet("background-color:rgb(110,150,110)")

    def get_image_dir(self):
        filepath = pm.system.sceneName()
        if filepath:
            granpa =os.path.dirname(os.path.dirname(filepath))
            dir = os.path.join(granpa,"publish","textures")
            dir = dir.replace("\\","/")
            return dir
        else:
            return "none"

    def generate_proxy_clicked(self):
        target_reduce = self.reduce_value.value()
        grp = pm.ls(selection=True)[0]
        self.generate_proxy_button.setStyleSheet("background-color:rgb(110,150,110)")
        pp.generate_proxy(grp, target_reduce)



    def bakeTexture_button_clicked(self):
        dir = self.get_image_dir()
        obj = pm.ls(selection=True)[0]
        pp.bake_texture(obj,dir,proxy_texture=self.proxy_baked_texture.isChecked())
        self.bakeTexture_button.setStyleSheet("background-color:rgb(110,150,110)")
    def generate_lowpoly_clicked(self):
        hd_grp =pm.ls(sl=True)[0]
        if not hd_grp.name().split("|")[-1].endswith('HD'):
            utils.warning("Please select HD group")
        pp.generate_lowpoly(hd_grp)
        self.generate_lowpoly_button.setStyleSheet("background-color:rgb(110,150,110)");
try:
    ui.deleteLater()
except:
    pass
ui = ProxyPrepper()
ui.create()
ui.show()
