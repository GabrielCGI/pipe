# Select by object type
import maya.cmds as cmds
yetiList = []
sel = cmds.ls()
for s in sel:
    if cmds.objectType(s, isType='pgYetiMaya'):
        yetiList.append(s)
        #cmds.setAttr(s+".displayOutput", 1)
        #cmds.setAttr(s+".drawFeedback", 1)
        

cmds.select(yetiList)