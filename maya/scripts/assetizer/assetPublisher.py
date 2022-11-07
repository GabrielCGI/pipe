import maya.cmds as cmds
import os
import sys

# UTILITY FUNCTION
def write_ass(path=""):
    cmds.file(path,
              force=False,
              options="-shadowLinks 0;-mask 24;-lightLinks 0;-boundingBox;-fullPath",
              type="ASS Export",
              exportSelected=True)

# EXPORT FUNCTION
def exportVariant(ass_directory, assetName, variantSet, variant):
    variant_basename = variant.split("|")[-1] # ex: "toy_default|HIGH" --> "HIGH"
    variantName = variantSet + "_" + variant_basename + ".ass" #ex: "HIGH" --> "toy_default_HIGH.ass"
    variantPath = os.path.join(ass_directory,variantSet,variantName)

    #select variant in maya
    cmds.select(variant)

    #Store visibility
    variant_visibility_state = cmds.getAttr(variant+".visibility")
    variantSet_visibitlity_state = cmds.getAttr(variantSet+".visibility")

    #Make visible
    cmds.setAttr(variant+".visibility",1)
    cmds.setAttr(variantSet+".visibility",1)

    #Export ass
    print ("-------- %s ---------"%(variant))
    write_ass(variantPath)

    #Restore visibility_state
    cmds.setAttr(variant+".visibility",variant_visibility_state)
    cmds.setAttr(variantSet+".visibility",variantSet_visibitlity_state)

def make_proxy_scene(asset):
    #Init name

    proxy = "PROXY"
    asset_proxy = asset.name+"_proxy"

    #Visibility
    visibility_state = cmds.getAttr(proxy+".visibility")
    cmds.setAttr(proxy+".visibility",1)

    #Arnold attribut
    cmds.setAttr(proxy+".ai_translator",  "procedural", type="string")
    default_ass_path = os.path.join(asset.ass_directory,  asset.name+"_default", asset.name+"_default_HIGH.ass")
    cmds.setAttr(proxy+".dso",default_ass_path,type="string")
    cmds.setAttr(proxy+".aiOverrideShaders",0)
    cmds.setAttr(proxy+".aiOverrideMatte",1)




    #rename proxy group before export
    cmds.rename(proxy,asset_proxy)
    cmds.select(asset_proxy )
    cmds.file(asset.lib_name,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)

    #Restore properties
    cmds.rename(asset_proxy , proxy)
    cmds.setAttr(proxy+".ai_translator",  "polymesh", type="string")
    cmds.setAttr(proxy+".visibility",visibility_state)

class Asset():
    def __init__(self):
        self.maya_scene = cmds.file(q=True, sn=True)
        self.name =  os.path.basename(self.maya_scene).split("_")[0] # ex: "../assets/shading/toy_shading.002.ma" --> "toy"
        self.directory =  os.path.dirname(os.path.dirname(self.maya_scene))
        self.lib_name = os.path.join(self.directory, "lib",self.name+".v001")
        self.ass_directory = os.path.join(self.directory,"lib","ass")
        self.variantSets = self.scan_scene_variantSets()

    def scan_scene_variantSets(self):
        variantSets = [i for i in cmds.ls(assemblies=True) if i.split("_")[0] == self.name and len(i.split("_"))== 2]
        return variantSets

def checkScene(asset):
    error_report = None
    error_message = ""
    #Test if an object PROXY exist

    if not cmds.objExists('PROXY'):
        error_report = True
        error_message  += "PROXY object missing"

    if len(asset.variantSets) == 0:
        error_report = True
        error_message  += "NO variantSet found. Check naming (case sensitve)"

    if asset.name+"_default" not in asset.variantSets:
        error_report = True
        error_message  += "default variant set not found"

    if error_report is not None:
        cmds.warning("Something went wrong... " + error_message)

    return error_report

def run ():

    #Init asset
    asset= Asset()
    error_report = checkScene(asset)
    if error_report is not None:
        return

    #List variantSet children to find variant then export
    for variantSet in asset.variantSets:
        variants = cmds.listRelatives(variantSet, path=True)
        for variant in variants:
            exportVariant(asset.ass_directory, asset.name, variantSet, variant)

    make_proxy_scene(asset)
