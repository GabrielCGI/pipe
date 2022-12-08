import maya.cmds as cmds
import pymel.core as pm
import os
import utils_pymel as utils
import importlib
importlib.reload(utils)
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    has_unknown_nodes = False
    unkown_nodes = pm.ls(type="unknown")
    if len(unkown_nodes)>0:
        logger.info("Unknown nodes found. Trying to delete")
        try:
            pm.delete(unkown_nodes)
            logger.info("Unknown nodes deleted.")
        except:
            logger.info("Can't delete unknown node")
            logger.info(unkown_nodes)
            has_unknown_nodes = True
            
    if has_unknown_nodes:
        filename, extension = os.path.splitext(path)
        scene_file, scene_extention = os.path.splitext(pm.system.sceneName())
        if extension != scene_extention:
            path = filename+scene_extention
            logger.info("Changing scene extention to prevent maya refusing to save because of unknown nodes")
        else:
            logger.info("Unknown nodes present, but no need to change the scene format")

    pm.system.exportSelected(path, force=False)

    #cmds.file(path,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)

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

def warning(txt):
    cmds.confirmDialog(message= txt)
    cmds.error(txt)

def ask_save():
    fileCheckState = pm.system.isModified()
    scene_file = pm.system.sceneName()
    if not scene_file:
        utils.warning("Save the scene before!")

    if fileCheckState:
        result = pm.confirmDialog( title='Save ?',
                            message='Do you want to save?',
                            button=['Yes','Skip',"Cancel"],
                            defaultButton='Yes',
                            cancelButton='"Cancel',
                            dismissString='"Cancel' )
        if result == "Yes":
            pm.saveFile()

        if result == "Cancel":
            warning("Abort by user")

def short_name(long_name):
    logger.debug('Trying to shorten name %s'%long_name)
    short_name_withnamespace = long_name.split("|")[-1]
    short_name = short_name_withnamespace.split(":")[-1]
    logger.debug('Succes %s -> %s'%(long_name,short_name))
    return short_name

def is_dir_exist(path):
    path = path.replace("\\","/")
    if not os.path.isdir(path):
        msg = pm.confirmDialog( title='Confirm',message='The directory does not exist.\n%s'%(path),
        button=['Create','Cancel'], defaultButton='Cancel', cancelButton='Cancel', dismissString='Cancel')
        if msg == "Create":
            os.makedirs(path, exist_ok = True)
            logger.info('Directory created: %s'%path)
            return True
        else:
            logger.info('Abort directory creation: %s'%path)
            raise
            return False
    else:
        logger.debug('Check directory existence success: %s '%path)
        return True

def exportVariant(asset, variant, assets_dir, export_shading=False):
    log = ""
    asset_name = utils.only_name(asset)
    variant_name = utils.only_name(variant)
    mb_state = pm.getAttr("defaultArnoldRenderOptions.motion_blur_enable")
    if mb_state == 1:
        pm.setAttr("defaultArnoldRenderOptions.motion_blur_enable",0)

    #Store visibility
    variant_visibility_state = variant.visibility.get()

    #Make visible
    if not variant_visibility_state:
        variant.visibility.set(True)

    asset_publish_dir = os.path.join(assets_dir, asset_name )
    is_dir_exist(asset_publish_dir)
    variant_publish_dir = os.path.join(asset_publish_dir,"publish", "ass",variant_name)
    is_dir_exist(variant_publish_dir)
    variant_last_v = get_last_v(variant_publish_dir)

    variant_full_path = os.path.join(variant_publish_dir,variant_last_v,variant_name)
    variant_maya_scene = variant_full_path+".ma"
    variant_maya_ass = variant_full_path+".ass"
    if export_shading:
        shading_scene_dir = os.path.join(asset_publish_dir,"shading")
        is_dir_exist(shading_scene_dir)
        variant_shading_scene_name= "%s_shading"%(variant_name)
        variant_shading_scene = get_next_publish_scene(shading_scene_dir, variant_shading_scene_name)
    #Export ass
    logger.info("--------Start export %s  ---------"%(variant.name()))
    pm.select(variant)
    write_ass(variant_maya_ass)
    log += ("- %s\n"%variant_maya_ass)
    write_maya_scene(variant_maya_scene)
    log += ("- %s\n"%variant_maya_scene)
    logger.info("Maya variant scene export succes: %s"%variant_maya_scene)
    if export_shading:
        write_maya_scene(variant_shading_scene)
        logger.info("Shading export succes: %s"%variant_maya_scene)

    #Restore visibility_state
    variant.visibility.set(variant_visibility_state)
    if mb_state == 1:
        pm.setAttr("defaultArnoldRenderOptions.motion_blur_enable",mb_state)
    return log

