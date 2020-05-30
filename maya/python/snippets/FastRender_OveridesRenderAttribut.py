import maya.cmds as cmds
def setOverride(state=0):
    cmds.setAttr("defaultArnoldRenderOptions.ignoreMotionBlur",state)
    cmds.setAttr("defaultArnoldRenderOptions.ignoreDof",state)
    cmds.setAttr("defaultArnoldRenderOptions.ignoreSubdivision",state)
    
    
setOverride(state=1)