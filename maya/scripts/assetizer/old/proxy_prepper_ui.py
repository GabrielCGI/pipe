
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
import utils as utils
import proxy_prepper as pp
importlib.reload(pp)
importlib.reload(utils)


dir_global = "D:/gabriel/assetizer/assets"
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

        # WIDGET LIST
        self.onlyInt = QtGui.QIntValidator()
        self.reduce_value = QtWidgets.QLineEdit(self)
        self.reduce_value.setValidator(self.onlyInt)
        self.reduce_value.setText("2000")

        self.dir_image = QtWidgets.QLineEdit(self)
        self.dir_image.setText(self.get_image_dir())

        #WIDGET CHECKBOX



        self.display_label = QtWidgets.QLabel("Bake texture directory")
        self.generate_proxy_button = QtWidgets.QPushButton("Generate proxy")
        self.hierarchy = QtWidgets.QPushButton("Generate hierarchy")
        self.bakeTexture_button = QtWidgets.QPushButton("Bake Texture")
        self.generate_lowpoly_button = QtWidgets.QPushButton("Generate Low poly")
        self.hierarchy = QtWidgets.QPushButton("Generate hierarchy")

        # ADD WIDGET TO LAYOUT

        self.button_layout.addWidget(self.display_label)

        self.button_layout.addWidget(self.dir_image )

        self.button_layout.addWidget(self.reduce_value )

        self.button_layout.addWidget(self.hierarchy)
        self.button_layout.addWidget(self.generate_lowpoly_button)
        self.button_layout.addWidget(self.generate_proxy_button)
        self.button_layout.addWidget(self.bakeTexture_button)

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)

        #CONNECT WIDGET
        self.generate_proxy_button.clicked.connect(self.generate_proxy_clicked)
        self.bakeTexture_button.clicked.connect(self.bakeTexture_button_clicked)
        self.generate_lowpoly_button.clicked.connect(self.generate_lowpoly_clicked)
        self.hierarchy.clicked.connect(self.hierarchy_clicked)


    def mergeuvs_button_clicked(self):
        obj = cmds.ls(selection=True)[0]
        pp.merge_uv_sets(obj)
    def hierarchy_clicked(self):
        pp.build_hiearchy()

    def get_image_dir(self):
        filepath = cmds.file(q=True, sn=True)
        if filepath:
            granpa =os.path.dirname(os.path.dirname(filepath))
            dir = os.path.join(granpa,"publish","textures")
            #dir= os.path.abspath(dir)
            dir = dir.replace("\\","/")
            os.makedirs(dir, exist_ok=True)
            return dir
        else:
            return "none"

    def generate_proxy_clicked(self):
        target_reduce = self.reduce_value.text()
        root = cmds.ls(selection=True,long=True)
        sel = cmds.ls(selection=True, long=True)[0]
        try:
            asset_name =  cmds.listRelatives(cmds.listRelatives(sel,parent=True, fullPath=True)[0],parent=True,fullPath=True)[0]
            asset_root = cmds.listRelatives(cmds.listRelatives(sel,parent=True, fullPath=True)[0],parent=True, fullPath=True)[0]

        except Exception as e:
            print(e)
            utils.warning("Please select a valide variant. Exemple: |rock|variant_basic|HD")
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog','asset Name:',text=asset_name.split("|")[-1]+"_proxy" )
        if ok:

            pp.proxy_generate(asset_name,asset_root, sel,text,int(target_reduce))
        else:
            utils.warning('abort by user')



    def bakeTexture_button_clicked(self):
        dir =self.dir_image.text()
        os.makedirs(dir, exist_ok = True)
        root = cmds.ls(selection=True)[0]
        pp.bake_texture(root,dir)

    def generate_lowpoly_clicked(self):
        hd_grp =cmds.ls(sl=True, long=True)[0]
        if hd_grp.split("|")[-1] != 'HD':
            utils.warning("Please select HD group")
        pp.generate_lowpoly(hd_grp)

try:
    ui.deleteLater()
except:
    pass
ui = ProxyPrepper()
ui.create()
ui.show()
