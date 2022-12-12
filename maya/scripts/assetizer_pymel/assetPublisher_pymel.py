import maya.cmds as cmds
import pymel.core as pm
import os
import utils_pymel as utils
import importlib
importlib.reload(utils)
import logging
import re
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
#logger.setLevel(logging.INFO)
zero_matrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]

def write_ass(path=""):
    cmds.file(path,
              force=False,
              options="-shadowLinks 0;-mask 6201;-lightLinks 0;-boundingBox;-fullPath",
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

def get_last_scene(dir, pattern, nextAvailable=False):
    if os.path.isdir(dir):
        my_list = os.listdir(dir)
    r = re.compile(pattern)
    newlist = list(filter(r.match, my_list))
    newlist.sort()
    if newlist:
        last_scene = newlist[-1]
        path = os.path.join(dir,last_scene)
        return path
    else:
        return None

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
                            button=['Save','Incremente & Save','Skip',"Cancel"],
                            defaultButton='Yes',
                            cancelButton='"Cancel',
                            dismissString='"Cancel' )
        if result == "Yes":
            pm.saveFile()

        if result == "Incremente & Save":
            pm.mel.eval("incrementAndSaveScene 0;")

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
    asset_name = asset.name
    variant_name = utils.only_name(variant)
    mb_state = pm.getAttr("defaultArnoldRenderOptions.motion_blur_enable")
    if mb_state == 1:
        pm.setAttr("defaultArnoldRenderOptions.motion_blur_enable",0)

    #Store visibility
    variant_visibility_state = variant.visibility.get()

    #Make visible
    if not variant_visibility_state:
        variant.visibility.set(True)
    utils.delete_hidden_children(variant)
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

def import_all_references(node):

    list_path = []
    if pm.referenceQuery(node,isNodeReferenced=True):
        list_path.append(pm.referenceQuery(node, filename=True))
    for s in pm.listRelatives(node, allDescendents=True):
        if pm.referenceQuery(s,isNodeReferenced=True):
            path = pm.referenceQuery(s, filename=True)
            if path not in list_path:
                list_path.append(path)
    if list_path:
        for path in list_path:
            ref_node = pm.FileReference(path)
            pm.FileReference.importContents(ref_node)

def deleteSource(node):
    import_all_references(node)
    pm.delete(node)

def cleanAsset(asset):
    asset_visibility_state= asset.maya.visibility.get()

    asset.maya.visibility.set(1)
    asset_copy = pm.duplicate(asset.maya)[0]
    logger.debug(asset_copy.name())
    if asset_copy.getParent():
        pm.parent(asset_copy, world=True)
        logger.debug("parent")

    if pm.objExists("|"+asset.name):
        asset_rename = pm.rename("|"+asset.name, asset.name+"_original")
    pm.rename(asset_copy,asset.name)
    if utils.only_name(asset_copy) != asset.name:
        logger.debug("%s----> %s"%(asset_copy.name(),asset.name) )
        pm.delete(asset_copy)
        utils.warning("Could not rename before export: %s exist already "%asset.name)
    asset_copy.translate.set(0,0,0)
    asset_copy.rotate.set(0,0,0)
    asset_copy.scale.set(1,1,1)
    utils.convert_selected_to_tx(asset)

    #Textures search path
    pm.setAttr("defaultArnoldRenderOptions.absoluteTexturePaths",0)
    pm.setAttr("defaultArnoldRenderOptions.texture_searchpath", "[DISK_I];[DISK_B];[DISK_P];I:/;P:/;B:/")

    asset.maya.visibility.set(asset_visibility_state)
    asset_clean = Asset(asset_copy)
    return asset_clean

def scanAsset(asset):
    variants = [v for v in pm.listRelatives(asset,children=True) if v.endswith("HD") or v.endswith("SD")]
    proxy =  [p for p in pm.listRelatives(asset,children=True) if utils.only_name(p)==utils.only_name(asset)+"_proxy"]
    return variants, proxy[0]

class Asset():
    def __init__(self,root):
        self.name = utils.only_name(root)
        self.maya = root
        self.variants = self.getVariant(root)
        self.proxy = self.getProxy(root)


    def getProxy(self, root):
        proxy =  [p for p in pm.listRelatives(root,children=True) if utils.only_name(p)==utils.only_name(root)+"_proxy"]
        if proxy:
            return proxy[0]
        else:
            return False

    def getVariant(self,root):
        variants = [v for v in pm.listRelatives(root,children=True) if v.endswith("HD") or v.endswith("SD")]
        return variants

def checkAsset(asset, proxy_must_exist=False):
    if not asset.variants: utils.warning("No variants found")
    if not asset.proxy and proxy_must_exist: utils.warning("No proxy found")

    for v in asset.variants:
        if has_transform(v) : utils.warning('Transfroms applied on %s -> Plz fix manually'%v )
    if proxy_must_exist:
        if has_transform(asset.proxy) : utils.warning('Transfroms applied on %s -> Plz fix manually'%asset.proxy)

    logger.info("Check success")
    logger.info("Variants found: " + ", ".join([variant.name() for variant in asset.variants]))
    if asset.proxy: logger.info("Proxy found:" +asset.proxy.name())

