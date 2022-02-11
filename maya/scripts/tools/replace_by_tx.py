import os.path
import maya.cmds as cmds
def replace_by_tx():
    counter = 0
    errorcounter= 0
    allFileNodes = cmds.ls(et="file")

    for eachFile in allFileNodes:
        my_file = cmds.getAttr("%s.fileTextureName" % eachFile)
        base = os.path.splitext(my_file)[0]
        new_file = base+".tx"
        if os.path.isfile(new_file):
            counter+=1
            cmds.setAttr("%s.fileTextureName" % eachFile, new_file, type="string")
        else:
           errorcounter+=1
           error =("MISSING TX: %s " % my_file)
           cmds.warning( error )
    print ("Replaced %s files !  \n%s errors"%(counter,errorcounter))
