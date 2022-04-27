import maya.cmds as cmds
import maya.mel as mel


#### VARIABLE TO SET ####

rawDirPath = r"I:\candyUp_2201\shots\olait_shot0140\fur\01"

range = "100 130"

sampleTimes = '"-0.15 0 0.15"'

####################################


dirPath = rawDirPath.replace('\\', '/')
selection = cmds.ls(type="pgYetiMaya")

path = dirPath + "/<NAME>.%04d.fur"

for s in selection:
    if cmds.getAttr(s+".fileMode") == 1:
        cmds.setAttr(s+".fileMode", 0)

cmds.select(selection)
cmd = 'pgYetiCommand -writeCache "%s" -range %s -sampleTimes %s'%(path, range, sampleTimes)

mel.eval(cmd)
for sel in selection:
    name = sel.replace(":","_")

    pathYeti = dirPath +"/"+ name + ".%04d.fur"
    cmds.setAttr(sel+".fileMode", 1)
    cmds.setAttr(sel+".cacheFileName", pathYeti, type="string")
