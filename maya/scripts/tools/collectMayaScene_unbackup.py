import shutil
import os
import time
import maya.cmds as cmds
import logging
import sys

logger = logging.getLogger("CollectFiles")
# Init variable
localCacheFolder = "Z:/"
networkPath = "I:/"
dirList = []  # List of full directory to copy
assSequenceDir = []


# Return ful path for list directroy
def list_full_paths(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory)]


def getHotCacheDir(dir):
    splitDir = dir.split(":")
    hotCacheDir = localCacheFolder + "/" + splitDir[0] + splitDir[-1]
    return hotCacheDir


def mTimeListDir(dir):
    list = os.listdir(dir)
    mtimeList = []
    for a in list:
        path = os.path.join(dir, a)
        mTime = os.stat(path).st_mtime
        mtimeList.append(mTime)
    return (mtimeList)


def isDirModified(dir):
    timestamp = None
    hotCacheDir = getHotCacheDir(dir)
    os.makedirs(hotCacheDir, exist_ok=True)
    # dirTime = os.stat(dir).st_mtime
    # print ("DIR TIME: "+str(dirTime))
    last_modif_dir = mTimeListDir(dir)
    last_modif_hotDir = mTimeListDir(hotCacheDir)

    if last_modif_dir != last_modif_hotDir:
        return True
    else:
        return False


def writeTimeStamp(time, dir):
    timeStamp = os.path.join(dir, "timestamp.txt")
    with open(timeStamp, 'w') as f:
        f.write(str(time))


def getTimeStamp(dir):
    hotCacheDir = getHotCacheDir(dir)
    timeStampPath = os.path.join(hotCacheDir, "timestamp.txt")
    with open(timeStampPath) as f:
        lines = f.readlines()
    timestamp = float(lines[0])
    return timestamp


# Return the path of all Arnold Ass StadnIN
def listAllAssPath():
    allAssPath = []
    listFiles = cmds.ls(type='aiStandIn')
    for l in listFiles:
        assPath = cmds.getAttr(l + '.dso')
        # CHECK IS IT'S AN ASS SEQUENCE
        if assPath.endswith('.####.ass'):
            dirname = os.path.dirname(assPath).replace("\\", "/")
            print("ASS SEQUENCE FOUND: " + assPath)
            if dirname not in assSequenceDir:
                assSequenceDir.append(dirname)
                if isDirModified(dirname):
                    print("Difference found. Updating " + dirname)
                    assListDir = list_full_paths(dirname)
                    allAssPath = allAssPath + assListDir
                    writeTimeStamp(os.stat(dirname).st_mtime, getHotCacheDir(dirname))
                else:
                    print("No folder difference found. Skipping  " + dirname)

        else:
            if assPath not in allAssPath:
                allAssPath.append(assPath)
    return allAssPath


def copyFromTo(source, to):
    if source == to:
        raise 
    size_source = os.path.getsize(source)
    size_dest = 0
    # need to check scene exist before getting size
    try:
        size_dest = os.path.getsize(to)
    except:
        pass
    kind = ""
    os.makedirs(os.path.dirname(to), exist_ok=True)

    # CHECK 1 !
    if (not os.path.exists(to)):
        try:
            shutil.copy2(source, to)
            kind = "new"
            print("New file cached:" + source + " ---> " + to + "\n")
        except Exception as e:

            cmds.warning("Failed to copy a new file: %s to %s" % (source, to))
            print("Oops!", e.__class__, "occurred.")

    # CHECK 2 ! Check if the file has a different timestamp.

    elif (os.stat(source).st_mtime != os.stat(to).st_mtime or size_source != size_dest):
        size_dif = size_source - size_dest
        time_dif = str(os.stat(source).st_mtime - os.stat(to).st_mtime)
        # size_dif = size_source-size_dest
        try:
            shutil.copy2(source, to)
            kind = "update"
            print("Updating: %s ---> %s (time dif= %s seocnde)(size dif=%s)" % (source, to, time_dif, size_dif))
        except Exception as e:
            cmds.warning("Failed to updated %s to %s (Time difference = %s secondes)" % (source, to, time_dif))
            print("Oops!", e.__class__, "occurred.")

    # CHECK 3 !
    else:
        kind = "skipped"
        print("Already sync: " + source)
    return kind


def run():
    print("\n")
    print("\n")
    print("------------------------------------------------")
    print("---------- Collect maya scene files ------------")
    print("------------------------------------------------")
    print("\n")
    allMayaFile = cmds.file(list=True, q=True)
    allAssFile = listAllAssPath()
    allPath = allMayaFile + allAssFile

    # print ("LIST OF ASSET FOUND:")
    # for path in allPath:
    #    print(path)
    counter_new = 0
    counter_update = 0
    counter_skip = 0
    copy = ""

    cmds.progressWindow(title='Stepped Progress Bar', progress=0, status='Local asset caching:', isInterruptable=False)
    limit = len(allPath)
    print("Total path: " + str(limit))
    step = 10
    i = 0
    for path in allPath:
        splitPath = path.split(":")
        localPath = path.replace("I:/swarovski_2205","Z:/swaChristmas_2023")
        localPath = localPath.replace("E:/swarovski_2205","Z:/swaChristmas_2023")
        assetFilename = os.path.basename(path)
        # logger.info("Cache on farm asset: %s"%(assetFilename))
        print("Cache on farm asset: %s" % (assetFilename))

        try:
            copy = copyFromTo(path, localPath)
        except Exception as e:
            print(path)
            print(localPath)
            print("FAILURE!")
            print("Oops!", e.__class__, "occurred.")
        if copy == "update":
            counter_update += 1
        if copy == "new":
            counter_new += 1
        if copy == "skipped":
            counter_skip += 1
        print("------------------------------------------------")

        i += 1
        progress = 100.0 / limit * i
        if progress % step:
            continue
        cmds.progressWindow(e=1, progress=progress, status='Local asset caching')
    cmds.progressWindow(endProgress=1)

    print("\n")
    print("Done !")
    print(str(counter_new) + " new files cached")
    print(str(counter_update) + " files updated")
    print(str(counter_skip) + " files skipped (already cached)")


def copySceneFile():
    path = cmds.file(q=True, sn=True)
    splitPath = path.split(":")
    print("paaath"+path)
    localPath = path.replace("E:/swarovski_2205","Z:/swaChristmas_2023")

    try:
        copy = copyFromTo(path, localPath)
    except Exception as e:
        print("Oops!", e.__class__, "occurred.")
