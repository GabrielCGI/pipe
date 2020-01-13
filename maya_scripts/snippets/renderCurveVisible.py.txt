import maya.cmds as cmds

sel = cmds.ls(selection=True)
for i in sel:
    try:
        cmds.setAttr(i+".aiRenderCurve", 1)
        cmds.setAttr(i+".aiCurveWidth",0.05)
        cmds.setAttr(i+".aiMode",1)
        cmds.connectAttr("aiStandardSurface2.outColor", i+".aiCurveShader")
    except:
        print "failed"+i