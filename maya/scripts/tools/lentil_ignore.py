def lentil_ignore():
    for s in cmds.ls(selection=True):
        #addAttr -ln "mtoa_constant_ign"  -at double  -dv 1 |group1|pTorus1|pTorusShape1;
        shapes = cmds.listRelatives(s,fullPath=True,shapes=True)
        if shapes:
            shape= shapes[0]
            try:
                cmds.addAttr(shape,longName='mtoa_constant_ignore',at="double", dv=1)
                cmds.setAttr(shape+".mtoa_constant_ignore",keyable=True)
            except:
                print("skipping " + shape)
