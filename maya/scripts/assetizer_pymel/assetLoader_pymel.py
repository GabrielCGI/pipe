
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

from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from pathlib import Path

import importlib


import utils_pymel as utils
importlib.reload(utils)
import pymel.core as pm

assets_directory  = utils.get_working_directory()


def list_set_selected_byName(list,name):
    items = list.findItems(name,QtCore.Qt.MatchExactly)
    if len(items)>0:
        list.setCurrentItem(items[0])

def build_dso(asset_dir, asset_name, variant_name, version):
    ass_name = "%s.ass"%(variant_name)
    dso = os.path.join(asset_dir,"publish","ass",variant_name,version,ass_name)
    return dso

def build_maya_path(asset_dir, asset_name, variant_name, version):
    maya_name = "%s.ma"%(variant_name)
    maya_path = os.path.join(asset_dir,"publish","ass",variant_name,version,maya_name)
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

        # WIDGET LIST

        self.variant_Qlist = QtWidgets.QListWidget()
        self.version_Qlist = QtWidgets.QListWidget()


        #WIDGET CHECKBOX


        self.display_label = QtWidgets.QLabel("Asset:")
        #self.push_edit_button = QtWidgets.QPushButton("Push edit")
        self.convert_to_maya = QtWidgets.QPushButton("Convert to maya")
        self.set_version = QtWidgets.QPushButton("Set version")

        # ADD WIDGET TO LAYOUT


        self.comboLayout.addWidget(self.variant_Qlist)
        self.comboLayout.addWidget(self.version_Qlist)


        self.button_layout.addWidget(self.display_label)
        #self.button_layout.addWidget(self.push_edit_button)
        self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.convert_to_maya)

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        #self.push_edit_button.clicked.connect(self.push_edit_clicked)
        self.set_version.clicked.connect(self.set_version_clicked)
        self.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)

        self.variant_Qlist.itemClicked.connect(self.variant_Qlist_changed)

        self.load_asset_clicked()

    def checkAsset(self):
        check = True
        error_msg = ""
        sel = pm.ls(selection=True)
        if not sel:
            error_msg += "No selection"
            check = False
        try:
            if not sel[0].dso.get():
                error_msg += "No dso"
                check = False
        except:
            error_msg += "No dso"
            check = False    
        try:      
            if sel[0].ai_translator.get() != "procedural":
                error_msg += "Not a procedural"
                check = False
        except:
            error_msg += "No dso"
            check = False               
        return sel, check, error_msg


    def load_asset_clicked(self):
        #GET PROXY NAME FROM MAYA SELECTION

        sel, check, error_msg = self.checkAsset()

        if check == False:
            self.display_label.setText("The current selected obj is not a standin")
            self.display_label.setStyleSheet("color: None")

            self.variant_Qlist.clear()
            self.version_Qlist.clear()
            return
        else:
            self.proxy=sel[0]

    
        #Set label:
        self.display_label.setText("Asset: "+self.proxy.name())
        #GET DSO
        asset_dso = self.proxy.dso.get() 
        #GET ASSET INFOS
        self.asset_dir = Path(asset_dso).parents[4] 
        print(self.asset_dir)
        self.ass_dir = Path(asset_dso).parents[2] 

        dso_split = os.path.normpath(asset_dso).split(os.sep)
        print(dso_split)
        self.current_variant = dso_split[-3]
        self.current_version = dso_split[-2]
        self.asset_name = dso_split[-6]


        #BUILD DIC
        self.asset_dic = utils.scan_ass_directory(self.ass_dir)
        print(self.ass_dir)

        #CLEAR COMBOBOX
        self.variant_Qlist.clear()
        self.version_Qlist.clear()

        #REBUILD ALL LIST
        self.rebuild_variant_Qlist()
        self.rebuild_version_Qlist()


        #Set list selection from current item
        list_set_selected_byName(self.variant_Qlist,self.current_variant)
        list_set_selected_byName(self.version_Qlist,self.current_version)

        if self.current_version != self.version_Qlist.item(0).text():
            self.display_label.setText("Out of date - %s %s"%(self.current_variant,self.current_version))
            self.display_label.setStyleSheet("color: yellow")
        else:
            self.display_label.setText("Up to date -  %s %s"%(self.current_variant,self.current_version))
            self.display_label.setStyleSheet("color: green")



    ### QLIST CHANGED ###


    # ON VARIANT CHANGE
    def variant_Qlist_changed(self):
        self.current_variant = self.variant_Qlist.currentItem().text()
        self.rebuild_version_Qlist()



    ### REBLUID  ###
    # REBUILD VARIANT LIST
    def rebuild_variant_Qlist(self):
        self.variant_Qlist.clear()
        self.version_Qlist.clear()
        for variant in self.asset_dic.keys():
            self.variant_Qlist.addItem(variant)
        #SELECT THE FIRST ROW BY DEFAULT THEN REBUILD VERSION
        self.variant_Qlist.setCurrentRow(0)
        self.rebuild_version_Qlist()

    # REBUILD VERSION LIST
    def rebuild_version_Qlist(self):
        self.version_Qlist.clear()
        versions = self.asset_dic[self.current_variant]
        versions.sort()
        versions.reverse()
        for version in versions:
            self.version_Qlist.addItem(version)
        #SELECT THE FIRST ROW BY DEFAULT
        self.version_Qlist.setCurrentRow(0)

    ### BUTTON CLICKED ###
    def set_version_clicked(self):
        variant_name = self.variant_Qlist.currentItem().text()
        version = self.version_Qlist.currentItem().text()
        new_dso = build_dso(self.asset_dir, self.asset_name, variant_name, version)
        self.proxy.dso.set(new_dso)

        if version != self.version_Qlist.item(0).text():
            self.display_label.setText("Out of date - %s %s"%( variant_name, version))
            self.display_label.setStyleSheet("color: yellow")
        else:
            self.display_label.setText("Up to date - %s %s"%(variant_name, version))
            self.display_label.setStyleSheet("color: green")


    def convert_to_maya_clicked(self):
        #Get maya scene path
        variant_name = self.variant_Qlist.currentItem().text()
        version = self.version_Qlist.currentItem().text()
        maya_path = build_maya_path(self.asset_dir, self.asset_name,variant_name, version)
        #Build a namescape
        namespace_for_creation = utils.nameSpace_from_path(maya_path)
        #Reference the maya scene

        refNode = pm.system.createReference(maya_path, namespace=namespace_for_creation)
        nodes = pm.FileReference.nodes(refNode)
        utils.match_matrix(nodes[0],self.proxy)

        self.proxy.visibility.set(False)



    def maya_selection_changed_callback(self,*args):
        try:
            return
            self.load_asset_clicked()
        except Exception as e:
            print (e)

    def closeEvent(self, event):

        OpenMaya.MMessage.removeCallback(self.selection_changed_callback)


try:
    OpenMaya.MMessage.removeCallback(ui.selection_changed_callback)
    ui.deleteLater()
except:
    pass
ui = AssetLoader()
ui.create()
ui.show()
