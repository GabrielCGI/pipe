import os
import maya.cmds as cmds
#TO DO create light no shadow?
import utils as utils
import importlib
importlib.reload(utils)
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def bake_texture(obj, dir,resolution=1024):
    if not obj.endswith("_proxy"):
        utils.warning("The selected object must be a proxy (ex: rock_proxy)")
    uv_generate = False
    auto_layout_uv = False

    result = cmds.confirmDialog( title='UV?',
                        message='What about uvs?',
                        button=['Auto-generate','Use existing','Existing + Autolayout'],
                        defaultButton='Use existing',
                        cancelButton='"Cancel',
                        dismissString='"Cancel' )
    if result == "Auto-generate":
        uv_generate = True

    if result == "Use existing":
        uv_generate = False
    if result == "Existing + Autolayout":
        auto_layout_uv = True

    if result == "Cancel":
        utils.warning("abort by user")

    #Lights manipulation
    dic_lights={}
    lights = cmds.ls(type="light")
    for l in lights:
        dic_lights[l]= cmds.getAttr(l+".visibility")
        cmds.setAttr(l+".visibility",0)
    domeL = cmds.createNode("aiSkyDomeLight")
    transform_domeL= cmds.listRelatives(domeL,parent=True)[0]
    cmds.connectAttr(transform_domeL+".instObjGroups", "defaultLightSet.dagSetMembers",nextAvailable=True)
    cmds.setAttr(domeL+".aiCastShadows",1)
    cmds.setAttr(domeL+".aiSpecular",0)


    default_uv  = merge_uv_sets(obj)


    cmds.select(obj)
    proxy_uvset = default_uv
    if uv_generate:
        proxy_uvset = cmds.polyUVSet(create=True,uvSet = "proxyUv")[0]
        cmds.polyAutoProjection(uvSetName=proxy_uvset,ps= 0.4)

    if auto_layout_uv:
        proxy_uvset = cmds.polyUVSet(create=True,uvSet = "proxyUv")[0]
        cmds.polyCopyUV(obj, uvi=default_uv , uvs=proxy_uvset)
        cmds.polyUVSet(obj,currentUVSet=True,uvSet=proxy_uvset)
        cmds.u3dLayout(res = 512, scl=1, rmn = 0, rmx = 360, rst= 25, spc= 0.003, mar = 0.003)

    cmds.select(obj)
    cmds.move(0,1000,0,relative=True)
    cmds.arnoldRenderToTexture(folder=dir,aa_samples=2,extend_edges=True,resolution=resolution, enable_aovs=True,uv_set=proxy_uvset)
    cmds.move(0,-1000,0,relative=True)
    shape = cmds.listRelatives(obj, shapes=True)[0]
    albedo = [f for f in os.listdir(dir) if f.endswith(".exr") and shape in f][0]
    albedo_path = os.path.join(dir,albedo)
    file_node_albedo = cmds.shadingNode("file", asTexture=True, name ="proxyAlbedo")
    cmds.setAttr(file_node_albedo+".fileTextureName",albedo_path, type="string")
    cmds.setAttr(file_node_albedo+".cs","ACEScg", type="string")

    proxy_shader = cmds.shadingNode("aiStandardSurface", asShader=True)
    #TO DO rename
    cmds.setAttr(proxy_shader+".specular",0.4)
    shadingGroup = cmds.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr(file_node_albedo+".outColor ", proxy_shader +".baseColor")
    cmds.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
    cmds.sets(obj, e=True, forceElement= shadingGroup)
    cmds.select(obj)
    cmds.polyCopyUV(obj, uvi=proxy_uvset,uvs=default_uv )
    cmds.delete(obj, constructionHistory = True)
    default_uv  = merge_uv_sets(obj)
    cmds.delete(obj, constructionHistory = True)
    
    #Clean Lights
    cmds.delete(transform_domeL)
    for l in dic_lights.keys():
        cmds.setAttr(l+".visibility",dic_lights[l])
    logger.info("Bake textures success ! ")

