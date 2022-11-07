
"""
import sys
sys.path.append("D:/gabriel/assetizer/scripts")

import assetPublisher
import importlib
importlib.reload(assetPublisher)

"""
import maya.cmds as cmds
import os


def get_asset_dirs():
    maya_scene_path = cmds.file(q=True, sn=True)
    asset_directory = os.path.dirname( os.path.dirname (maya_scene_path ))
    lib_directory =  os.path.join(asset_directory,"lib")
    ass_directory = os.path.join(lib_directory,"ass")
    return asset_directory, lib_directory, ass_directory

def get_asset_name_from_scene():
    maya_scene_path = cmds.file(q=True, sn=True)
    asset_name = os.path.basename(maya_scene_path).split("_")[0]
    return asset_name

def write_ass(path=""):
    cmds.file(path,
              force=False,
              options="-shadowLinks 0;-mask 24;-lightLinks 0;-boundingBox;-fullPath",
              type="ASS Export",
              exportSelected=True)

class asset():
    def __init__(self):
        asset_directory, lib_directory, ass_directory = get_asset_dirs()
        self.name = get_asset_name_from_scene()
        self.asset_directory = asset_directory
        self.ass_directory = ass_directory
        self.lib_directory = lib_directory
        self.lib_name = os.path.join(lib_directory,self.name+"_v001.ma")
        self.variant_list = self.get_variant_list()

    def get_variant_list(self):
        #Scan the scene and return a list of variant
        #Naming convention: assetName_variantName
        variant_list = []
        all_maya_root_transform = cmds.ls(assemblies=True)
        for node in all_maya_root_transform:
            try:
                split_node = node.split("_")
                if len(split_node) == 2 and split_node[0] == self.name:
                    variant_list.append(node)
            except Exception as e:
                print(e.message, e.args)
        return variant_list



class LOD():
    def __init__(self,asset_name, variant_name, lod_maya_path):
        self.asset_name = asset_name
        self.variant_name = variant_name
        self.lod_maya_path =  lod_maya_path
        self.lod_name = lod_maya_path.split("|")[-1]

        self.ass_name =  "%s_%s.ass "%(self.variant_name,self.lod_name) #assName_High.ass
        self.ass_path = os.path.join(asset.ass_directory, self.variant_name, self.ass_name)

    def export_to_ass(self):
        cmds.select(self.lod_maya_path)
        visibility_state = cmds.getAttr(self.lod_maya_path+".visibility")
        cmds.setAttr(self.lod_maya_path+".visibility",1)
        cmds.setAttr(self.lod_maya_path+".aiOverrideShaders",0)

        print("START EXPORING:" + self.ass_path)

        write_ass(self.ass_path)
        cmds.setAttr(self.lod_maya_path+".visibility",visibility_state)


asset = asset()
for variant in asset.variant_list:
    lod_list = cmds.listRelatives(variant, path=True)
    for lod in lod_list:
        print(variant)
        print(lod)
        class_lod = LOD(asset.name, variant, lod)
        class_lod.export_to_ass()


def make_proxy_scene():
    proxy = "PROXY"
    asset_proxy = asset.name+"_proxy"
    visibility_state = cmds.getAttr(proxy+".visibility")
    cmds.setAttr(proxy+".visibility",1)


    cmds.setAttr(proxy+".ai_translator",  "procedural", type="string")
    #TO DO: CLEAN deafault_ass_path
    default_ass_path = os.path.join(asset.ass_directory,  asset.name+"_default", asset.name+"_default_HIGH.ass")
    cmds.setAttr(proxy+".dso",default_ass_path,type="string")


    #Lock Proxy
    attrList = [".tx", ".ty", ".tz",".rx", ".ry", ".rz",".sx", ".sy", ".sz"]
    for attr in attrList: cmds.setAttr(proxy+attr,lock=True)

    #rename proxy group before export
    cmds.rename(proxy,asset_proxy)
    cmds.select(asset_proxy )
    cmds.file(asset.lib_name,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)
    cmds.rename(asset_proxy , proxy)
    cmds.setAttr(proxy+".ai_translator",  "polymesh", type="string")

    #DELETE standIn
    cmds.setAttr(proxy+".visibility",visibility_state)

make_proxy_scene()
