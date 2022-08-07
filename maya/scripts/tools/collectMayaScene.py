import shutil
import os
localCacheFolder = "I:/guerlain_cache"
networkPath = "I:/"
import time
dirList=[] #List of full directory to copy




import os

print ("---------- Start caching procces ----------- ")
def list_full_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory)]


def listAllAssPath():
    allAssPath = []
    listFiles = cmds.ls(type = 'aiStandIn')
    for l in listFiles:
        assPath = cmds.getAttr( l+'.dso' )
        #CHECK IS IT'S AN ASS SEQUENCE
        if assPath.endswith('.####.ass'):
            dirname = os.path.dirname(assPath).replace("\\", "/")
            assListDir = list_full_paths(dirname)

            allAssPath = allAssPath + assListDir
        else:
            if assPath not in allAssPath:
                allAssPath.append(assPath)
    return allAssPath

allMayaFile = cmds.file(list=True, q=True)
allAssFile = listAllAssPath()
allPath = allMayaFile + allAssFile

print ("LIST OF ASSET FOUND:")
for path in allPath:
    print(path)


def copyFromTo (source, to):
    os.makedirs(os.path.dirname(to),exist_ok=True)
    if (not os.path.exists(to)):
        try:
            shutil.copy2(source, to)
            print ("NEW FILE CACHED !\n " + source + "\n" + to+"\n")
        except:
            cmds.warning("Failed to copy a new file: %s to %s"%(source,to))
    #Check if the file has a different timestamp.
    elif(os.stat(source).st_mtime != os.stat(to).st_mtime):
        time_dif= str(os.stat(source).st_mtime - os.stat(to).st_mtime)
        try:
            shutil.copy2(source, to)
            print ("FILE UPDATED ! ("+time_dif+" secondes) \n"+ source + "\n" + to+"\n")
        except:
            cmds.warning("Failed to updated %s to %s (Time difference = %s secondes)"%(source,to,time_dif))

    else:
        print ("Skipping: " + source)



for path in allPath:
    splitPath = path.split(":")
    localPath = localCacheFolder +"/"+ splitPath[0] + splitPath[-1]
    print("CACHE PROCESS ON -> +"+path)
    try:

        copyFromTo(path,localPath)
    except:
        print("UNKNOWN FAILURE !")

print("********* Copy done *********** ")
