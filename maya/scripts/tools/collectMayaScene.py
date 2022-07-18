import shutil
import os
localCacheFolder = "I:/swarovski_cache"
networkPath = "I:/"

allMayaFile = cmds.file(list=True, q=True)
allAssFile = listAllAssPath()
allPath = allMayaFile + allAssFile

def listAllAssPath():
    allAssPath = []
    listFiles = cmds.ls(type = 'aiStandIn')
    for l in listFiles:
        assPath = cmds.getAttr( l+'.dso' )
        allAssPath.append(assPath)
    return allAssPath


def copyFromTo (source, to):
    os.makedirs(os.path.dirname(to),exist_ok=True)
    if (not os.path.exists(to)):
        print ("COPYING NEW FILE ! FROM " + source + "TO" + to)
        shutil.copy2(source, to)

    elif(os.stat(source).st_mtime - os.stat(to).st_mtime > 1):
        print ("NEW FILE FOUND! UPDATING "+ source + "TO" + to)

    else:
        print ("skipping" + source)

for path in allPath:
    splitPath = path.split(":")
    localPath = localCacheFolder +"/"+ splitPath[0] + splitPath[-1]
    try:
        copyFromTo(path,localPath)
    except:
        print("failed to copy:" + path + "--- to:" + localPath)

  
