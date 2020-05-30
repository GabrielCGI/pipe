import maya.cmds as cmds
sel = cmds.ls(selection=True)
for s in sel:
    try:
        cmds.setAttr(s+".aiOverrideMatte",1)
    except:
        pass