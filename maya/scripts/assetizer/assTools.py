import maya.cmds as cmds
import os

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)
zero_matrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]

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
    logger.debug('Get last v: %s'%v_list)
    if v_list:
        new_v = int(v_list[-1].split("v")[-1])+1
        new_v_str = "v"+str(new_v).zfill(3)
        logger.debug('New v: %s'%new_v_str)
        return new_v_str
    else:
         return "v001"

def get_next_publish_scene(dir, asset_name):
    list=[] #init empty list
    if not is_dir_exist(dir): return
    raw_list = os.listdir(dir) #list all file and directory
    raw_list.sort()
    #Keep only file mathcing the pattern  toy.v001.ma
    for item in raw_list:
        split = item.split(".")
        if len(split) == 3:
            if split[-2].startswith("v"):
                if split[0] == asset_name:
                    list.append(item)
    list.sort()
    if len(list) == 0:
        lastest_version = "temp.v000.ma"
    else:
        lastest_version = list[-1]
    latest_version_number = int(lastest_version.split(".")[-2].split("v")[-1]) #toy.v001.ma --> 001 (int)
    next_version_number = latest_version_number +1
    next_publish_name =  asset_name+".v"+str(next_version_number).zfill(3)+".ma"
    next_maya_publish_scene=os.path.join(dir, next_publish_name )
    return next_maya_publish_scene

def short_name(long_name):
    short_name = long_name.split("|")[-1]
    return short_name

def is_dir_exist(path):
    if not os.path.isdir(path):
        msg = cmds.confirmDialog( title='Confirm',message='The directory does not exist.\n%s'%(path),
        button=['Create','Cancel'], defaultButton='Cancel', cancelButton='Cancel', dismissString='Cancel')
        if msg == "Create":
            os.makedirs(path, exist_ok = True)
            logger.info('Directory created: %s'%path)
            return True
        else:
            logger.info('Abort directory creation: %s'%path)
            return False
    else:
        logger.debug('Check directory existence success: %s '%path)
        return True

def exportVariant(dir, asset, variant, export_shading_scene = False):
    cmds.select(variant.name_long)


    #Store visibility
    variant_visibility_state = cmds.getAttr(variant.name_long+".visibility")
    variantSet_visibitlity_state = cmds.getAttr(variant.vSet_name_long+".visibility")
    logger.debug('Store visibility success')
    #Make visible
    cmds.setAttr(variant.name_long+".visibility",1)
    cmds.setAttr(variant.vSet_name_long+".visibility",1)

    asset_publish_dir = os.path.join(dir, asset.name)
    if not is_dir_exist(asset_publish_dir): return
    variant_publish_dir = os.path.join(asset_publish_dir,"publish", "ass", variant.dir)
    if not is_dir_exist(variant_publish_dir): return
    variant_publish_name = "%s_%s_%s"%(asset.name, variant.vSet_name, variant.name)
    variant_last_v = get_last_v(variant_publish_dir)
    variant_full_path = os.path.join(variant_publish_dir,variant_last_v,variant_publish_name)
    variant_maya_scene = variant_full_path+".ma"
    variant_maya_ass = variant_full_path+".ass"
    if export_shading_scene:
        shading_scene_dir = os.path.join(asset_publish_dir,"shading")
        if not is_dir_exist(shading_scene_dir): return
        variant_shading_scene_name= "%s_%s_%s_shading"%(asset.name, variant.vSet_name, variant.name)
        variant_shading_scene = get_next_publish_scene(shading_scene_dir, variant_shading_scene_name)
    #Export ass

    logger.info("--------Start export %s %s ---------"%(variant.vSet_name, variant.name))
    write_ass(variant_maya_ass)
    write_maya_scene(variant_maya_scene)
    if export_shading_scene:
        write_maya_scene(variant_shading_scene)
    logger.info("Maya scene export succes: %s"%variant_maya_scene)
    #Restore visibility_state
    cmds.setAttr(variant.name_long+".visibility",variant_visibility_state)
    cmds.setAttr(variant.vSet_name_long+".visibility",variantSet_visibitlity_state)

def printInfo(object):

    logger.debug("--- Object Infos ----")
    infos = vars(object)
    for i in infos.keys():
        logger.debug(i+": "+infos[i])
    logger.debug("--- Object Infos End ----")

class Variant():
    def __init__(self,variant_name, vSet_name, asset_name ):
        self.asset_name =  short_name(asset_name)
        self.vSet_name = short_name(vSet_name).split("variant_")[-1]
        self.vSet_name_long = vSet_name
        self.name_long  = variant_name
        self.name = short_name(variant_name)
        self.dir = os.path.join(self.vSet_name,self.name)

class Asset():
    def __init__(self,maya_name):
        self.name = short_name(maya_name)
        self.name_long = maya_name


def build_dic_variantSet(ass_dir):

    dic_variantSet={}
    variantSets = os.listdir(ass_dir)

    for variantSet in variantSets:
        variantSetDir = os.path.join(ass_dir,variantSet)
        variants = os.listdir(variantSetDir)
        dic_variant={}
        for variant in variants:

            variantDir = os.path.join(variantSetDir,variant)
            versions = os.listdir(variantDir)
            dic_variant[variant]=versions
        dic_variantSet[variantSet]=dic_variant
    logger.debug("-- Build dic variant set result --")
    logger.debug(dic_variantSet)
    return dic_variantSet