def printInfo(object):

    logger.debug("--- Object Infos ----")
    infos = vars(object)
    for i in infos.keys():
        logger.debug(i+": "+infos[i])
    logger.debug("--- Object Infos End ----")

def has_transfrom(obj):
    if cmds.xform(obj,query=True, matrix=True) != zero_matrix:
        logger.error('Transfroms applied on %s -> Plz fix manually'%obj)
        return True
    else:
        return False

def has_transfrom_user_fix_possible(obj):

    if cmds.xform(obj,query=True, matrix=True) != zero_matrix:
        msg = ("The root of the asset has transfrom informations.\n"
               "Transform will be reset before export\n"
               )
        result = cmds.confirmDialog( title='Confirm',message=msg,
        button=['Continue', "Cancel"],
        defaultButton='Continue', cancelButton='Cancel', dismissString='Cancel')
        if result == "Continue":
            cmds.move(0, 0, 0, ls=True)
            cmds.rotate(0, 0, 0)
            cmds.scale(1, 1, 1)
        if result == "Cancel":
            warning("Abort by user")

def deleteSource(node):
    if pm.referenceQuery(node,isNodeReferenced=True):
        path = pm.referenceQuery(node, filename=True)
        reference_node = pm.FileReference(path)
        pm.FileReference.importContents(reference_node)
        pm.delete(node)
    else:
        pm.delete(node)

def cleanAsset(asset):
    asset_name = asset.name().split(":")[-1]
    asset_visibility_state= asset.visibility.get()
    asset.visibility.set(1)
    variants, proxy = scanAsset(asset)
    asset_copy = pm.duplicate(asset)[0]
    if asset_copy.getParent():
        pm.parent(asset_copy, world=True)

    if pm.objExists("|"+asset_name):
        asset_rename = pm.rename("|"+asset_name, asset_name+"_original")
    pm.rename(asset_copy,asset_name)
    if asset_copy.name() != asset_name:
        pm.delete(asset_copy)
        utils.warning("Could not rename before export: %s exist already "%asset_name)
    asset_copy.translate.set(0,0,0)
    asset_copy.rotate.set(0,0,0)
    asset_copy.scale.set(1,1,1)


    utils.convert_selected_to_tx(asset)

    #Textures search path
    pm.setAttr("defaultArnoldRenderOptions.absoluteTexturePaths",0)
    pm.setAttr("defaultArnoldRenderOptions.texture_searchpath", "[DISK_I];[DISK_B];[DISK_P];I:/;P:/;B:/")

    asset.visibility.set(0)
    return asset_copy

def publish(asset, asset_dir, import_proxy_scene=False, selected_variant=False):
    log = "---- SUCCES ---- \n"

    asset_name = asset.name()
    asset_clean = cleanAsset(asset)
    variants, proxy = scanAsset(asset_clean)

    for v in variants:
        log += exportVariant(asset_clean,v,asset_dir,export_shading=True)

    proxy_scene_path = make_proxy_scene(asset_clean, asset_dir)
    if import_proxy_scene:
        namespace = utils.nameSpace_from_path(proxy_scene_path)
        refNode = pm.system.createReference(proxy_scene_path, namespace=namespace)
        nodes = pm.FileReference.nodes(refNode)
        if asset.getParent():
            pm.parent(nodes[0], asset.getParent())
        utils.match_matrix(nodes[0],asset)
    log += "- " + proxy_scene_path
    pm.delete(proxy)
    pm.delete(asset_clean)
    if not pm.referenceQuery(asset, isNodeReferenced=True):
        pm.rename(asset,asset_name)
    pm.confirmDialog(message= log.replace("\\","/"))
    logger.info("Publish succes !")

