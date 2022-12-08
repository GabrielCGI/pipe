import pymel.core as pm
import logging
logger = logging.getLogger()
import os
def warning(txt):
    pm.error(txt)

def only_name(obj):
    only_name = obj.name().split("|")[-1].split(":")[-1]
    return only_name

def get_working_directory():
    working_directory = "D:/tmp/assets"
    return working_directory

def nameSpace_from_path(path):
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        nameSpace = name + "_00"
        nameSpace.replace(".","_")
        return nameSpace

def lock_all_transforms(obj, lock=True):

    if lock == True:
        if type(obj) == list:
            for o in obj:
                o.translate.lock()
                o.rotate.lock()
                o.scale.lock()
        else:
            obj.translate.lock()
            obj.rotate.lock()
            obj.scale.lock()
    if lock == False:
        if type(obj) == list:
            for o in obj:
                o.translate.unlock()
                o.rotate.unlock()
                o.scale.unlock()
        else:
            obj.translate.unlock()
            obj.rotate.unlock()
            obj.scale.unlock() 

def match_matrix(source, target):
    m = pm.xform(target, matrix=True, query=True)
    pm.xform(source, matrix=m)

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
        sg = pm.listConnections(s,type='shadingEngine')[0]
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
    print("cooooooooooonveeeeeeeert")
    tex_list= list_all_textures_from_selected(obj)
    for tex in tex_list:
        print(tex)
        convert_to_tx(tex)
