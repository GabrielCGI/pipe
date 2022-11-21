import os

#TO DO create light no shadow?
def bake_texture(obj, dir):
    cmds.select(obj)
    proxy_uvset = cmds.polyUVSet(create=True,uvSet = "proxyUv")
    cmds.polyAutoProjection(uvSetName=proxy_uvset[0])
    cmds.arnoldRenderToTexture(folder=dir,aa_samples=5,extend_edges=True,enable_aovs=True,uv_set=proxy_uvset[0])

    albedo = [f for f in os.listdir(dir) if f.endswith(".exr")][0]
    albedo_path = os.path.join(dir,albedo)
    file_node_albedo = cmds.shadingNode("file", asTexture=True, name ="proxyAlbedo")
    cmds.setAttr(file_node_albedo+".fileTextureName",albedo_path, type="string")

    proxy_shader = cmds.shadingNode("aiStandardSurface", asShader=True, name ="proxyShader")
    shadingGroup = cmds.sets(name="%sSG" % proxy_shader, empty=True, renderable=True, noSurfaceShader=True)

    cmds.connectAttr(file_node_albedo+".outColor ", proxy_shader +".baseColor")
    cmds.connectAttr("%s.outColor" % proxy_shader, "%s.surfaceShader" % shadingGroup)
    cmds.sets(obj, e=True, forceElement= shadingGroup)
    cmds.select(obj)
    cmds.polyCopyUV(obj, uvi=proxy_uvset[0],uvs="map1")
    uvsets = cmds.polyUVSet( obj, query=True, allUVSets=True )

    for uvset in uvsets:
        cmds.polyUVSet( delete=True, uvSet=uvset)




bake_texture("pCube2", "D:/gabriel/bake")
