
"""
import sys
sys.path.append("C:/Users/monti/Documents/gabriel/assetizer")

import assetPublisher_ui
import importlib
importlib.reload(assetPublisher_ui)

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

import assTools
import importlib
importlib.reload(assTools)


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
        self.publish_asset = QtWidgets.QPushButton("Publish selected asset")
        self.publish_variant = QtWidgets.QPushButton("Publish selected variant")
        self.set_version = QtWidgets.QPushButton("Set version")

        # ADD WIDGET TO LAYOUT


        self.button_layout.addWidget(self.use_latest)
        self.button_layout.addWidget(self.display_label)
        self.button_layout.addWidget(self.publish_asset)
        self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.publish_variant )

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        self.publish_asset.clicked.connect(self.publish_asset_clicked)
        self.publish_variant.clicked.connect(self.publish_variant_clicked)
        #sself.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        #self.use_latest.stateChanged.connect(self.use_latest_changed)

    def publish_asset_clicked(self):
        sel = cmds.ls(selection=True)[0]
        obj = assTools.cleanAssetBeforeExport(sel)
        if not obj: return
        asset, variants = assTools.scanAsset(obj)
        sub_assets = assTools.get_from_asset(asset.name_long, "sub_assets")
        proxy = assTools.get_from_asset(asset.name_long, asset.name+"_proxy")
        if not obj: return
        if not asset: return
        if not proxy: return

        dir = "D:/gabriel/assetizer/shots/shot10/lighting/assets"
        for v in variants:
            assTools.printInfo(v)
            assTools.exportVariant(dir, asset, v, export_shading_scene = True)

        assTools.make_proxy_scene(asset.name,dir,proxy,sub_assets)
    def publish_variant_clicked(self):
        asset=None
        sel = cmds.ls(selection=True)
        if not sel:
            cmds.warning("Select something !")
            return
        variant_select = sel[0]
        variant_set = cmds.listRelatives(variant_select, parent = True, fullPath=True)
        if variant_set:
            parent = cmds.listRelatives(variant_set[0], parent = True, fullPath=True)
            if parent:
                asset=parent[0]
                if not asset:
                    cmds.warning("No variant selected.")
        if not asset:cmds.warning("No variant selected.")

        obj = assTools.cleanAssetBeforeExport(asset)
        if not obj:
            cmds.warning("cleanAssetBeforeExport asset went wrong")
            return
        asset, variants = assTools.scanAsset(obj)
        if any( [asset == None, variants == None,obj==None] ):
            cmds.warning("scanAsset went wrong... ")
            return


        dir = "D:/gabriel/assetizer/shots/shot10/lighting/assets"
        for v in variants:
            if v.name == variant_select:
                assTools.exportVariant(dir, asset, v, export_shading_scene = True)

try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
