from functools import partial
import maya.cmds as cmds
import os



def run(core):
    data = {}
    refNodes = cmds.ls(type='reference')
    for refNode in refNodes:
        if refNode == "sharedReferenceNode":
            continue
    
        try:
            file_path = cmds.referenceQuery(refNode, f=True, wcn=True)
            namespace = cmds.referenceQuery(refNode, ns=True)
        except:
            continue

        # récupérer les entity du porudcts via prism
        entity = core.products.getProductDataFromFilepath(file_path)


        # chercher tout les autre products qui sont lier aux Rigging
        data_all_variants = {}
        for product in core.products.getProductsFromEntity(entity):
            if not product["product"].startswith("Rigging_"):
                continue
            
            file_name = product["asset"] + "_" + product["product"] + "_" + product["version"] + ".ma"
            last_version_of_product = product["path"] + "\\" + product["version"] + "\\" + file_name

            if os.path.exists(last_version_of_product):
                data_all_variants[product["product"]] = last_version_of_product

        name_ctrl, name_variant = findNameCtrlVariant(namespace)
        data[refNode] = {"path_variants": data_all_variants, "namespace" : namespace, "name_ctrl": name_ctrl, "name_variant": name_variant}
    
    cmds.scriptJob(ka=True)
    CreateScrpitJob(data)


def findNameCtrlVariant(namespace):
    #permet de trouver le bon controller world et de trouver le bon attribute qui à le bon nom
    name_variant = None
    name_ctrl = None
    for ctrl in  ["ctrl_world", "c_world", "World_Ctr"]:
        if cmds.objExists(f"{namespace}:{ctrl}"):
            name_ctrl = f"{namespace}:{ctrl}"
            break
    
    for attr in  ["Variant", "variant", "var"]:
        if cmds.objExists(f"{name_ctrl}.{attr}"):
            name_variant = attr
            break
    
    return name_ctrl, name_variant


def callBackFunc(data, refNode):
    # cette fonction permet de reload / replace la référence du rig quand le un variant est selecitonner
    ctrl_world = data[refNode]["name_ctrl"]
    name_variant = data[refNode]["name_variant"]

    variant = cmds.getAttr(f"{ctrl_world}.{name_variant}", asString=True)
    try:
        scene_path = data[refNode]["path_variants"]["Rigging_" + variant]
    except:
        return

    cmds.file(scene_path, loadReference=refNode)
    
    #quand une commande est executer les scriptJob sont détruie du coup on rappeller la fonction qui les creer.
    CreateScrpitJob(data)

def CreateScrpitJob(data):
    # cette fonction permet de creer les scriptjob de callback quand un attribute est changer grace aux data nous pouvons faire des callback très précis grace aux nom de chaque ctrl_world de chaque référence.
    for refNode in data:
        data_variant = data[refNode]

        ctrl_world = data_variant["name_ctrl"]
        name_variant = data_variant["name_variant"]
        print(refNode, ctrl_world, name_variant)
        try:
            src = cmds.listConnections(f"{ctrl_world}.{name_variant}", plugs=True, source=True, destination=False)
            if src:
                cmds.disconnectAttr(src[0], f"{ctrl_world}.{name_variant}")
        except:
            continue

        cmds.scriptJob(attributeChange=[f"{ctrl_world}.{name_variant}", partial(callBackFunc, data, refNode)], killWithScene=False, ro=True)