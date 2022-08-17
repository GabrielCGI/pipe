import maya.cmds as cmds
def run():

    nodes=cmds.ls( type="aiStandIn" )
    for node in nodes:

        if "herbesA_ass" in node:
            print ("FIXED :"+ node)
            cmds.setAttr(node+".overrideShaders",0)

    #Alemanchier
    for node in nodes:

        if "leafA" in node or "leafsG" in node:
            if cmds.getAttr(node+".dso") == "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/leafA.abc" :
                cmds.setAttr(node+".dso", "I:/guerlain_2206/assets/plantAmelanchier/ass/leafA.ass", type="string")
                cmds.setAttr(node+".overrideShaders",0)
                print ("FIXED :"+ node)
                cmds.setAttr(node+".overrideShaders",0)
            if cmds.getAttr(node+".dso") == "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/leafG.abc" :
                cmds.setAttr(node+".dso", "I:/guerlain_2206/assets/plantAmelanchier/ass/leafG.ass", type="string")
                cmds.setAttr(node+".overrideShaders",0)
                print ("FIXED :"+ node)
                cmds.setAttr(node+".overrideShaders",0)

run()
