import pymel.core as pm
import re
import logging
logger = logging.getLogger()
import os
def warning(txt):
    result = pm.confirmDialog( title='Warning',
                            message=txt,
                            button=["Continue"],
                            defaultButton='Continue')
    pm.error(txt)

def info(txt):
    pm.confirmDialog( title='Info',
                        message=txt,
                        button=["Continue"],
                        defaultButton='Continue')

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


def assignAiStandard(objs, color=(0.5,0.5,0.8), name="aiStandardSurface"):
    proxy_shader = pm.shadingNode("aiStandardSurface", asShader=True, name=name)
    proxy_shader.specular.set(0.4)
    proxy_shader.baseColor.set(color)
    shadingGroup = pm.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)
    pm.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
    shadingGroup.forceElement(objs)

def popUp(txt):
    result = pm.confirmDialog( title='Pop up',
                        message=txt,
                        button=["Continue", "Stop"],
                        defaultButton='Continue',
                        cancelButton='"Stop',
                        dismissString='"Stop' )

    if result == "Stop":
        warning("abort by user")

def only_name(obj):
    only_name = obj.name().split("|")[-1].split(":")[-1]
    return only_name

def get_assets_directory():
    assets_dir = os.getenv('ASSETS_DIR')
    if not assets_dir:
        warning("NO ASSETS_DIR ! ")
    return assets_dir

def use_prism():
    current_project = os.getenv("CURRENT_PROJECT")
    if current_project == "trashtown_2112":
        return False
    else:
        return True

def get_asset_directory_from_asset_name(asset_name):
    #NO MAJUSCULE AT ASSET MEANING IT'S A SHOT ASSETS OR TRASHTOWN
    assets_dir = get_assets_directory()
    kind = ["Environment","Prop"]
    if not use_prism():

        asset_dir = os.path.join(assets_dir, asset_name)
        print (asset_dir)
        return asset_dir


    asset_enviro = os.path.join(assets_dir, kind[0], asset_name)
    is_enviro = os.path.isdir(asset_enviro)
    asset_prop = os.path.join(assets_dir, kind[1], asset_name)
    is_prop = os.path.isdir(asset_prop)

    if is_enviro and not is_prop:
        assets_dir = os.path.join(assets_dir, kind[0])
        return assets_dir

    if is_prop and not is_enviro:
        assets_dir = os.path.join(assets_dir, kind[1])
        return assets_dir

    if is_prop and is_enviro:
        warning("FAIL TO GUSS THE ASSET TYPE (Environment or Prop). Both exist with same name %s"%asset_name)

    if not is_enviro and not is_prop:
        warning("FAILED TO FIND THE ASSETS DIRECTORY FOR %s in %s"%(asset_name,assets_dir))

def nameSpace_from_path(path):
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        nameSpace = name + "_00"
        nameSpace= nameSpace.replace(".","_")
        return nameSpace

def lock_all_transforms(obj, lock=True):

    if lock == True:
        if type(obj) is not list:
            tpm_list = []
            tpm_list.append(obj)
            obj=tpm_list
        for o in obj:
            o.translate.lock()
            o.rotate.lock()
            o.scale.lock()

    if lock == False:
        if type(obj) is not list:
            tpm_list = []
            tpm_list.append(obj)
            obj=tpm_list
        for o in obj:
            #Note need to unlock both translate and translateXYZ to be sure
            o.translate.unlock()
            o.translateX.unlock()
            o.translateY.unlock()
            o.translateZ.unlock()
            o.rotate.unlock()
            o.rotateX.unlock()
            o.rotateY.unlock()
            o.rotateZ.unlock()
            o.scale.unlock()
            o.scaleX.unlock()
            o.scaleY.unlock()
            o.scaleZ.unlock()


def match_matrix(source, target):
    m = pm.xform(target, matrix=True, query=True)
    pm.xform(source, matrix=m)

def match_zero_matrix(source):
    zero_matrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    pm.xform(source, matrix=zero_matrix)

def delete_hidden_children(root):
    childs= pm.listRelatives(root,allDescendents=True)
    for c in childs:
        try:
            if c.visibility.get() ==0 and pm.objExists(c):
                pm.delete(c)
                logger.debug("Hidden item delete before proxy generation %s"%c)
        except Exception as e:
            logger.debug("Fail to delete %s in deletehiddenchildren()" %c)
            print (e)

def scan_ass_directory(ass_dir):

    dic_variants={}
    variants = os.listdir(ass_dir)
    for v in variants:
        v_dir = os.path.join(ass_dir,v)
        versions = os.listdir(v_dir)
        dic_variants[v]=versions

    return dic_variants

def list_all_textures_from_selected(obj):
    tex_list = []
    sg_list = []
    shapes= pm.listRelatives(allDescendents=True,shapes=True)
    for s in shapes:
        sg = pm.listConnections(s,type='shadingEngine')
        if sg:
            if sg not in sg_list:
                sg_list.append(sg)
    for sg in sg_list:
        files = pm.listHistory(sg, type="file")
        tex_list += files
        aiImages= pm.listHistory(sg, type="aiImage")
        tex_list += aiImages
    tex_list = list(set(tex_list))
    return tex_list

def convert_to_tx(texture):
    if pm.objectType(texture) == "file":
        path = texture.fileTextureName.get()
        base, ext = os.path.splitext(path)
        tx_path = base+".tx"
        if os.path.isfile(tx_path) and ext != ".tx":
            texture.fileTextureName.set(tx_path)
            logger.info("Set tx on: %s"%tx_path)
        elif ext == ".tx":
            logger.info("Already TX, skipping: %s"%tx_path)

        else:
            logger.info("Failed to set tx on: %s"%tx_path)

    if pm.objectType(texture) == "aiImage":
        path = texture.filename.get()
        base, ext = os.path.splitext(path)
        tx_path = base+".tx"
        if os.path.isfile(tx_path) and ext != ".tx":
            texture.fileTextureName.set(tx_path)
            logger.info("Set tx on: %s"%tx_path)
        elif ext == ".tx":
            logger.info("Already TX, skipping: %s"%tx_path)

        else:
            logger.info("Failed to set tx on: %s"%tx_path)

def convert_selected_to_tx(obj):

    tex_list= list_all_textures_from_selected(obj)
    for tex in tex_list:

        convert_to_tx(tex)

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
