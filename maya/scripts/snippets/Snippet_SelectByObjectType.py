# Select by object type
import maya.cmds as cmds
yetiList = []
sel = cmds.ls()
for s in sel:
    if cmds.objectType(s, isType='pgYetiMaya'):
        if "hedgehog" in s:
            yetiList.append(s)

cmds.select(yetiList)