def fixcarrot():
    allObjects = cmds.ls(l=True)
    path = "B:/nutro_1909/assets/pr_carrotLeavesB/ass/leaveB/07/carrotLeaveB.####.ass"
    pathBushA = "B:/nutro_1909/assets/pr_carrotLeavesB/ass/bushA/04/bushA.####.ass"
    pathBushB = "B:/nutro_1909/assets/pr_carrotLeavesB/ass/bushB/05/bushB.####.ass"

    for obj in allObjects:
       if cmds.nodeType(obj) == 'aiStandIn':
           if "pr_carrotLeavesBVarB_prox" in obj:
               cmds.setAttr(obj+".dso", path, type="string")
               try:
                   cmds.setAttr(obj+".useFrameExtension",1)
               except:
                   pass
           if "bushA" in obj:
               cmds.setAttr(obj+".dso", pathBushA, type="string")
               cmds.setAttr(obj+".frameOffset",0)
           if "bushB" in obj:
               cmds.setAttr(obj+".dso", pathBushB, type="string")
               cmds.setAttr(obj+".frameOffset",0)