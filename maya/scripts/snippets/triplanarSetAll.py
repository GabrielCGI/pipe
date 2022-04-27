import maya.cmds as cmds
import maya.mel as mel


selection = cmds.ls(type="aiTriplanar")



for s in selection:
    cmds.setAttr(s+".coordSpace", 2)

