import shutil
import os
import time
import maya.cmds as cmds
import logging
import sys
logger = logging.getLogger("CollectFiles")
#Init variable
localCacheFolder = "I:/guerlain_cache"
networkPath = "I:/"
dirList=[] #List of full directory to copy

#Return ful path for list directroy
def list_full_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory)]


#Return the path of all Arnold Ass StadnIN
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



def copyFromTo (source, to):

    kind=""
    os.makedirs(os.path.dirname(to),exist_ok=True)

    # CHECK 1 !
    if (not os.path.exists(to)):
        try:
            shutil.copy2(source, to)
            kind="new"
            print ("New file cached:" + source + " ---> " + to+"\n")
        except Exception as e:
            cmds.warning("Failed to copy a new file: %s to %s"%(source,to))
            print("Oops!", e.__class__, "occurred.")

    #CHECK 2 ! Check if the file has a different timestamp.
    elif(os.stat(source).st_mtime != os.stat(to).st_mtime):
        time_dif= str(os.stat(source).st_mtime - os.stat(to).st_mtime)
        try:
            counter_update = counter_update+1
            shutil.copy2(source, to)
            kind="update"
            print ("Updating: %s ---> %s (time dif= %s seocnde)"%(source,to,time_dif))
        except Exception as e:
            cmds.warning("Failed to updated %s to %s (Time difference = %s secondes)"%(source,to,time_dif))
            print("Oops!", e.__class__, "occurred.")
    #CHECK 3 !
    else:
        kind="skipped"
        print ("Already sync: " + source)
    return kind
def run():
    print("\n")
    print("\n")
    print ("------------------------------------------------")
    print ("---------- Collect maya scene files ------------")
    print ("------------------------------------------------")
    print("\n")
    allMayaFile = cmds.file(list=True, q=True)
    allAssFile = listAllAssPath()
    allPath = allMayaFile + allAssFile

    #print ("LIST OF ASSET FOUND:")
    #for path in allPath:
    #    print(path)
    counter_new=0
    counter_update=0
    counter_skip=0
    copy=""
    for path in allPath:
        splitPath = path.split(":")
        localPath = localCacheFolder +"/"+ splitPath[0] + splitPath[-1]
        assetFilename = os.path.basename(path)
        #logger.info("Cache on farm asset: %s"%(assetFilename))
        sys.stdout.write("Cache on farm asset: %s\n"%(assetFilename))

        try:
            copy = copyFromTo(path,localPath)
        except Exception as e:
            print("FAILURE!")
            print("Oops!", e.__class__, "occurred.")
        if copy == "update":
            counter_update +=1
        if copy == "new":
            counter_new +=1
        if copy == "skipped":
            counter_skip+=1
        print ("------------------------------------------------")


    print("\n")
    print ("Done !")
    print (str(counter_new) +" new files cached")
    print (str(counter_update) +" files updated")
    print (str(counter_skip)+" files skipped (already cached)")
