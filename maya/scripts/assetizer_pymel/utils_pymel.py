import pymel.core as pm
import logging
logger = logging.getLogger()
import os
def warning(txt):
    pm.error(txt)

def popUp(txt):

    result = pm.confirmDialog( title='Pop up',
                        message=txt,
                        button=["Continue", "Stop"],
                        defaultButton='Continue',
                        cancelButton='"Stop',
                        dismissString='"Stop' )

    if result == "Stop":
        utils.warning("abort by user")

def only_name(obj):
    only_name = obj.name().split("|")[-1].split(":")[-1]
    return only_name

def get_working_directory():
    working_directory = "D:/assets"
    return working_directory

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
