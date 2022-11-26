import maya.cmds as cmds
import os

import logging
logger = logging.getLogger('assTools')

logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# prevent logging from bubbling up to maya's logger
logger.propagate=0

# 'application' code

#logger.debug('debug message')
#logger.info('info message')
#logger.warning('warn message')
#logger.error('error message')
#logger.critical('critical message')


def write_ass(path=""):
    cmds.file(path,
              force=False,
              options="-shadowLinks 0;-mask 24;-lightLinks 0;-boundingBox;-fullPath",
              type="ASS Export",
              exportSelected=True)

def write_maya_scene(path):
    cmds.file(path,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)

def get_last_v(path):
    list = os.listdir(path)
    if not list: return "v001"
    v_list = [v for v in list if os.path.isdir(os.path.join(path,v)) and v.startswith("v")]
    v_list.sort()
    if v_list:
        return v_list[-1]
    else:
         return "v001"

def short_name(long_name):
    short_name = long_name.split("|")[-1]
    return short_name

def exportVariant(dir, asset, variant):

    #version = getVersion(variantDir, variantName)
    #select variant in maya
    cmds.select(variant.name_long)

    #Store visibility
    variant_visibility_state = cmds.getAttr(variant.name_long+".visibility")
    variantSet_visibitlity_state = cmds.getAttr(variant.vSet_name_long+".visibility")

    #Make visible
    cmds.setAttr(variant.name_long+".visibility",1)
    cmds.setAttr(variant.vSet_name_long+".visibility",1)

    variant_publish_dir = os.path.join(dir, asset.name, variant.dir)
    variant_publish_name = "%s_%s_%s"%(asset.name, variant.vSet_name, variant.name)
    variant_last_v = get_last_v(variant_publish_dir)
    variant_full_path = os.path.join(variant_publish_dir,variant_last_v,variant_publish_name)
    variant_maya_scene = variant_full_path+".ma"
    variant_maya_ass = variant_full_path+".ass"
    #Export ass
    print ("------EXPORT BEGGING-------")
    print ("-------- %s ---------"%(variant.name))
    write_ass(variant_maya_ass)
    write_maya_scene(variant_maya_scene)

    #Restore visibility_state
    cmds.setAttr(variant.name_long+".visibility",variant_visibility_state)
    cmds.setAttr(variant.vSet_name_long+".visibility",variantSet_visibitlity_state)

def printInfo(object):

    print("--- Infos ----")
    infos = vars(object)
    for i in infos.keys():
        print (i+": "+infos[i])
    print("")


class Variant():
    def __init__(self,variant_name, vSet_name, asset_name ):
        self.asset_name =  short_name(asset_name)
        self.vSet_name = short_name(vSet_name)
        self.vSet_name_long = short_name(vSet_name)
        self.name_long  = variant_name
        self.name = short_name(variant_name)
        self.dir = os.path.join(self.vSet_name,self.name)

class Asset():
    def __init__(self,maya_name):
        self.name = short_name(maya_name)
        self.name_long = maya_name


def scanAsset(obj):
    asset = Asset(obj)
    vSets = [vSet for vSet in cmds.listRelatives(obj, fullPath=True)
            if short_name(vSet).startswith("variant_") ]
    if not vSets:
        logger.warning('No variant set found !')
        return None, None

    for vSet in vSets:
        variants = [Variant(var, vSet, obj) for var in cmds.listRelatives(vSet, fullPath=True)]
    return asset, variants


    #exportVariant(dir, asset, variants)
