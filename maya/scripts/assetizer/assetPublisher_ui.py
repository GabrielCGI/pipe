
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
from shiboken2 import wrapInstance
from pathlib import Path
import sys
import assTools
import importlib
importlib.reload(assTools)

dir_global = "D:/proA/assets"
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
        self.is_a_shot_asset =  QtWidgets.QCheckBox("is a shot asset")
        self.is_a_shot_asset.setChecked(True)

        self.keep_original =  QtWidgets.QCheckBox("keep original")
        self.keep_original.setChecked(False)

        self.import_published =  QtWidgets.QCheckBox("import published")
        self.import_published.setChecked(True)

        self.display_label = QtWidgets.QLabel("Asset:")
        self.publish_asset = QtWidgets.QPushButton("Publish selected asset")
        self.publish_variant = QtWidgets.QPushButton("Publish selected variant")
        self.set_version = QtWidgets.QPushButton("Set version")

        # ADD WIDGET TO LAYOUT


        self.button_layout.addWidget(self.is_a_shot_asset)
        self.button_layout.addWidget(self.keep_original)
        self.button_layout.addWidget(self.import_published)

        self.button_layout.addWidget(self.display_label)
        self.button_layout.addWidget(self.publish_asset)
        #self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.publish_variant )

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        self.publish_asset.clicked.connect(self.publish_asset_clicked)
        self.publish_variant.clicked.connect(self.publish_variant_clicked)
        #sself.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        #self.use_latest.stateChanged.connect(self.use_latest_changed)

    def publish_asset_clicked(self):
        assTools.ask_save()
        sel = cmds.ls(selection=True,long=True)
        dir = self.get_dir()
        try:
            obj = sel[0]
        except:
            assTools.warning("The selected obj is not working -> %s"%sel)
        matrix = cmds.xform(obj, worldSpace = True, matrix=True, query=True)
        new_obj, original_obj, proxy = assTools.cleanAsset(obj, needProxy=True)
        asset, variants = assTools.scanAsset(new_obj)
        proxy = assTools.get_from_asset(asset.name_long, asset.name+"_proxy",must_exist=True)
        sub_assets = assTools.get_from_asset(asset.name_long, "sub_assets", must_exist=False)

        for v in variants:
            assTools.exportVariant(dir, asset, v, export_shading_scene = True)
        publish_proxy_scene = assTools.make_proxy_scene(asset.name,dir,proxy,sub_assets)
        if self.import_published.isChecked():
            maya_object = cmds.file(publish_proxy_scene, reference=True, namespace=asset.name)
            nodes= cmds.referenceQuery(maya_object ,nodes=True)
            cmds.xform(nodes[0],  matrix=matrix )
        cmds.delete(asset.name_long)
        assTools.deleteSource(original_obj, asset.name_long, asset.name, self.keep_original.isChecked())


    def publish_variant_clicked(self):
        sel = cmds.ls(selection=True,long=True)
        dir = self.get_dir()
        try:
            var_set = cmds.listRelatives(sel[0], parent=True)
            obj= cmds.listRelatives(var_set[0],parent=True)[0]
        except:
            assTools.warning("The selected obj is not working -> %s"%sel)

        new_obj, original_obj, proxy = assTools.cleanAsset(obj, needProxy=False)
        asset, variants = assTools.scanAsset(new_obj)
        sub_assets = assTools.get_from_asset(asset.name_long, "sub_assets", must_exist=False)
        for v in variants:
            if assTools.short_name(sel[0]) == v.name:
                assTools.exportVariant(dir, asset, v, export_shading_scene = True)

        cmds.delete(asset.name_long)
        assTools.deleteSource(original_obj, asset.name_long, asset.name, self.keep_original.isChecked())

    def get_dir(self):
        if self.is_a_shot_asset.isChecked():
            filepath = cmds.file(q=True, sn=True)
            dir =os.path.dirname(filepath)
        else:
            dir = dir_global
        return dir
try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
