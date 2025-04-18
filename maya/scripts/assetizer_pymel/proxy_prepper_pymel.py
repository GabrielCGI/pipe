import os
import maya.cmds as cmds
import importlib
import logging
import pymel.core as pm
import utils_pymel as utils

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

zero_matrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def only_name(obj):
    only_name = obj.name().split("|")[-1]
    return only_name

def build_var_hiearchy(objs):
    # Check
    if len(objs) == 0:
        utils.warning("Not enough object selected")
    result = pm.promptDialog(
        title='Rename Object',
        message='Enter Name:',
        text=str(utils.only_name(objs[0])),
        button=['Validate as HD','Validate as SD', 'Cancel'],
        defaultButton='Validate as HD',
        cancelButton='Cancel',
        dismissString='Cancel')
    is_HD = result == "Validate as HD"
    is_SD = result == "Validate as SD"
    if not is_HD and not is_SD:
        utils.warning('abort by user')
        return
    if is_HD:
        suffix = "HD"
    else:
        suffix = "SD"
    asset_name = pm.promptDialog(query=True, text=True)

    #if variant already exists, parent to existing transform

    if cmds.objExists(asset_name):
        for obj in objs:
            var = pm.createNode("transform", n=asset_name+"_"+utils.only_name(obj).replace("_","")+suffix)
            pm.parent(obj, var)
            pm.parent(var, asset_name)
        pm.select(asset_name)

    else:
        root = pm.createNode("transform", n=asset_name)
        for obj in objs:
            var = pm.createNode("transform", n=asset_name+"_"+utils.only_name(obj).replace("_","")+suffix)
            pm.parent(var, root)
            pm.parent(obj, var)
        pm.select(root)


