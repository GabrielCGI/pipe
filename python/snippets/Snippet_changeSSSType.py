import maya.cmds as cmds
sel = cmds.ls(selection=True)
for s in sel:
    try:
        if cmds.getAttr(s+".subsurfaceType") == 1:
            print "\n=============\nCHANGED: "+s
        cmds.setAttr(s+".subsurfaceType",0)
    except:
        pass