# Regular expression example, replace 'Shot_003' with 'Shot_002'
import re
import os.path
import nuke
import nukescripts
import glob

def frameRange(path):
    dir = os.path.dirname(path)
    filename = path.split("\\")[-1]
    baseFileName = filename.split(".")[0]
    baseFilePath = os.path.join(dir, baseFileName)
    list = glob.glob(baseFilePath+'*')

    start = list[0].split(".")[-2]
    if not start == "0000":
        start = start.lstrip("0")

    end  = list[-1].split(".")[-2]
    if not end == "0000":
        end = end.lstrip("0")
    try:
        print int(start)
        print int(end)
    except:
        print "ERROR WITH START AND END RANGE"
        print 'start' + start
        print 'end' + end
        raise
    startEnd = start + "-" + end
    return startEnd



def start():
    oReadNodes = nuke.allNodes('Read')
    nodeList = []
    selNodes= nuke.selectedNodes()
    if selNodes[0].Class() != "Read":
        raise

    selNodePath = selNodes[0]['file'].value()
    oldDirPath = os.path.dirname(selNodePath)
    for node in oReadNodes:
        if  os.path.dirname(node['file'].value()) == oldDirPath:
            nodeList.append(node)

    path = nuke.getFilename("Select Directory")
    if not os.path.basename(path):
        #newDirPath = os.path.abspath(path)
        newDirPath =  os.path.dirname(path)
    else:
        newDirPath = os.path.dirname(path)

    for node in nodeList:
        oPath = node["file"].value()
        oNewPath = re.sub(oldDirPath, newDirPath, oPath) #UPDATE THE DIRECTORY

        # TURN A SINGLE FRAME INTO SEQUENCE using "####"
        splitPath = oNewPath.split("/")
        fileName = splitPath[-1].split(".")
        #Calculate the padding ####

        if fileName[-2] == "%03d":
            padding = "###"
        if fileName[-2] == "%04d":
            padding = "####"

        fileName[-2]=padding

        fileNameCompo = ""
        for file in fileName:
            fileNameCompo = fileNameCompo+"."+file
        splitPath[-1]= fileNameCompo[1:]

        #REBUILD THE PATH WITH THE NEW ####
        oNewPath = os.path.join(*splitPath)
        oNewPath = os.path.abspath(oNewPath )

        startEnd = frameRange(oNewPath)
        node["file"].fromUserText(oNewPath + " "+ startEnd)
