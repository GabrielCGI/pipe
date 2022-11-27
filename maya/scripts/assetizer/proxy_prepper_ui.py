
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
import proxy_prepper as pp
importlib.reload(pp)


dir_global = "D:/gabriel/assetizer/assets"
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
        self.reduce_value = QtWidgets.QLineEdit(self)
        self.reduce_value.setText("3 60 3000")

        self.dir_image = QtWidgets.QLineEdit(self)
        self.dir_image.setText(self.get_image_dir())
        #maxEdgeLength=3,collapseThreshold=60, targetVertex= 3000


        #WIDGET CHECKBOX
        self.is_a_shot_asset =  QtWidgets.QCheckBox("is a shot asset")
        self.is_a_shot_asset.setChecked(True)

        self.display_label = QtWidgets.QLabel("Edge lenght: %s"%(pp.getsize(cmds.ls(selection=True)[0])))
        self.generate_proxy_button = QtWidgets.QPushButton("Generate proxy")
        self.bakeTexture_button = QtWidgets.QPushButton("Bake Texture")
        self.generate_lowpoly_button = QtWidgets.QPushButton("Generate Low poly")

        # ADD WIDGET TO LAYOUT

        self.button_layout.addWidget(self.display_label)
        self.button_layout.addWidget(self.is_a_shot_asset)
        self.button_layout.addWidget(self.dir_image )

        self.button_layout.addWidget(self.reduce_value )

        self.button_layout.addWidget(self.generate_proxy_button)
        self.button_layout.addWidget(self.bakeTexture_button)
        self.button_layout.addWidget(self.generate_lowpoly_button)


        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        self.generate_proxy_button.clicked.connect(self.generate_proxy_clicked)
        self.bakeTexture_button.clicked.connect(self.bakeTexture_button_clicked)
        self.generate_lowpoly_button.clicked.connect(self.generate_lowpoly_clicked)
        #self.publish_variant.clicked.connect(self.publish_variant_clicked)
        #sself.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        #self.use_latest.stateChanged.connect(self.use_latest_changed)

    def get_image_dir(self):
        filepath = cmds.file(q=True, sn=True)
        granpa =os.path.dirname(os.path.dirname(filepath))
        dir = os.path.join(granpa,"publish")
        os.makedirs(dir, exist_ok=True)
        return dir

    def generate_proxy_clicked(self):
        text = self.reduce_value.text()
        maxEdgeLength,collapseThreshold,targetVertex = text.split(" ")
        root = cmds.ls(selection=True)
        pp.proxy_generate(root, "proxy",float(maxEdgeLength), float(collapseThreshold),float(targetVertex))

    def bakeTexture_button_clicked(self):
        dir =self.dir_image.text()
        root = cmds.ls(selection=True)[0]
        pp.bake_texture(root,dir)

    def generate_lowpoly_clicked(self):
        pp.displace_disable()
        pass

try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
