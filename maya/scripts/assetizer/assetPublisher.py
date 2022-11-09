import maya.cmds as cmds
import os
import sys
import inspect

# UTILITY FUNCTION
def write_ass(path=""):
    cmds.file(path,
              force=False,
              options="-shadowLinks 0;-mask 24;-lightLinks 0;-boundingBox;-fullPath",
              type="ASS Export",
              exportSelected=True)

def write_maya_scene(path):
    cmds.file(path,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)

def getVersion(variantDir, variantName):
    pass

# EXPORT FUNCTION
def exportVariant(variant, variantSet):


    #version = getVersion(variantDir, variantName)


    #select variant in maya
    cmds.select(variant.maya_name)

    #Store visibility
    variant_visibility_state = cmds.getAttr(variant.maya_name+".visibility")
    variantSet_visibitlity_state = cmds.getAttr(variantSet.maya_name+".visibility")

    #Make visible
    cmds.setAttr(variant.maya_name+".visibility",1)
    cmds.setAttr(variantSet.maya_name+".visibility",1)

    #Export ass
    print ("------EXPORT BEGGING-------")
    print ("-------- %s ---------"%(variant.name))
    write_ass(variant.ass_full_path)
    write_maya_scene(variant.variant_maya_scene_path)

    #Restore visibility_state
    cmds.setAttr(variant.maya_name+".visibility",variant_visibility_state)
    cmds.setAttr(variantSet.maya_name+".visibility",variantSet_visibitlity_state)

def make_proxy_scene(asset):
    #Init name

    proxy = "PROXY"
    asset_proxy = asset.name+"_proxy"

    #Visibility
    visibility_state = cmds.getAttr(proxy+".visibility")
    cmds.setAttr(proxy+".visibility",1)

    #Arnold attribut
    cmds.setAttr(proxy+".ai_translator",  "procedural", type="string")
    default_ass_path = asset.last_default_variant_ass_path
    cmds.setAttr(proxy+".dso",default_ass_path,type="string")
    cmds.setAttr(proxy+".aiOverrideShaders",0)
    cmds.setAttr(proxy+".aiOverrideMatte",1)

    #rename proxy group before export
    cmds.rename(proxy,asset_proxy)
    cmds.select(asset_proxy )
    cmds.file(asset.publish_maye_scene,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)

    #Restore properties
    cmds.rename(asset_proxy , proxy)
    cmds.setAttr(proxy+".ai_translator",  "polymesh", type="string")
    cmds.setAttr(proxy+".visibility",visibility_state)

class Asset():
    def __init__(self):
        self.maya_scene = cmds.file(q=True, sn=True)
        self.name =  os.path.basename(self.maya_scene).split("_")[0] # ex: "../assets/shading/toy_shading.002.ma" --> "toy"
        self.directory =  os.path.dirname(os.path.dirname(self.maya_scene))
        self.publish_directory =  os.path.join(self.directory, "publish")
        self.publish_maye_scene = self.get_next_maya_publish_scene()
        self.ass_directory = os.path.join(self.directory,"publish","ass")
        self.variantSets = self.scan_scene_variantSets()
        self.last_default_variant_ass_path = self.get_last_default_variant_ass_path()

    def scan_scene_variantSets(self):
        variantSets = [VariantSet(i, self.ass_directory, self.name ) for i in cmds.ls(assemblies=True) if i.split("_")[0] == "variant" and len(i.split("_"))== 2]
        return variantSets

    def get_last_default_variant_ass_path(self):
        last_default_variant_ass_path = None
        for variantSet in self.variantSets:
            if variantSet.name == "basic":
                for variant in variantSet.variants:
                    if variant.name == "HD":
                        last_default_variant_ass_path =  variant.ass_full_path
        return last_default_variant_ass_path


    def printInfo(self):
        attrs = vars(self)
        print("---- Asset %s infos ---"%(self.name))
        for attr in attrs:
            if str(attr)=="variantSets":
                print("VariantSet list:")
                for a in attrs[attr]:
                    print("__ " + a.name)
                    for variant in a.variants:
                        print ("___ "+ variant.name + " ("+variant.next_version+")")


            else:
                print (attr +" : " + str(attrs[attr]))

    def export_all_Variant(self):
        for variantSet in self.variantSets:
            for variant in variantSet.variants:
                exportVariant(variant, variantSet)

    def  get_next_maya_publish_scene(self):
        list=[] #init empty list
        os.makedirs(self.publish_directory, exist_ok = True)
        raw_list = os.listdir(self.publish_directory) #list all file and directory
        raw_list.sort()
        #Keep only file mathcing the pattern  toy.v001.ma
        for item in raw_list:
            if len(item.split(".")) == 3:
                if item.split(".")[-2].startswith("v"):
                    list.append(item)
        list.sort()
        if len(list) == 0:
            lastest_version = "temp.v000.ma"
        else:
            lastest_version = list[-1]
        latest_version_number = int(lastest_version.split(".")[-2].split("v")[-1]) #toy.v001.ma --> 001 (int)
        next_version_number = latest_version_number +1
        next_publish_name = self.name+".v"+str(next_version_number).zfill(3)+".ma"
        next_maya_publish_scene=os.path.join(self.publish_directory, next_publish_name )
        return next_maya_publish_scene

class VariantSet():
    def __init__(self, name, ass_directory, asset_name):
        self.asset_name = asset_name
        self.maya_name = name #ex: variant_basic --> basic
        self.name= name.split("_")[-1]
        self.directory = os.path.join(ass_directory,self.name)
        self.variants = self.getVariants()

    def getVariants(self):
        variants = [Variant(maya_name , self.directory, self.name, self.asset_name) for maya_name in cmds.listRelatives(self.maya_name, path=True)]
        return variants
        pass

class Variant():
    def __init__(self, maya_name, variantSet_directory, variantSet_name, asset_name):
        self.maya_name = maya_name # ex: variant_basic|HD
        self.name = maya_name.split("|")[-1] # ex: HD
        self.asset_name = asset_name
        self.variantSet_name =  variantSet_name
        self.fullname = "%s_%s_%s"%(self.asset_name, self.variantSet_name, self.name) #ex: toy_basic_HD
        self.variantSet_directory = variantSet_directory
        self.next_version = self.get_next_version()
        self.ass_full_path = os.path.join(self.variantSet_directory, self.name, self.next_version,self.fullname +".ass")
        self.variant_maya_scene_path =  os.path.join(self.variantSet_directory,self.name, self.next_version, self.fullname +".ma")

    def get_next_version(self):
        #Variant_directory path ...\ass\toy_default\ --> ...\ass\toy_default\HIGH
        variant_directory = os.path.join(self.variantSet_directory,self.name) #
        #Create the directory if needed
        os.makedirs(variant_directory,exist_ok=True)
        #List all version directory
        listDir = os.listdir(variant_directory)
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

    variantNameList = [variantSet.name for variantSet in asset.variantSets]

    if "basic" not in variantNameList:
        error_report = True
        error_message  += "variant: 'basic' not found in the current maya scene"

    if error_report is not None:
        cmds.warning("Something went wrong... " + error_message)

    return error_report

def assetPrint():
    asset= Asset()
    asset.printInfo()
    error_report = checkScene(asset)
def run ():
    #Init asset
    asset= Asset()
    asset.printInfo()
    error_report = checkScene(asset)
    if error_report is not None:
        return

    #List variantSet children to find variant then export
    asset.export_all_Variant()

    make_proxy_scene(asset)
