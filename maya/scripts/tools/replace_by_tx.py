import os.path
import maya.cmds as cmds
def replace_by_tx():
    counter = 0
    errorcounter= 0
    goodList = []
    allFileNodes = cmds.ls(et="file")
    for eachFile in allFileNodes:
        my_file = cmds.getAttr("%s.fileTextureName" % eachFile)
        base = os.path.splitext(my_file)[0]
        new_file = base+".tx"
        if os.path.isfile(new_file):
            counter+=1
            goodList.append(new_file)
            cmds.setAttr("%s.ignoreColorSpaceFileRules" % eachFile,1)
            cmds.setAttr("%s.fileTextureName" % eachFile, new_file, type="string")
        else:
           errorcounter+=1
           error =("MISSING TX: %s " % my_file)
           cmds.warning( error )
    print ("Replaced %s files !  \n%s errors"%(counter,errorcounter))
    for i in goodList:
        print ("Replaced with succes: "+i)

def replace_by_original():
    counter = 0
    errorcounter= 0
    goodList=[]
    allFileNodes = cmds.ls(et="file")
    fileType = ["exr","jpg","png","tiff"]
    for eachFile in allFileNodes:
        my_file = cmds.getAttr("%s.fileTextureName" % eachFile)
        base = os.path.splitext(my_file)[0]
        checkcounter = counter
        for type in fileType:
            new_file = base+"."+type

            if os.path.isfile(new_file):
                counter+=1
                goodList.append(new_file)
                cmds.setAttr("%s.ignoreColorSpaceFileRules" % eachFile,1)
                cmds.setAttr("%s.fileTextureName" % eachFile, new_file, type="string")
        if checkcounter == counter:
               errorcounter+=1
               error =("MISSING ORIGINAL FILE : %s " % my_file)
               cmds.warning( error )
    print ("Replaced %s files !  \n%s errors"%(counter,errorcounter))
    for i in goodList:
        print ("Replaced with succes:"+i)
replace_by_tx()
replace_by_original()
