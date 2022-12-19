
def fix_shader_vp():
    dic_sg={}
    listShadingEngine = cmds.ls(type="shadingEngine")
    listShadingEngine.remove('initialParticleSE')
    listShadingEngine.remove('initialShadingGroup')
    for sg in listShadingEngine:
        try:
            a = cmds.listConnections( sg+".surfaceShader", plugs =True)
            cmds.connectAttr(a[0], sg+".aiSurfaceShader")
            print("succes aiSurfaceShader: "+ a[0])

        except Exception as e:
            print (e)
    for sg in listShadingEngine:
        try:
            a = cmds.listConnections( sg+".surfaceShader", plugs =True)
            cmds.connectAttr("lambert1.outColor", sg+".surfaceShader",f=True)
            print("succes lambert surface: "+ a[0])

        except Exception as e:
            print (e)
shader_operator()