def build_hiearchy(obj):
    # Check
    if len(obj) != 1:
        utils.warning("Too many object selected")
    if pm.referenceQuery(obj, isNodeReferenced=True):
        utils.warning("Please import reference before")
    # Get asset name
    obj = obj[0]
    # Get the base name of the current scene file
    filename = pm.system.sceneName().basename()
    print(f"Filename: {filename}")

    # Split the filename by underscores
    filename_split = filename.split("_shading")

    # Check if there are more than two parts in the split filename
    if len(filename_split) >= 2:
        # Concatenate the first two parts to form the asset name
        asset_name = filename_split[0]
        print(f"Asset Name: {asset_name}")
    else:
        print("Filename does not contain enough parts to form an asset name.")
        asset_name = filename


    result = pm.promptDialog(
        title='Rename Object',
        message='Enter Name:',
        text=str(asset_name),
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel')
    if result == "OK":
        asset_name = pm.promptDialog(query=True, text=True)
    else:
        utils.warning('abort by user')

    scene_parent = pm.listRelatives(obj, parent=True)

    asset_grp = pm.createNode("transform")
    asset_grp_hd = pm.createNode("transform")
    pm.parent(asset_grp_hd, asset_grp)

    pm.matchTransform(asset_grp, obj)
    pm.parent(obj, asset_grp_hd)
    utils.lock_all_transforms(asset_grp_hd)
    for s in pm.listRelatives(asset_grp_hd, allDescendents=True, type="transform"):
        utils.lock_all_transforms(s)
    pm.rename(asset_grp, asset_name)
    pm.rename(asset_grp_hd, asset_name + "_HD")
    if utils.only_name(obj) == utils.only_name(asset_grp):
        pm.rename(obj, asset_name + "_geo")

    if scene_parent:
        pm.parent(asset_grp, scene_parent)
    pm.select(asset_grp_hd)
    return asset_grp


def generate_lowpoly(hd_grp):
    asset_name = only_name(hd_grp).split("_HD")[0]
    sd_grp = pm.duplicate(hd_grp, name=asset_name + "_SD")

    sd_grp = sd_grp[0]
    shapes = pm.listRelatives(sd_grp, allDescendents=True, shapes=True)
    disable_displace(shapes)
    catclark_max(shapes)
    hd_grp.visibility.set(0)
    logger.info("Generate lowpoly success!")
    return sd_grp


def disable_displace(shapes):
    list_sg = []
    for shape in shapes:
        sg = pm.listConnections(shape, type="shadingEngine", destination=True)
        if len(sg) == 1:
            if sg[0].name() != "initialShadingGroup":
                if sg[0] not in list_sg:
                    list_sg.append(sg[0])

    for sg in list_sg:

        displace = pm.listConnections(sg + ".displacementShader")
        if not displace:
            continue

        shader = pm.listConnections(sg + ".surfaceShader")
        shader_ai = pm.listConnections(sg + ".aiSurfaceShader")

        new_sg = pm.sets(name="sd_" + sg.name(), empty=True, renderable=True, noSurfaceShader=True)
        if shader_ai:
            pm.connectAttr(shader_ai[0] + ".outColor", new_sg + ".aiSurfaceShader")

        if shader:
            pm.connectAttr(shader[0] + ".outColor", new_sg + ".surfaceShader")
        member_list = sg.members()

        if shader or shader_ai:
            match_set = set(member_list).intersection(shapes)
            new_sg.forceElement(match_set)


def catclark_max(shapes, sub_max=1):
    for s in shapes:
        try:
            subdiv_type = pm.getAttr(s + ".aiSubdivType")
            ite = pm.getAttr(s + ".aiSubdivIterations")

            if subdiv_type == 1 and ite > sub_max:
                logger.debug("Lowering catclark on %s: %s to %s" % (s, ite, sub_max))
                pm.setAttr(s + ".aiSubdivIterations", sub_max)
        except Exception as e:
            print(e)


def merge_uv_sets(obj):
    if type(obj) == list:
        obj = obj[0]
    default_uv = pm.getAttr(obj + ".uvSet[0].uvSetName")
    all_uv_sets = pm.polyUVSet(obj, q=1, allUVSets=1)
    all_uv_sets.remove(default_uv)

    for uv_set in all_uv_sets:
        pm.polyUVSet(currentUVSet=True, uvSet=uv_set)
        uvs = pm.polyListComponentConversion(obj, toUV=True)
        pm.polyCopyUV(uvs, uvi=uv_set, uvs=default_uv)
        pm.polyUVSet(delete=True, uvSet=uv_set)
    return default_uv


def delete_all_uv_sets(obj):
    if type(obj) == list:
        obj = obj[0]
    uv_sets_list = pm.polyUVSet(obj, q=True, allUVSets=True)
    default_uv = pm.getAttr(obj + ".uvSet[0].uvSetName")
    uv_sets_list.remove(default_uv)
    for uv_set in uv_sets_list:
        try:
            pm.polyUVSet(delete=True, uvSet=uv_set)
        except:
            logger.debug("Can't delete %s" % uv_set)


def bake_texture(obj, dir, resolution=512, proxy_texture=False):
    if not obj.endswith("_proxy"):
        utils.warning("Not a proxy")

    if not proxy_texture:
        proxy_shader = pm.shadingNode("aiStandardSurface", asShader=True, name=obj.name() + "_shader")
        proxy_shader.specular.set(0.4)
        proxy_shader.baseColor.set(0.59436, 0.936, 0.936)
        shadingGroup = pm.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)
        pm.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
        shadingGroup.forceElement(obj)
        delete_all_uv_sets(obj)
        pm.delete(obj, constructionHistory=True)
        return

    result = pm.confirmDialog(title='UV?',
                              message='What about uvs?',
                              button=['Auto-generate', 'Use existing', 'Existing + Autolayout'],
                              defaultButton='Use existing',
                              cancelButton='"Cancel',
                              dismissString='"Cancel')

    if result == "Cancel":
        utils.warning("abort by user")

    default_uv = merge_uv_sets(obj)
    os.makedirs(dir, exist_ok=True)

    if result == "Auto-generate":
        proxy_uvset = pm.polyUVSet(create=True, uvSet="proxyUv")[0]
        pm.polyAutoProjection(uvSetName=proxy_uvset, ps=0.4)

    if result == "Existing + Autolayout":
        proxy_uvset = pm.polyUVSet(create=True, uvSet="proxyUv")[0]
        pm.polyCopyUV(obj, uvi=default_uv, uvs=proxy_uvset)
        pm.polyUVSet(obj, currentUVSet=True, uvSet=proxy_uvset)
        pm.u3dLayout(res=512, scl=1, rmn=0, rmx=360, rst=25, spc=0.003, mar=0.003)

    if result == "Use existing":
        proxy_uvset = default_uv

    dic_lights = {}
    lights = pm.ls(type=["light", "aiSkyDomeLight", "aiAreaLight"])
    for l in lights:
        l = l.getTransform()
        dic_lights[l] = l.visibility
        l.visibility.set(False)
    domeL = pm.createNode("aiSkyDomeLight")
    pm.connectAttr(domeL.getTransform() + ".instObjGroups", "defaultLightSet.dagSetMembers",
                   nextAvailable=True)  # Illuminate by default
    domeL.aiSpecular.set(0)

    pm.move(obj, 1000, r=True)
    pm.select(obj)
    pm.arnoldRenderToTexture(
        folder=dir,
        aa_samples=2, extend_edges=True,
        resolution=resolution,
        enable_aovs=True,
        uv_set=proxy_uvset
    )
    pm.move(obj, -1000, r=True)

    albedo = [f for f in os.listdir(dir) if f.endswith(".exr") and obj.name() in f][0]
    albedo_path = os.path.join(dir, albedo)
    file_node_albedo = pm.shadingNode("file", asTexture=True, name="proxyAlbedo")
    file_node_albedo.fileTextureName.set(albedo_path)
    file_node_albedo.cs.set("ACEScg")

    proxy_shader = pm.shadingNode("aiStandardSurface", asShader=True, name=obj.name() + "_shader")
    proxy_shader.specular.set(0.4)
    proxy_shader.baseColor.set(0.59436, 0.936, 0.936)

    shadingGroup = pm.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)
    pm.connectAttr(file_node_albedo + ".outColor ", proxy_shader + ".baseColor")
    pm.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
    shadingGroup.forceElement(obj)

    pm.polyCopyUV(obj, uvi=proxy_uvset, uvs=default_uv)
    default_uv = merge_uv_sets(obj)
    pm.delete(obj, constructionHistory=True)
    pm.delete(domeL.getTransform())

    for l in dic_lights.keys():
        l.visibility.set(True)
    logger.info("Bake textures success ! ")


