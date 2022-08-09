import maya.cmds as cmds
def run():

    nodes=cmds.ls( type="aiStandIn" )
    for node in nodes:

        if "herbesA_ass" in node:
            print ("FIXED :"+ node)
            cmds.setAttr(node+".overrideShaders",0)
run()
