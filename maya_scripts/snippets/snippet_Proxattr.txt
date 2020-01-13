import maya.cmds as cmds

patterns = ["bush_A"]


nodes = cmds.ls("*%s*" % p) # Get all node wich ends with this pattern
print nodes
path = "B:/nutro_1909/assets/pr_carrotLeaves/wind/D/pr_carrotLeavesWindVarD_standin.####.ass"

for node in nodes:
    try:
        print node
        cmds.setAttr(node+".dso", path, type="string")
        cmds.setAttr(node+".useFrameExtension", 1)
        cmds.setAttr(node+".frameOffset", -80)
    except:
        pass