def generate_proxy(grp, percentage):
    try:
        asset = grp.getParent()

    except Exception as e:
        print(e)
        utils.warning("Please select a valid group")
    result = pm.promptDialog(
        title='Proxy name',
        message='Enter Name:',
        text=str(only_name(asset)) + "_proxy",
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel')

    if result == "OK":
        proxy_name = pm.promptDialog(query=True, text=True)
    else:
        utils.warning('abort by user')

    proxy = pm.duplicate(grp)
    proxy_parent = pm.listRelatives(grp, parent=True)
    utils.delete_hidden_children(proxy)

    try:
        proxy_unit = pm.polyUnite(proxy, mergeUVSets=True)[0]
        pm.delete(proxy_unit, constructionHistory=True)
        if pm.objExists(proxy):
            logger.info("Leftover found, cleaning...")
            pm.delete(proxy)  # Get ride of non polymesh & non united leftover
        proxy = proxy_unit
        logger.info("Poly Unit success %s" % proxy)
    except Exception as e:
        child = pm.listRelatives(proxy, children=True)[0]
        pm.parent(child, proxy_parent)
        pm.delete(proxy)
        proxy = child
        logger.info("Skipping poly unit %s" % proxy)
        pass

    pm.polyReduce(proxy, ver=1, keepQuadsWeight=0, p=percentage)
    pm.polySetToFaceNormal(proxy)
    pm.delete(proxy, constructionHistory=True)
    utils.lock_all_transforms(proxy, lock=False)
    for s in pm.listRelatives(proxy, allDescendents=True, type="transform"):
        utils.lock_all_transforms(s, lock=False)

    pm.parent(proxy, proxy_parent)
    pm.matchTransform(proxy, proxy_parent, pivots=True)
    pm.makeIdentity(proxy, apply=True)

    pm.rename(proxy, proxy_name)
    pm.delete(proxy, constructionHistory=True)
    utils.lock_all_transforms(proxy)
    grp.visibility.set(0)

    proxy_shape = proxy.getShape()
    proxy_shape.primaryVisibility.set(0)
    proxy_shape.castsShadows.set(0)
    proxy_shape.aiVisibleInDiffuseReflection.set(0)
    proxy_shape.aiVisibleInSpecularReflection.set(0)
    proxy_shape.aiVisibleInDiffuseTransmission.set(0)
    proxy_shape.aiVisibleInSpecularTransmission.set(0)
    proxy_shape.aiVisibleInVolume.set(0)
    proxy_shape.aiSelfShadows.set(0)

    logger.info("Proxy generate success ! ")