def publish_selected_variant(selected_variant, asset_dir):
    fake_proxy = False
    asset= selected_variant.getParent()
    if not asset: utils.warning("Can't get parent!")
    proxy_name = asset.name()+("|%s_proxy"%utils.only_name(asset))
    logger.debug(proxy_name+ "fake proxy")
    if not pm.objExists(proxy_name):
        logger.debug("Temp proxy created.")
        fake_proxy = pm.polySphere()[0]
        pm.parent(fake_proxy,asset)
        pm.xform(fake_proxy,m=zero_matrix)
        pm.rename(fake_proxy, proxy_name)

    log = "---- SUCCES ---- \n"
    asset_name = asset.name()
    asset_clean = cleanAsset(asset)
    variants, proxy = scanAsset(asset_clean)

    match = [v for v in variants if utils.only_name(v) == utils.only_name(selected_variant)]
    variants = match

    for v in variants:
        log += exportVariant(asset_clean,v,asset_dir,export_shading=True)

    pm.delete(proxy)
    pm.delete(asset_clean)
    if fake_proxy:
        pm.delete(fake_proxy)
    if not pm.referenceQuery(asset, isNodeReferenced=True):
        pm.rename(asset,asset_name)
    pm.confirmDialog(message= log.replace("\\","/"))
    logger.info("Publish succes !")


      
def has_transform(obj):
    if pm.xform(obj,query=True, matrix=True) != zero_matrix:
        return True
    else:
        return False

def scanAsset(asset):

    variants = [v for v in pm.listRelatives(asset,children=True) if v.endswith("_HD") or v.endswith("_SD")] 

    proxy =  [p for p in pm.listRelatives(asset,children=True) if utils.only_name(p)==utils.only_name(asset)+"_proxy"]
    if not variants: utils.warning("No variants found")
    if not proxy: utils.warning("No proxy found")

    for v in variants:
        if has_transform(v) : utils.warning('Transfroms applied on %s -> Plz fix manually'%v )
    if has_transform(proxy[0]) : utils.warning('Transfroms applied on %s -> Plz fix manually'%proxy[0])

    logger.info("Scan success")
    logger.info("Variants found: " + ", ".join([variant.name() for variant in variants]))
    logger.info("Proxy found: " +proxy[0].name())

    return variants, proxy[0]

def get_last_basic_variant_ass(asset_name,ass_dir):

    dic = utils.scan_ass_directory(ass_dir)
    if not dic: utils.warning("No variant found for proxy default DSO")
    ass_path = None
    default_variant = asset_name+"_HD"
    if default_variant in dic.keys():
        variant = default_variant
        last = dic[default_variant][-1]
        logger.debug("last found:%s "%(last))

    else:
        variant = list(dic.keys())[0]
        last =  dic[variant][-1]

        logger.debug("Found something, not sure what it is...:  %s"%(last))
    ass_path = os.path.join(ass_dir,variant,last,"%s.ass"%(variant))
    return ass_path

def make_proxy_scene(asset, asset_dir):
    #Init name
    variants, proxy = scanAsset(asset)
    asset_name = utils.only_name(asset)
    #Visibility
    visibility_state = proxy.visibility.get()
    proxy.visibility.set(True)

    #Arnold attribut
    proxy.ai_translator.set("procedural")
    ass_dir = os.path.join(asset_dir)
    ass_dir = os.path.join(asset_dir,asset_name,"publish","ass")
    ass_path =  get_last_basic_variant_ass(asset_name,ass_dir)

    proxy.dso.set(ass_path)
    proxy.aiOverrideShaders.set(0)
    proxy.aiOverrideMatte.set(1)

    publish_proxy_scene_dir = os.path.join(asset_dir,asset_name,"publish")
    next_publish_proxy_scene= get_next_publish_scene(publish_proxy_scene_dir, asset_name)
    logger.info("Next publish proxy maya scene  = %s"%next_publish_proxy_scene)

    pm.select(proxy)
    sub_assets = [s for s in pm.listRelatives(asset,children=True) if s.endswith("_assets")] 

    if sub_assets:
        pm.select(sub_assets[0],add=True,)
    else:

        proxy = pm.parent(proxy,world=True)[0]
        utils.lock_all_transforms(proxy, lock=False)
        pm.select(proxy)
    pm.system.exportSelected(next_publish_proxy_scene, force=False)    
    #cmds.file(next_publish_proxy_scene,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)
    logger.info('Proxy export success %s!'%next_publish_proxy_scene)
    #Restore properties
    proxy.ai_translator.set("polymesh")
    proxy.visibility.set(visibility_state)
    return next_publish_proxy_scene


