
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


assets_directory  = "D:/gabriel/assetizer/assets"

def match_matrix(source,target):
    m = cmds.xform(source, worldSpace = True, matrix=True, query=True)
    cmds.xform(target,  matrix=m)

def list_set_selected_byName(list,name):
    items = list.findItems(name,QtCore.Qt.MatchExactly)
    if len(items)>0:
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

def get_next_version(variant_dir):

    #Create the directory if needed
    os.makedirs(variant_dir,exist_ok=True)
    #List all version directory
    listDir = os.listdir(variant_dir)
    listDir.sort()

    #Keep only directory starting with a "V"
    for item in listDir:
        if not item.startswith("v"):
            listDir.remove(item)

    #If not version yet, return v001
    if len(listDir) == 0:
        next_version = "v001"
        return next_version

    last_version = listDir[-1] #Get last version
    last_version_number = int(last_version.split("v")[-1]) #v001 --> 1 (int)
    next_version_number = last_version_number + 1 # 1 --> 2
    next_version = "v" + str(next_version_number).zfill(3) # 2 --> v002
    return next_version

def write_ass(path=""):
    cmds.file(path,
              force=False,
              options="-shadowLinks 0;-mask 24;-lightLinks 0;-boundingBox;-fullPath",
              type="ASS Export",
              exportSelected=True)

