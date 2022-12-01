import os
import maya.cmds as cmds
#TO DO create light no shadow?

def bake_texture(obj, dir,resolution=1024):
    result = cmds.confirmDialog( title='UV?',
                        message='What about uvs?',
                        button=['Auto-generate','Use existing'],
                        defaultButton='Use existing',
                        cancelButton='"Cancel',
                        dismissString='"Cancel' )
    if result == "Auto-generate":
        uv_generate = True

    if result == "Use existing":
        uv_generate = False
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
    print(default_uv)

    cmds.select(obj)
    if uv_generate:
        proxy_uvset = cmds.polyUVSet(create=True,uvSet = "proxyUv")
        cmds.polyAutoProjection(uvSetName=proxy_uvset[0])
    cmds.select(obj)
    cmds.arnoldRenderToTexture(folder=dir,aa_samples=1,extend_edges=True,resolution=resolution, enable_aovs=True,uv_set=proxy_uvset[0])
    shape = cmds.listRelatives(obj, shapes=True)[0]
    albedo = [f for f in os.listdir(dir) if f.endswith(".exr") and shape in f][0]
    albedo_path = os.path.join(dir,albedo)
    file_node_albedo = cmds.shadingNode("file", asTexture=True, name ="proxyAlbedo")
    cmds.setAttr(file_node_albedo+".fileTextureName",albedo_path, type="string")

    proxy_shader = cmds.shadingNode("aiStandardSurface", asShader=True)
    #TO DO rename
    cmds.setAttr(proxy_shader+".specular",0.4)
    shadingGroup = cmds.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr(file_node_albedo+".outColor ", proxy_shader +".baseColor")
    cmds.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
    cmds.sets(obj, e=True, forceElement= shadingGroup)
    cmds.select(obj)
    cmds.polyCopyUV(obj, uvi=proxy_uvset[0],uvs=default_uv )
    cmds.delete(obj, constructionHistory = True)
    #Clean Lights
    cmds.delete(transform_domeL)
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


def displace_disable():
    shaderGroup=[]
    shapes =  cmds.ls(dag=1,o=1,s=1,sl=1)
    list_shadingGrp = []
    for shape in shapes:
        shadingGrp = cmds.listConnections(shape,type='shadingEngine')
        if shadingGrp :
            print("shading group found")
            if len(shadingGrp)==1:
                print("only one shafding group")
                if shadingGrp[0] != 'initialShadingGroup':
                    print("not a initialShadingGroup")
                    if shadingGrp[0] not in list_shadingGrp:
                        list_shadingGrp.append(shadingGrp[0])
                else:
                    print("It's a initialShadingGroup, can't duplicate")
            else:
                print (shadingGrp)
                print ("Too many shading group: %s"%str(len(shadingGrp)))
        else:
            print("No shading engine found !")

    if 'initialShadingGroup'in list_shadingGrp:  list_shadingGrp.remove('initialShadingGroup')
    print (list_shadingGrp)
    try:
        for shadingGrp in list_shadingGrp:
            shader = cmds.listConnections(shadingGrp+".surfaceShader")
            shader_ai = cmds.listConnections(shadingGrp+".aiSurfaceShader")
            if shader_ai != None:
                shader = shader_ai
            if shader != None:

                newshadingGroup = cmds.sets(name="lowpoly_%s" % shadingGrp, empty=True, renderable=True, noSurfaceShader=True)
                print("connecting aiSurface: %s"%shader[0])
                cmds.connectAttr("%s.outColor" % shader[0], "%s.aiSurfaceShader" % newshadingGroup)

                cmds.connectAttr("lambert1.outColor", "%s.surfaceShader" % newshadingGroup)
                print("connecting lambert success !")
                member_list = cmds.sets(shadingGrp, q=True)

                #Assign only to the geo that is both part of lowpoly set and shading group set
                match_set = set(member_list).intersection(shapes)

                cmds.sets(list(match_set), e=True, forceElement=newshadingGroup)

    except Exception as e:
            print(e)

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

def catclark_max(objs,max=1):
    for obj in objs:
        try:
            type = cmds.getAttr(obj+".aiSubdivType")

            ite = cmds.getAttr(obj+".aiSubdivIterations")

            if type ==1 and ite > max:
                cmds.setAttr(obj+".aiSubdivIterations",max)
        except Exception as e:
            print(e)


def proxy_generate(obj_root,name, maxEdgeLength=3,collapseThreshold=60, targetVertex= 3000):
    proxy= cmds.duplicate(obj_root, name=name)
    proxy = proxy[0]
    childrens = cmds.listRelatives(proxy,allDescendents=True, type="mesh",fullPath=True)
    #for o in cmds.listRelatives(proxy ,allDescendents=True, fullPath=True):
        #if cmds.objectType(o, isType='mesh'):
             #cmds.select(o)
             #cmds.polyRemesh(maxEdgeLength=maxEdgeLength, constructionHistory=0,collapseThreshold=collapseThreshold,caching=1)
    if cmds.listRelatives(proxy,parent=True) != None:
        proxy = cmds.parent(proxy, world=True )[0]
    try:
        proxy = cmds.polyUnite (proxy,mergeUVSets=True, n=name)[0]
    except:
        print("Poly unit failed")
    cmds.delete(proxy, constructionHistory = True)
    cmds.select(proxy)
    cmds.polyReduce (ver=1 ,trm=1 ,shp=0, keepBorder=1 ,keepMapBorder=1 ,
                    keepColorBorder=1 ,keepFaceGroupBorder=1 ,keepHardEdge=1 ,
                    keepCreaseEdge=1 ,keepBorderWeight=0.5 ,
                    keepMapBorderWeight=0.5,keepColorBorderWeight=0.5,
                    keepFaceGroupBorderWeight=0.5,
                    keepHardEdgeWeight=0.5 , keepCreaseEdgeWeight=0.5,
                    useVirtualSymmetry=0,preserveTopology=1,keepQuadsWeight=0,
                    cachingReduce=1 ,ch=1 ,p=50 ,vct=targetVertex ,tct=0 ,replaceOriginal=1)

    cmds.delete(proxy, constructionHistory = True)
    cmds.move(0, 0,0, proxy+".scalePivot",proxy+".rotatePivot", absolute=True)
    cmds.select(proxy)
    return (proxy)
