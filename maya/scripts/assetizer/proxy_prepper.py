import os
import maya.cmds as cmds
#TO DO create light no shadow?

def bake_texture(obj, dir,resolution=1024):
    #Lights manipulation
    dic_lights={}
    lights = cmds.ls(type="light")
    for l in lights:
        dic_lights[l]= cmds.getAttr(l+".visibility")
        cmds.setAttr(l+".visibility",0)
    domeL = cmds.createNode("aiSkyDomeLight", n="tex_bake_dome")
    cmds.setAttr(domeL+".aiCastShadows",0)
    cmds.setAttr(domeL+".aiSpecular",0)


    default_uv  = merge_uv_sets(obj)

    cmds.select(obj)
    proxy_uvset = cmds.polyUVSet(create=True,uvSet = "proxyUv")
    cmds.polyAutoProjection(uvSetName=proxy_uvset[0])
    cmds.arnoldRenderToTexture(folder=dir,aa_samples=1,extend_edges=True,resolution=resolution, enable_aovs=True,uv_set=proxy_uvset[0])

    albedo = [f for f in os.listdir(dir) if f.endswith(".exr")][0]
    albedo_path = os.path.join(dir,albedo)
    file_node_albedo = cmds.shadingNode("file", asTexture=True, name ="proxyAlbedo")
    cmds.setAttr(file_node_albedo+".fileTextureName",albedo_path, type="string")

    proxy_shader = cmds.shadingNode("aiStandardSurface", asShader=True, name ="proxyShader")
    cmds.setAttr(proxy_shader+".specular",0.4)
    shadingGroup = cmds.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr(file_node_albedo+".outColor ", proxy_shader +".baseColor")
    cmds.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
    cmds.sets(obj, e=True, forceElement= shadingGroup)
    cmds.select(obj)
    cmds.polyCopyUV(obj, uvi=proxy_uvset[0],uvs=default_uv )
    cmds.delete(obj, constructionHistory = True)
    #Clean Lights
    cmds.delete(domeL)
    for l in dic_lights.keys():
        cmds.setAttr(l+".visibility",dic_lights[l])

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




def proxy_generate(obj_list, name, targetVertex= 500):
    if len(obj_list)>1:
        cmds.polyUnite  (obj_list,mergeUVSets=True, n=name)

    cmds.polyReduce (ver=1 ,trm=1 ,shp=0, keepBorder=1 ,keepMapBorder=1 ,
                    keepColorBorder=1 ,keepFaceGroupBorder=1 ,keepHardEdge=1 ,
                    keepCreaseEdge=1 ,keepBorderWeight=0.5 ,
                    keepMapBorderWeight=0.5,keepColorBorderWeight=0.5,
                    keepFaceGroupBorderWeight=0.5,
                    keepHardEdgeWeight=0.5 , keepCreaseEdgeWeight=0.5,
                    useVirtualSymmetry=0,preserveTopology=1,keepQuadsWeight=0,
                    cachingReduce=1 ,ch=1 ,p=50 ,vct=targetVertex ,tct=0 ,replaceOriginal=1)
    cmds.delete(name, constructionHistory = True)
