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

for s in cmds.ls(l=True):
    try:
        if cmds.nodeType(s) == 'aiStandIn':
            print s
            cmds.setAttr(s+".standInDrawOverride",0)
	    cmds.setAttr("defaultArnoldRenderOptions.standinDrawOverride", 3)
        
    except:
        pass