def merge_uv_sets(obj):
    default_uv = cmds.getAttr(obj+".uvSet[0].uvSetName")
    all_uv_sets = cmds.polyUVSet(obj, q=1, allUVSets=1)
    all_uv_sets.remove(default_uv)
    #temp_uv  = cmds.polyUVSet(create=True,uvSet = "temp_uv")[0]
    for uv_set in all_uv_sets:
        cmds.polyUVSet(currentUVSet = True, uvSet=uv_set)
        uvs = cmds.polyListComponentConversion(obj, toUV=True)
        #cmds.select(uvs)
        cmds.polyCopyUV( uvs, uvi= uv_set, uvs=default_uv )
        cmds.polyUVSet( delete=True, uvSet=uv_set)
    return default_uv

def generate_lowpoly(HD_grp):
    SD_GRP = cmds.duplicate(HD_grp,"SD")[0]
    SD_GRP = cmds.rename(SD_GRP,"SD")
    logger.info("SD group created")
    shapes = cmds.ls(SD_GRP,dag=1,o=1,s=1,sl=1)
    displace_disable(shapes)
    logger.info("Disable displace succes")
    catclark_max(shapes,1)

def displace_disable(shapes):
    shaderGroup=[]
    list_shadingGrp = []
    for shape in shapes:
        shadingGrp = cmds.listConnections(shape,type='shadingEngine')
        if shadingGrp:
            if len(shadingGrp)==1:
                if shadingGrp[0] != 'initialShadingGroup':
                    if shadingGrp[0] not in list_shadingGrp:
                        list_shadingGrp.append(shadingGrp[0])
            else:
                print ("Too many shading group: %s"%str(len(shadingGrp)))


    counter= 0
    for shadingGrp in list_shadingGrp:
        displace_shader = cmds.listConnections(shadingGrp+".displacementShader")
        if displace_shader == None:
            continue
        shader = cmds.listConnections(shadingGrp+".surfaceShader")
        shader_ai = cmds.listConnections(shadingGrp+".aiSurfaceShader")

        newshadingGroup = cmds.sets(name="lowpoly_%s" % shadingGrp, empty=True, renderable=True, noSurfaceShader=True)
        if shader_ai != None:
            cmds.connectAttr("%s.outColor" % shader_ai[0], "%s.aiSurfaceShader" % newshadingGroup)
        if shader != None:
            cmds.connectAttr("%s.outColor" % shader[0], "%s.surfaceShader" % newshadingGroup)
            member_list = cmds.sets(shadingGrp, q=True)
        if shader != None or shader_ai != None:
            #Assign only to the geo that is both part of lowpoly set and shading group set
            match_set = set(member_list).intersection(shapes)
            cmds.sets(list(match_set), e=True, forceElement=newshadingGroup)
            logger.info("Shading group created: %s"%newshadingGroup)
            logger.info("Shape list: " + ",".join(list(match_set)))
            counter+=1
    logger.info("%s shading group replaced"%(counter))

def getsize(sel):
    if not sel:
        return 0
    try:
        bb = cmds.xform(sel,bb=True, query=True)
        x = bb[3]-bb[0]
        y = bb[4]-bb[1]
        z = bb[5]-bb[2]
        moy = (x+y+z)/3
        edge_length = moy *0.05
        return edge_length
    except Exception as e:
        print(e)
        return 0

