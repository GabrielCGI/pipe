import maya.cmds as cmds
def light_link():
    a =cmds.ls(selection=True)
    ass = a[-1]
    assShape = cmds.listRelatives(ass, children=True)[0]
    del a[-1]
    b = cmds.listRelatives(a, fullPath=True)
    c=[f.replace("|","/") for f in b]
    d= "' '".join(c)
    e= d.replace(",","")
    expression= "['"+e+"']"
    node = cmds.createNode("aiSetParameter")
    nodeUse = cmds.createNode("aiSetParameter")
    cmds.setAttr (node +".assignment[0]", "light_group=%s"%expression,type="string")
    cmds.setAttr ( node +".selection", "*",type="string")
    cmds.setAttr (node +".assignment[1]", "bool use_light_group=True",type="string")
    cmds.connectAttr(node+".out","%s.operators[20]"%(assShape), f=True )
