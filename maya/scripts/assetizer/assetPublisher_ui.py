
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
        self.checkbox_layout = QtWidgets.QHBoxLayout(self)


        # WIDGET LIST


        #WIDGET CHECKBOX
        self.is_a_shot_asset =  QtWidgets.QCheckBox("Next to scene")
        self.delete_after_publish =  QtWidgets.QCheckBox("Delete source")
        self.import_published =  QtWidgets.QCheckBox("Import published ")
        self.init_checkbox()


        #self.display_label = QtWidgets.QLabel("Shot mode")
        self.publish_asset = QtWidgets.QPushButton("Publish selected asset")
        self.publish_variant = QtWidgets.QPushButton("Publish selected variant")
        self.set_version = QtWidgets.QPushButton("Set version")


        # ADD WIDGET TO LAYOUT
        #self.checkbox_layout.addWidget(self.display_label)

        self.checkbox_layout.addWidget(self.delete_after_publish)
        self.checkbox_layout.addWidget(self.is_a_shot_asset)
        self.checkbox_layout.addWidget(self.import_published)
        self.checkbox_layout.addStretch()




        self.button_layout.addWidget(self.publish_asset)
        self.button_layout.addWidget(self.publish_variant )
        #self.button_layout.addWidget(self.display_label)


        self.mainLayout.addLayout(self.button_layout)
        self.mainLayout.addLayout(self.checkbox_layout)


        #CONNECT WIDGET
        self.publish_asset.clicked.connect(self.publish_asset_clicked)
        self.publish_variant.clicked.connect(self.publish_variant_clicked)

    def init_checkbox(self):
        filepath = cmds.file(q=True, sn=True)
        if filepath:
            split = filepath.split("/")
            if split[-2] != "shading":
                self.delete_after_publish.setChecked(True)
                self.is_a_shot_asset.setChecked(True)
                self.import_published.setChecked(True)




    def publish_asset_clicked(self):
        assTools.ask_save()
        sel = cmds.ls(selection=True,long=True)
        if not sel: assTools.warning("The selected obj is not working -> %s"%sel)
        if len(sel)>1: assTools.warning("Too many object selected -> %s"%sel)
        proxy = sel[0]+"|"+assTools.short_name(sel[0])+"_proxy"
        if not cmds.objExists(proxy): assTools.warning("need proxy!")
        dir = self.get_dir()
        matrix = cmds.xform(sel[0], worldSpace = True, matrix=True, query=True)
        parent = cmds.listRelatives(sel[0],parent=True)
        if parent: parent=parent[0]
        asset, variants, proxy, asset_og_name_long = assTools.cleanAsset(sel)
        sub_assets = assTools.get_from_asset(asset.name_long, "sub_assets", must_exist=False)

        for v in variants:
            assTools.exportVariant(dir, asset, v, export_shading_scene = True)
        publish_proxy_scene, proxy = assTools.make_proxy_scene(asset.name,dir,proxy,sub_assets)
        if self.import_published.isChecked():
            maya_object = cmds.file(publish_proxy_scene, reference=True, namespace=asset.name)
            nodes= cmds.referenceQuery(maya_object ,nodes=True)
            cmds.xform(nodes[0],  matrix=matrix )
            if parent: cmds.parent(nodes[0],parent)
        cmds.delete(asset.name_long)
        cmds.delete(proxy)

        if self.delete_after_publish.isChecked():
            assTools.deleteSource(asset_og_name_long)


    def publish_variant_clicked(self):
        sel = cmds.ls(selection=True,long=True)
        dir = self.get_dir()
        try:
            var_set = cmds.listRelatives(sel[0], parent=True,fullPath=True)
            asset_maya= cmds.listRelatives(var_set[0],parent=True,fullPath=True)
        except:
            assTools.warning("The selected obj is not working -> %s"%sel)
        variant_name= assTools.short_name(sel[0])
        asset, variants, proxy, asset_og_name_long = assTools.cleanAsset(asset_maya)
        for v in variants:
            if variant_name== v.name:
                assTools.exportVariant(dir, asset, v, export_shading_scene = True)

        cmds.delete(asset.name_long)
        if self.delete_after_publish.isChecked():
            assTools.deleteSource(asset_og_name_long)

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