def publish(root, asset_dir, import_proxy_scene=False, selected_variant=False):

    asset= Asset(root)
    proxy_must_exist = True if selected_variant == False else False

    checkAsset(asset,  proxy_must_exist= proxy_must_exist)
    asset_clean = cleanAsset(asset)

    if selected_variant:
        exportVariant(asset_clean,selected_variant,asset_dir,export_shading=False)

    for v in asset_clean.variants:
        log = exportVariant(asset_clean,v,asset_dir,export_shading=False)

    if selected_variant:
        proxy_dir = os.path.join(asset_dir, asset_clean.name, "publish")
        proxy_scene_path = get_last_scene(proxy_dir,asset_clean.name+".v.*")
    else:
        proxy_scene_path = make_proxy_scene(asset_clean, asset_dir)

    if import_proxy_scene:
        namespace = utils.nameSpace_from_path(proxy_scene_path)
        refNode = pm.system.createReference(proxy_scene_path, namespace=namespace)
        nodes = pm.FileReference.nodes(refNode)
        if asset.maya.getParent():
            pm.parent(nodes[0], asset.maya.getParent())
        utils.match_matrix(nodes[0],asset.maya)
    log += "- " + proxy_scene_path
    if proxy_must_exist: pm.delete(asset_clean.proxy)
    pm.delete(asset_clean.maya)
    if not pm.referenceQuery(asset.maya, isNodeReferenced=True):
        pm.rename(asset.maya,root)
    pm.confirmDialog(message= log.replace("\\","/"))
    logger.info("Publish succes !")

def recursive_publish(root):
    childs= pm.listRelatives(root, children=True)
    shapes_list=[]
    transforms_list=[]
    for c in childs:
        shape = c.getShape()
        if shape:
            if pm.objectType(shape) == "mesh":
                print("mesh_found%s"%shape)
                shapes_list.append(c)
        else:
            transforms_list.append(c)

    if shapes_list:
        hd_grp= pm.createNode("transform",n="HD")
        pm.parent(hd_grp,root)
        utils.match_zero_matrix(hd_grp)
        pm.matchTransform(hd_grp,root,pivots=True)
        pm.parent(shapes_list,hd_grp)
        path = "D:/tmp/"+root.longName().replace("|","_")+".ass"
        #pm.select(hd_grp)
        publish_selected_variant(hd_grp, "D:/tmp/")
        #pm.system.exportSelected(path,force=False, type="ASS Export")
    if transforms_list:
        for transform in transforms_list:
            if pm.listRelatives(transform, children=True):
                recursive_publish(transform)

def has_transform(obj):
    if pm.xform(obj,query=True, matrix=True) != zero_matrix:
        return True
    else:
        return False


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
    ass_name = "%s_%s_%s_00"%(asset_name,variant,last)
    ass_path = os.path.join(ass_dir,variant,last,"%s.ass"%(variant))
    return ass_path

def make_proxy_scene(asset, asset_dir):
    #Init name
    proxy = asset.proxy
    variants = asset.variants
    asset_name = asset.name

    #Visibility
    visibility_state = proxy.visibility.get()
    proxy.visibility.set(True)

    #Arnold attribut
    proxy_name = proxy.name()
    proxy.ai_translator.set("procedural")
    ass_dir = os.path.join(asset_dir)
    ass_dir = os.path.join(asset_dir,asset_name,"publish","ass")
    ass_path=  get_last_basic_variant_ass(asset_name,ass_dir)

    proxy.dso.set(ass_path)
    proxy.aiOverrideShaders.set(0)
    proxy.aiOverrideMatte.set(1)

    publish_proxy_scene_dir = os.path.join(asset_dir,asset_name,"publish")
    next_publish_proxy_scene= get_next_publish_scene(publish_proxy_scene_dir, asset_name)
    logger.info("Next publish proxy maya scene  = %s"%next_publish_proxy_scene)
    #Cosmetic color
    proxy.useOutlinerColor.set(True)
    proxy.outlinerColor.set(1,0,0)
    pm.mel.eval('AEdagNodeCommonRefreshOutliners();')


    sub_assets = [s for s in pm.listRelatives(asset.maya,children=True) if s.endswith("_assets")]

    #Clean inputs listConnection
    shape = asset.proxy.getShape()
    try:
        sg = pm.listConnections(shape ,type="shadingEngine",plugs=True,connections=True)[0]
        pm.disconnectAttr(shape)
        pm.connectAttr(sg[0],sg[1])
    except:
        logger.warning("Fail to disconnect attr on: %s"%shape)
    if sub_assets:
        #pm.parent(sub_assets,world=True)
        #pm.parent(proxy,world=True)
        pm.select(proxy[0])
        pm.select(sub_assets[0],add=True)
        logger.infos("Childs assets found ! %s"%" ".join(sub_assets))
    else:
        pm.select(proxy)
        logger.info("No Childs assets found ! ")
        proxy = pm.parent(proxy,world=True)[0]
        print(proxy)
        utils.lock_all_transforms(proxy, lock=False)
        pm.select(proxy)
    pm.system.exportSelected(next_publish_proxy_scene, force=False)
    #cmds.file(next_publish_proxy_scene,force=False, options="v=0;", type="mayaAscii", pr=True, es=True)
    logger.info('Proxy export success %s!'%next_publish_proxy_scene)
    #Restore properties
    proxy.ai_translator.set("polymesh")

    proxy.visibility.set(visibility_state)
    return next_publish_proxy_scene
