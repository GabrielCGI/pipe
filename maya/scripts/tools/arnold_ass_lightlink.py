import maya.cmds as cmds
def light_link():
    sel =cmds.ls(selection=True)
    ass = sel[-1]
    assShape = cmds.listRelatives(ass, children=True)[0]
    del sel[-1]
    lights = cmds.listRelatives(sel, fullPath=True)
    c=[l.replace("|","/") for l in lights]
    string= "' '".join(c)
    string= string.replace(",","")
    expression= "['"+string+"']"
    node = cmds.createNode("aiSetParameter")


    #Light GROUP
    cmds.setAttr (node +".assignment[0]", "light_group=%s"%expression,type="string")
    cmds.setAttr ( node +".selection", "*",type="string")
    cmds.setAttr (node +".assignment[1]", "bool use_light_group=True",type="string")

    #Shadow  GROUP
    cmds.setAttr (node +".assignment[2]", "shadow_group=%s"%expression,type="string")
    cmds.setAttr (node +".selection", "*",type="string")
    cmds.setAttr (node +".assignment[3]", "bool use_shadow_group=True",type="string")

    cmds.connectAttr(node+".out","%s.operators[30]"%(assShape), f=True )