def has_transfrom(obj):


    if cmds.xform(obj,query=True, matrix=True) != zero_matrix:
        logger.error('Transfroms applied on %s -> Plz fix manually'%obj)
        return True
    else:
        return False

def cleanAssetBeforeExport(obj):
    if not obj:
        logger.error('Need to have an obj to clean!')
        return None
    #CHECK IF VARIANT SETS EXIST
    logger.debug('cleanning... is there a variant set ?')
    vSets = [vSet for vSet in cmds.listRelatives(obj, fullPath=True)
            if short_name(vSet).startswith("variant_") ]
    if not vSets:
        logger.error('No variant set found !')
        return None
    logger.debug("variants set found: %s"%vSets)
    variants=[]
    logger.debug('cleanning... is there variant ?')
    #CHECK IF VARIANTS SET AND VARIANTS TRANSFROMS = 0
    for vSet in vSets:
        if has_transfrom(vSet): return None
        variants += [v for v in cmds.listRelatives(vSet, fullPath=True)]
    for v in variants:
        if has_transfrom(v): return None
    logger.debug("variants  found: %s"%variants)
    #CHECK IF PARENT IS WORLD
    if cmds.listRelatives(obj,parent=True ) is not None:
        logger.info('Reparenting to world %s'%obj)
        obj = cmds.parent(obj, world=True )[0]

    #CHECK IF ASSET TRANSFORMS == 0
    if cmds.xform(obj,query=True, matrix=True) != zero_matrix:
        msg = ("The asset has transfrom information.\n"
               "The asset should be exported from the center of the world \n"
               )
        result = cmds.confirmDialog( title='Confirm',message=msg,
        button=['Reset transforms','Freeze transforms', "Cancel"],
        defaultButton='Reset transforms', cancelButton='Cancel', dismissString='Cancel')
        if result == "Reset transforms":
            cmds.move(0, 0, 0, ls=True)
            cmds.rotate(0, 0, 0)
            cmds.scale(1, 1, 1)
        if result == "Freeze transforms":
            cmds.makeIdentity(obj,apply=True )
    return obj

def scanAsset(obj):
    variants =[]
    asset = Asset(obj)
    vSets = [vSet for vSet in cmds.listRelatives(obj, fullPath=True)
            if short_name(vSet).startswith("variant_") ]

    if not vSets:
        logger.error('No variant set found !')
        return None, None
    for vSet in vSets:
        variants += [Variant(var, vSet, obj) for var in cmds.listRelatives(vSet, fullPath=True)]

    if not variants:
        logger.error('No variants found !')
        return None, None
    logger.info('Scan success !')
    return asset, variants

def get_last_basic_variant_ass(ass_dir):
    dic = build_dic_variantSet(ass_dir)
    ass_path = None
    if "variant_basic" in dic.keys():
        if "HD" in dic["variant_basic"].keys():

            vSet = "variant_basic"
            variant = "HD"
            last = dic["variant_basic"]["HD"][-1]
        else:
            vSet = "variant_basic"
            variant = list(dic[vSet].keys())[0]
            last = dic["variant_basic"][variant][-1]
    else:
        vSet  = list(dic.keys())[0]
        variant = list(dic[vSet].keys())[0]
        last =   dic[vSet][variant][-1]
    ass_path = os.path.join(ass_dir,vSet,variant,last,"%s_%s_%s.ass"%(vSet,variant,last))
    return ass_path

def get_from_asset(asset_name_long, pattern):

    obj = asset_name_long+"|"+pattern
    logger.debug('Looking for... %s !' %obj)

    if cmds.objExists(obj):
        logger.debug('Found %s !' %obj)
        return obj
    else:
        logger.debug('Not Found %s !' %obj)
        return None

def make_proxy_scene(asset_name,dir,proxy, sub_assets=None):
    #Init name

    #Visibility
    visibility_state = cmds.getAttr(proxy+".visibility")
    cmds.setAttr(proxy+".visibility",1)

    #Arnold attribut
    cmds.setAttr(proxy+".ai_translator",  "procedural", type="string")
    ass_dir = os.path.join(dir,asset_name,"publish","ass")
    ass_path =  get_last_basic_variant_ass(ass_dir)
    logger.debug("get_last_basic_variant_ass() = %s"%ass_path)
    cmds.setAttr(proxy+".dso",ass_path,type="string")
    cmds.setAttr(proxy+".aiOverrideShaders",0)
    cmds.setAttr(proxy+".aiOverrideMatte",1)
    cmds.makeIdentity(proxy, apply=True, t=1, r=1, s=1, n=2 )
    #rename proxy group before export


    publish_proxy_scene_dir = os.path.join(dir,asset_name)
    next_publish_proxy_scene= get_next_publish_scene(publish_proxy_scene_dir, asset_name)
    logger.info("Next publish proxy maya scene  = %s"%next_publish_proxy_scene)

    cmds.select(proxy)
    if sub_assets:
        cmds.select(sub_assets,add=True,)
    cmds.file(next_publish_proxy_scene,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)
    logger.info('Proxy export success %s!'%next_publish_proxy_scene)
    #Restore properties

    cmds.setAttr(proxy+".ai_translator",  "polymesh", type="string")
    cmds.setAttr(proxy+".visibility",visibility_state)
