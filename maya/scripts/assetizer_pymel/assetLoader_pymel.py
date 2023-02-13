
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
import API_ass
importlib.reload(API_ass)

assets_directory  = utils.get_assets_directory()


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
    if not os.path.exists(maya_path):
        raw_name, extension = os.path.splitext(maya_path)
        maya_mb_path = raw_name+".mb"
        if os.path.exists(maya_mb_path):
            return maya_mb_path

    return maya_path

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)



class Proxy():
    def __init__(self, maya):
        self.maya = maya


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
        self.add_transform = QtWidgets.QPushButton("Add transforms")
        #self.switch_proxy_type = QtWidgets.QPushButton("Convert to procedural")

        # ADD WIDGET TO LAYOUT


        self.comboLayout.addWidget(self.variant_Qlist)
        self.comboLayout.addWidget(self.version_Qlist)


        self.button_layout.addWidget(self.display_label)
        #self.button_layout.addWidget(self.push_edit_button)
        self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.convert_to_maya)
        self.button_layout.addWidget(self.add_transform)
        #self.button_layout.addWidget(self.switch_proxy_type)


        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        #self.push_edit_button.clicked.connect(self.push_edit_clicked)
        self.set_version.clicked.connect(self.set_version_clicked)
        self.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        self.add_transform.clicked.connect(self.add_transform_clicked)
        #self.switch_proxy_type.clicked.connect(self.switch_proxy_type_clicked)

        self.variant_Qlist.itemClicked.connect(self.variant_Qlist_changed)


        self.load_asset_clicked()

    def checkAsset(self):
        check = True
        error_msg = ""
        sel = pm.ls(selection=True)
        if not sel:
            check= False
            error_msg = "No selection"
            return sel, check, error_msg
        else:
            sel=sel[0]

        try:
            shape = sel.getShape()
        except:
            shape = False
            pass
        if shape:
            if pm.objectType(shape)=="mesh":
                try:
                    if sel.getParent().getShape().hasAttr('dso'):
                        sel = sel.getParent()
                        print("SETTING PARENT %s"%sel)
                    else:
                        check=False
                        error_msg = "Not a procedural"
                        return sel, check, error_msg
                except:
                    check=False
                    error_msg = "Not a procedural"
                    return sel, check, error_msg

        print (sel)
        if not sel:
                check=False
                error_msg = "Not a procedural"
                return sel, check, error_msg


        if not sel.hasAttr("dso"):
                check=False
                error_msg = "Not a procedural"
                return sel, check, error_msg

        if not os.path.isfile(sel.dso.get()):
            check=False
            error_msg = "Not a valid path"
            return sel, check, error_msg
        if pm.objectType(sel) == "aiStandIn" or pm.objectType(sel) == "mesh":
            sel=sel.getParent()

        return sel, check, error_msg

    def add_transform_clicked(self):
        API_ass.run(self.proxy.getShape())

    def load_asset_clicked(self):
        #GET PROXY NAME FROM MAYA SELECTION

        sel, check, error_msg = self.checkAsset()
        print(error_msg)

        if check == False:
            self.isValid = False
            self.display_label.setText("The current selected obj is not a standIn")
            self.display_label.setStyleSheet("color: None")
            self.variant_Qlist.clear()
            self.version_Qlist.clear()
            return
        else:
            self.isValid = True
            self.proxy=sel
            self.proxyShape = pm.listRelatives(sel,children=True)[0]
            self.proxyType = pm.objectType(self.proxyShape)

        #Set label:
        self.display_label.setText("Asset: "+self.proxy.name())
        #GET DSO
        asset_dso = self.proxy.dso.get()
        #GET ASSET INFOS
        self.asset_dir = Path(asset_dso).parents[4]
        self.ass_dir = Path(asset_dso).parents[2]

        dso_split = os.path.normpath(asset_dso).split(os.sep)
        self.current_variant = dso_split[-3]
        self.current_version = dso_split[-2]
        self.asset_name = dso_split[-6]

        #BUILD DIC
        self.asset_dic = utils.scan_ass_directory(self.ass_dir)

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


    def to_maya(self, standIn):
        dso = standIn.dso.get()
        maya_path = dso.replace(".ass",".ma")
        namespace_for_creation= utils.nameSpace_from_path(maya_path)
        refNode = pm.system.createReference(maya_path, namespace=namespace_for_creation)
        nodes = pm.FileReference.nodes(refNode)
        transform = standIn.getParent()
        parent = transform.getParent()
        if parent:
            pm.parent(nodes[0],parent)
        utils.match_matrix(nodes[0],transform)
        transform.visibility.set(False)

    def batch_convert(self, sel):
        standIn_list = []
        for s in sel:
            ass = s.getShape()
            if pm.objectType(ass) == "aiStandIn" :
                standIn_list.append(ass)
            elif pm.objectType(s) == "aiStandIn":
                standIn_list.append(s)
            elif pm.objectType(s.getParent().getShape()) == "aiStandIn":
                standIn_list.append(s.getParent().getShape())

        for ass in standIn_list:
            self.to_maya(ass)



    def convert_to_maya_clicked(self):
        sel = pm.ls(sl=True)
        self.batch_convert(sel)


    def switch_proxy_type_clicked(self):
        if self.proxyType == "mesh":
            self.convert_proxy_to_procedrual()
        if self.proxyType == "aiStandIn":
            self.convert_procedural_to_proxy()

    def convert_proxy_to_procedrual(self):
        if not self.isValid == True: utils.warning("Not a valid standIn")
        standInShape = pm.createNode("aiStandIn")
        standIn =standInShape.getParent()
        standInShape.dso.set(self.proxy.dso.get())
        pm.parent(standIn,self.proxy.getParent())
        pm.matchTransform(standIn,self.proxy)

        if pm.referenceQuery(self.proxy,isNodeReferenced=True):
            path = pm.referenceQuery(self.proxy, filename=True)
            ref_node = pm.FileReference(path)
            pm.FileReference.importContents(ref_node)

        utils.import_all_references(self.proxy)
        name = self.proxy.name()
        pm.delete(self.proxy)

        pm.rename(standIn,name)
        pm.rename(standInShape,name+"Shape")

    def convert_procedural_to_proxy(self):
        if not self.isValid == True: utils.warning("Not a valid standIn")
        proxy_dir = Path(self.proxy.dso.get()).parents[3]
        print(proxy_dir)
        proxy_path = utils.get_last_scene(proxy_dir, self.asset_name+"\.v*")
        if not proxy_path: utils.warning("No proxy path found to replace %s"%proxy_path)
        namespace = utils.nameSpace_from_path(proxy_path)
        refNode = pm.system.createReference(proxy_path, namespace=namespace)
        nodes = pm.FileReference.nodes(refNode)
        if self.proxy.getParent():
            pm.parent(nodes[0], self.proxy.getParent())
        utils.match_matrix(nodes[0],self.proxy)
        pm.delete(self.proxy)

    def maya_selection_changed_callback(self,*args):
        try:
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
