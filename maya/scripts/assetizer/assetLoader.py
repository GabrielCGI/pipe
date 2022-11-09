
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

def list_set_selected_byName(list,name):
    items = list.findItems(name,QtCore.Qt.MatchExactly)
    list.setCurrentItem(items[0])

def build_dso(asset_dir, asset_name, variantSet_name, variant_name, version):
    ass_name = "%s_%s_%s.ass"%(asset_name, variantSet_name,variant_name)
    dso = os.path.join(asset_dir,"publish","ass",variantSet_name,variant_name,version,ass_name)
    return dso

def build_maya_path(asset_dir, asset_name, variantSet_name, variant_name, version):
    ass_name = "%s_%s_%s.ma"%(asset_name, variantSet_name,variant_name)
    maya_path = os.path.join(asset_dir,"publish","ass",variantSet_name,variant_name,version,ass_name)
    return maya_path

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

        #ADD MAYA CALLBACK FRO SELECTION CHANGED
        self.selection_changed_callback = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.maya_selection_changed_callback)
        # LAYOUT
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.comboLayout = QtWidgets.QHBoxLayout(self)
        self.button_layout = QtWidgets.QVBoxLayout(self)

        # WIDGET
        self.variantSet_Qlist = QtWidgets.QListWidget()
        self.variant_Qlist = QtWidgets.QListWidget()
        self.version_Qlist = QtWidgets.QListWidget()


        self.display_label = QtWidgets.QLabel("Asset:")
        self.load_asset_button = QtWidgets.QPushButton("Select asset")
        self.convert_to_maya = QtWidgets.QPushButton("Convert to maya")
        self.set_version = QtWidgets.QPushButton("Set version")

        # ADD WIDGET TO LAYOUT

        self.comboLayout.addWidget(self.variantSet_Qlist)
        self.comboLayout.addWidget(self.variant_Qlist)
        self.comboLayout.addWidget(self.version_Qlist)

        self.button_layout.addWidget(self.display_label)
        self.button_layout.addWidget(self.load_asset_button)
        self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.convert_to_maya)

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        self.load_asset_button.clicked.connect(self.load_asset_clicked)
        self.set_version.clicked.connect(self.set_version_clicked)
        self.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        self.variantSet_Qlist.itemClicked.connect(self.variantSet_Qlist_changed)
        self.variant_Qlist.itemClicked.connect(self.variant_Qlist_changed)

    def load_asset_clicked(self):
        #GET PROXY NAME FROM MAYA SELECTION
        self.maya_proxy_name = cmds.ls(selection=True)[0]

        #Set label:
        self.display_label.setText("Asset: "+self.maya_proxy_name)
        #GET DSO
        asset_dso = cmds.getAttr(self.maya_proxy_name+".dso") # ex: D:\assets\toy\publish\ass\basic\HD\v001\truc.ass
        #GET ASSET INFOS
        self.asset_dir = Path(asset_dso).parents[5]  #ex: D:\assets\toy
        self.ass_dir = Path(asset_dso).parents[3] #ex: D:\assets\toy\publish\ass\
        dso_split = os.path.normpath(asset_dso).split(os.sep)
        self.current_variantSet = dso_split[-4]
        self.current_variant = dso_split[-3]
        self.current_version = dso_split[-2]
        self.asset_name = dso_split[-7]

        #BUILD DIC
        self.asset_dic = dic_tool.buildAssetDic(self.ass_dir)
        print(json.dumps(self.asset_dic ,indent=4))

        #CLEAR COMBOBOX
        self.variantSet_Qlist.clear()
        self.variant_Qlist.clear()
        self.version_Qlist.clear()

        #REBUILD ALL LIST
        self.rebuild_variantSet_Qlist()
        self.rebuild_variant_Qlist()
        self.rebuild_version_Qlist()

        #Set list selection from current item
        list_set_selected_byName(self.variantSet_Qlist,self.current_variantSet)
        list_set_selected_byName(self.variant_Qlist,self.current_variant)
        list_set_selected_byName(self.version_Qlist,self.current_version)


    ### QLIST CHANGED ###
    # ON VARIANT_SET CHANGE
    def variantSet_Qlist_changed(self):
        self.current_variantSet = self.variantSet_Qlist.currentItem().text()
        print(self.current_variantSet)
        self.rebuild_variant_Qlist()

    # ON VARIANT CHANGE
    def variant_Qlist_changed(self):
        self.current_variant = self.variant_Qlist.currentItem().text()
        self.rebuild_version_Qlist()

    def rebuild_variantSet_Qlist(self):
        self.variantSet_Qlist.clear()
        for variantSet in self.asset_dic.keys():
            self.variantSet_Qlist.addItem(variantSet)

    ### REBLUID  ###
    # REBUILD VARIANT LIST
    def rebuild_variant_Qlist(self):
        self.variant_Qlist.clear()
        self.version_Qlist.clear()
        for variant in self.asset_dic [self.current_variantSet]:
            self.variant_Qlist.addItem(variant)
        #SELECT THE FIRST ROW BY DEFAULT THEN REBUILD VERSION
        self.variant_Qlist.setCurrentRow(0)
        self.rebuild_version_Qlist()

    # REBUILD VERSION LIST
    def rebuild_version_Qlist(self):
        self.version_Qlist.clear()
        versions = self.asset_dic[self.current_variantSet][self.current_variant]
        versions.sort()
        versions.reverse()
        for version in versions:
            self.version_Qlist.addItem(version)
        #SELECT THE FIRST ROW BY DEFAULT
        self.version_Qlist.setCurrentRow(0)

    ### BUTTON CLICKED ###
    def set_version_clicked(self):
        variantSet_name = self.variantSet_Qlist.currentItem().text()
        variant_name = self.variant_Qlist.currentItem().text()
        version = self.version_Qlist.currentItem().text()
        new_dso = build_dso(self.asset_dir, self.asset_name, variantSet_name, variant_name, version)

        cmds.setAttr(self.maya_proxy_name+".dso",new_dso, type="string")
        cmds.setAttr()

    def convert_to_maya_clicked(self):
        #Get maya scene path
        variantSet_name = self.variantSet_Qlist.currentItem().text()
        variant_name = self.variant_Qlist.currentItem().text()
        version = self.version_Qlist.currentItem().text()
        maya_path = build_maya_path(self.asset_dir, self.asset_name, variantSet_name, variant_name, version)
        #Build a namescape
        namespace_for_creation = ("%s_%s_%s")%(self.asset_name,variantSet_name,variant_name)
        #Reference the maya scene
        maya_object = cmds.file(maya_path, reference=True, namespace=namespace_for_creation)
        #Get the REAL namesapce (with "RN" and versioning)
        namespace = cmds.file(maya_object, referenceNode=True, query=True)
        node= cmds.referenceQuery(namespace,nodes=True )
        cmds.matchTransform(node[0],self.maya_proxy_name)
        #Hide and rename proxy "TO_DELETE"
        cmds.setAttr(self.maya_proxy_name+".visibility",0)
        cmds.rename(self.maya_proxy_name,self.maya_proxy_name+"_TO_DELETE")

    def maya_selection_changed_callback(self,*args):
        try:
            self.load_asset_clicked()
        except Exception as e:
            print (e)
    def closeEvent(self, event):

        OpenMaya.MMessage.removeCallback(self.selection_changed_callback)


try:
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
