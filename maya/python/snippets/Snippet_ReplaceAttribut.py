import maya.cmds as cmds


oldnum = "001"
num = "002"

sel = cmds.ls(sl = True)

for s in sel:
    filepath = cmds.getAttr(s+".fileTextureName")
    newfilepath = filepath.replace(oldnum,num) 
    cmds.setAttr (s+".fileTextureName", newfilepath, type ="string")