def build_hiearchy():
    logger.info("Start building hiearchy...")
    sel = cmds.ls(selection=True)
    if len(sel)!=1:
        utils.warning("Please select only one object (group or geo)")
    cmds.select(sel) #HACK TO PREVENT "FALSE SELECTION" AFTER MANUALY CREATING A GROUP WITH CTRL+G
    logger.info("Selection: %s"%sel)
    scene_path = cmds.file(q=True, sn=True)
    if "shots" in scene_path:
        asset_name = sel.split("|")[-1]
        logger.info("'Shot' has been detected in the scene path")
    else:
        asset_name =  os.path.basename(scene_path).split("_")[0].split(".")[0]
        logger.info("Asset name: %s"%asset_name)


    scene_parent = cmds.listRelatives(sel,parent=True,fullPath=True)
    logger.info("Scene parent: %s"%scene_parent)
    result = cmds.promptDialog(
                    title='Rename Object',
                    message='Enter Name:',
                    text = str(asset_name),
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
    if result == "OK":
        asset_name = cmds.promptDialog(query=True, text=True)
    else:
        cmds.warning('abort by user')
        raise

    if len(cmds.listRelatives( sel, children=True ))>1:
        logger.info("'Renaming group %s to geo"%sel)
        sel = cmds.rename(sel,"geo")

    else:
        if sel == asset_name:
            logger.info("Adding geo suffix to %s"%sel)
            sel = cmds.rename(sel,sel+"_geo")


    g = cmds.createNode("transform")
    g1 = cmds.createNode("transform")
    g2 = cmds.createNode("transform")
    g3 = cmds.createNode("transform")
    logger.info("Locking transform.")
    utils.lock_all_transform(g2)
    utils.lock_all_transform(g3)

    asset_grp =cmds.parent(g1,g)[0]
    basic_grp = cmds.parent(g2,asset_grp)[0]
    hd_grp  = cmds.parent(g3,basic_grp)[0]

    cmds.rename(hd_grp,"HD")
    cmds.rename(basic_grp,"variant_basic")
    if scene_parent:
        asset_grp = cmds.parent(asset_grp,scene_parent)
    else:
        asset_grp = cmds.parent(asset_grp,world=True)
    cmds.delete(g)
    asset_grp = cmds.rename(asset_grp,asset_name)

    m = cmds.xform(sel, relative = True, matrix=True, query=True)
    cmds.xform(asset_grp, matrix=m)

    hd_grp = asset_grp+"|variant_basic|HD"
    logger.info("HD group: %s"%hd_grp)
    sel = cmds.parent(sel,hd_grp)[0]
    logger.info("Parenting: %s to %s"%(sel,hd_grp ))
    logger.info("Hierarchy building is a succes !")



    #zero_matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    #cmds.xform(sel, matrix=zero_matrix)

def catclark_max(objs,max=1):
    for obj in objs:
        try:
            type = cmds.getAttr(obj+".aiSubdivType")

            ite = cmds.getAttr(obj+".aiSubdivIterations")

            if type ==1 and ite > max:
                cmds.setAttr(obj+".aiSubdivIterations",max)
        except Exception as e:
            print(e)

def proxy_generate(asset_name,asset_root,obj_root,name,targetVertex= 3000):
    childrens = cmds.listRelatives(obj_root,allDescendents=True,fullPath=True)

    if len(childrens) == 2: #SHAPE + TRANSFROMS
        obj_root = childrens[0]
    proxy= cmds.duplicate(obj_root, name=name)
    proxy = proxy[0]
    logger.debug("Duplicate: %s --> %s"%(str(obj_root),proxy))
    childrens = cmds.listRelatives(proxy,allDescendents=True, type="mesh",fullPath=True)
    if cmds.listRelatives(proxy,parent=True) != None:
        proxy = cmds.parent(proxy, world=True )[0]
    try:
        unit = cmds.polyUnite (proxy,mergeUVSets=True)[0]
        cmds.delete(unit , constructionHistory = True)
        proxy = cmds.rename(unit,name)

    except:
        logger.info("Only one object, skipping polyUnite step ")

    cmds.select(proxy)

    cmds.polyReduce (ver=1 ,trm=1 ,shp=0, keepBorder=1 ,keepMapBorder=1 ,
                    keepColorBorder=1 ,keepFaceGroupBorder=1 ,keepHardEdge=1 ,
                    keepCreaseEdge=1 ,keepBorderWeight=0.5 ,
                    keepMapBorderWeight=0.5,keepColorBorderWeight=0.5,
                    keepFaceGroupBorderWeight=0.5,
                    keepHardEdgeWeight=0.5 , keepCreaseEdgeWeight=0.5,
                    useVirtualSymmetry=0,preserveTopology=1,keepQuadsWeight=0,
                    cachingReduce=1 ,ch=1 ,p=50 ,vct=targetVertex ,tct=0 ,replaceOriginal=1)
    logger.info("Poly reducing success! (%s vertex)"%targetVertex)
    cmds.delete(proxy, constructionHistory = True)
    proxy = cmds.parent(proxy,asset_root)[0]
    zero_matrix = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
    cmds.xform(proxy,  matrix=zero_matrix)

    cmds.select(proxy)
    logger.info("Proxy generate success ! ")
    return (proxy)
