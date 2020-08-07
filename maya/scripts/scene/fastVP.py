import maya.cmds as cmds
def fastVP():
    try:
        cmds.setAttr("defaultArnoldRenderOptions.standinDrawOverride",3)
    except:
        pass
    geometry = cmds.ls(geometry=True)
    for geo in geometry:
        try:
            cmds.setAttr( '{}.displaySmoothMesh'.format( geo ), 0 )
        except:
            pass
    cmds.evaluator(en = True, name = 'cache')