def write_maya_scene(path):
    cmds.file(path,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)

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
        self.variantSet_Qlist = QtWidgets.QListWidget()
        self.variant_Qlist = QtWidgets.QListWidget()
        self.version_Qlist = QtWidgets.QListWidget()
        self.version_Qlist.setVisible(False)

        #WIDGET CHECKBOX
        self.use_latest =  QtWidgets.QCheckBox("Use latest version")
        self.use_latest.setChecked(True)


        self.display_label = QtWidgets.QLabel("Asset:")
        self.push_edit_button = QtWidgets.QPushButton("Push edit")
        self.convert_to_maya = QtWidgets.QPushButton("Convert to maya")
        self.set_version = QtWidgets.QPushButton("Set version")

        # ADD WIDGET TO LAYOUT

        self.comboLayout.addWidget(self.variantSet_Qlist)
        self.comboLayout.addWidget(self.variant_Qlist)
        self.comboLayout.addWidget(self.version_Qlist)

        self.button_layout.addWidget(self.use_latest)
        self.button_layout.addWidget(self.display_label)
        self.button_layout.addWidget(self.push_edit_button)
        self.button_layout.addWidget(self.set_version)
        self.button_layout.addWidget(self.convert_to_maya)

        self.mainLayout.addLayout(self.comboLayout)
        self.mainLayout.addLayout(self.button_layout)


        #CONNECT WIDGET
        self.push_edit_button.clicked.connect(self.push_edit_clicked)
        self.set_version.clicked.connect(self.set_version_clicked)
        self.convert_to_maya.clicked.connect(self.convert_to_maya_clicked)
        self.variantSet_Qlist.itemClicked.connect(self.variantSet_Qlist_changed)
        self.variant_Qlist.itemClicked.connect(self.variant_Qlist_changed)
        self.use_latest.stateChanged.connect(self.use_latest_changed)

        self.load_asset_clicked()

    def checkAsset(self):
        check = True
        error_msg = ""
        if len(cmds.ls(selection=True)) == 0:
            error_msg += "No selection"
            check = False
        try:
            asset_dso = cmds.getAttr(self.maya_proxy_name+".dso")
            if cmds.getAttr(self.maya_proxy_name+".ai_translator") != "procedural":
                error_msg += "Not a procedural" + cmds.getAttr(self.maya_proxy_name+".ai_translator")
                check = False
        except:
            error_msg += "No dso"
            check = False



        return check, error_msg


    def load_asset_clicked(self):
        #GET PROXY NAME FROM MAYA SELECTION
        if len(cmds.ls(selection=True)) >0:
            self.maya_proxy_name = cmds.ls(selection=True)[0]
        else:
            return
        check, error_msg = self.checkAsset()

        if check == False:
            self.display_label.setText("Not a standin")
            print(error_msg)
            return



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
        self.use_latest_changed()

        #Set list selection from current item
        list_set_selected_byName(self.variantSet_Qlist,self.current_variantSet)
        list_set_selected_byName(self.variant_Qlist,self.current_variant)
        list_set_selected_byName(self.version_Qlist,self.current_version)


    ###USE LASTEST CHANGED ####
    def use_latest_changed(self):
        state = self.use_latest.isChecked()
        if state == True:
            self.version_Qlist.setVisible(False)
            pass
        else:
            self.version_Qlist.setVisible(True)
            pass
    ### QLIST CHANGED ###
    # ON VARIANT_SET CHANGE
    def variantSet_Qlist_changed(self):
        self.current_variantSet = self.variantSet_Qlist.currentItem().text()
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
        #☻match_matrix(node[0],self.maya_proxy_name)
        #Hide and rename proxy "TO_DELETE"
        cmds.setAttr(self.maya_proxy_name+".visibility",0)
        cmds.rename(self.maya_proxy_name,self.maya_proxy_name+"_TO_DELETE")

    def push_edit_clicked(self):
        #Get maya selection
        maya_sel = cmds.ls(selection=True)[0]

        if  cmds.listRelatives( maya_sel, parent=True ) is not None:
            cmds.warning("Select the top parent of the asset.")
            return

        #PAUSE CALLBACK
        #OpenMaya.MMessage.removeCallback(self.selection_changed_callback)
        #Get namescape
        ns = cmds.referenceQuery(maya_sel, namespace=True, shortName=True)
        full_namespace = cmds.referenceQuery(maya_sel, namespace=True)
        reference_node = cmds.referenceQuery(maya_sel,filename=True)

        #Get asset name , variant set name  and variant name
        asset_full_name = ns if not ns[-1].isdigit() else ns.rstrip(ns[-1])

        #Query the user and ask for asset name, variant set name, and variant name
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
            'Name:',QtWidgets.QLineEdit.Normal,text=asset_full_name)

        if ok:
            asset_name = str(text).split("_")[0]
            variantSet_name = str(text).split("_")[1]
            variant = str(text).split("_")[2]
        else:
            print("Abort by user")
            return

        # Build directories
        variantSet_dir = os.path.join(assets_directory,asset_name,"publish","ass",variantSet_name)
        variant_dir = os.path.join(variantSet_dir,variant)
        next_version = get_next_version(variant_dir)
        variant_with_version_dir = os.path.join(variant_dir,next_version)

        #Build paths
        name = "%s_%s_%s"%(asset_name,variantSet_name,variant)
        ass_path = os.path.join(variant_with_version_dir, name+".ass")
        maya_scene_path = os.path.join(variant_with_version_dir,name + ".ma")

        #### MAYA SHADING SCENE (with version awardness)
        maya_shading_scene_dir = os.path.join(os.path.join(assets_directory,asset_name,"shading"))
        maya_shading_scene_name = "%s_shading_%s_%s"%(asset_name,variantSet_name, variant)
        os.makedirs(maya_shading_scene_dir,exist_ok=True)

        #Return a list of files matching the rules:
        #   --- starts with "variantSetName_shading"
        #   --- at least two "." in the filename
        list = [f for f in os.listdir(maya_shading_scene_dir) if f.startswith(maya_shading_scene_name) and len(f.split("."))>=2]
        #Version parsing
        versions =[]
        for f in list:
            version = f.split(".")[-2]
            if version.isdigit(): versions.append(version)
        versions.sort()
        last_version = int(versions[-1])+1 if len(versions)>0 else 1
        maya_shading_scene_with_version = maya_shading_scene_name +"."+ str(last_version).zfill(4) + ".ma"
        maya_shading_scene_path = os.path.join(maya_shading_scene_dir,maya_shading_scene_with_version )
        ### END  MAYA SHADING SCENE

        #Create a temp group (hack to preserve object name when removing namespace)
        tmp_grp = cmds.group( maya_sel , n='tmp_grp')
        cmds.file(reference_node, importReference=True)
        cmds.namespace(removeNamespace=full_namespace, mergeNamespaceWithRoot=True)
        childs = cmds.listRelatives(tmp_grp, fullPath=True)
        variant_maya_sel = cmds.parent(childs, world=True)

        #Reset transform
        cmds.move(0, 0, 0, ls=True)
        cmds.rotate(0, 0, 0)
        cmds.scale(1, 1, 1)

        #Write ass and ma
        print ("------- Start pushing ! --------")
        write_ass(ass_path)
        print("Writing: %s"%maya_scene_path)
        write_maya_scene(maya_scene_path)
        print("Writing: %s"%maya_shading_scene_path)
        write_maya_scene(maya_shading_scene_path)
        print ("-------- Success pushed ! --------")

        #Clean up
        cmds.delete(tmp_grp)
        cmds.delete(variant_maya_sel)


        #TO DO: CLEAN SHADER AFTER DELETION
        #IMPORT PROXY
        #SAVE VARIANT SHADING SCENE
        #SAVE AS NEW VARIANT
        #CALL BACK
        #OFFSET PB

        #ADD CALLBACK AGAIN
        #self.selection_changed_callback = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.maya_selection_changed_callback)



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
