import maya.cmds as cmds
import os
import sys
import importlib
#Load Abc Plugins
cmds.loadPlugin("AbcImport.mll", quiet=True)
cmds.loadPlugin("AbcExport.mll", quiet=True)



import assetsDb as assetsDb

import projects as projects


currentProject = projects.getCurrentProject()
projectsData = projects.getProjectData(currentProject)
assetsDir = projectsData.get("assetsDir")
assetsDic = projects.buildAssetDb()   #Get dictionnary of all asset for th current project


def listAbcFromDir(path):
    "List all Abc from a directory"
    listAbc = []
    for abc in os.listdir(path):
        if abc.endswith(".abc"):
            listAbc.append(abc)
    return listAbc

def importReference(path, refNamespace):
    "Import a reference given a path"
    cmds.file(path, reference = True, namespace=refNamespace)

def nameFromAbc(abc):
    "ch_name_01.abc => ch_name"
    #HacK paradise
    if len(abc.split("_"))==3:
        name = "%s_%s"%(abc.split("_")[0],abc.split("_")[1])
    if len(abc.split("_"))==2:
        name = abc.split("_")[0]
    return name

def createScriptNode(refNamespace, abcPath):
    childRef = cmds.referenceQuery("%sRN"%(refNamespace), rfn=True, ch=True)[0]     #HACK PROD NUTRO !!!! [-1] to get the ABC. [0] usualy


    script ='cmds.file ("%s", loadReference = "%s", type="Alembic")'%(abcPath, childRef)
    scriptNodeName = "scriptNode_"+refNamespace
    scriptNode = cmds.scriptNode (st= 1, n= scriptNodeName, bs=script, stp = "python")

    deferScript = 'cmds.file("%s", loadReference="%s", type="Alembic")'%(abcPath, childRef)        #Update the alembic.
    cmds.evalDeferred(deferScript)

def abcLoad(abcPath):
    "Import Abc from a directory"
    abc = abcPath.split("/")[-1]
    name = nameFromAbc(abc)
    refNamespace = name +"_shading_lib_"+ abc.split("_")[-1].split(".")[0]  #00 ou 01 ou 02
    print(name)
    shadingRefPath = assetsDic.get(name).get("shading")
    print(shadingRefPath)
    scriptNodeName = "scriptNode_" + refNamespace

    #Check if ABC has already been imported
    if cmds.objExists(scriptNodeName):
        print("Updating animation for: %s \n %s"%(refNamespace, abcPath))
        cmds.delete (scriptNodeName)                #Delete old script Node
        createScriptNode(refNamespace, abcPath)             #Create new script Node
    else:
        print("Importing animation for: %s \n %s" % (refNamespace, abcPath))
        importReference(shadingRefPath, refNamespace)               #Import Reference
        createScriptNode(refNamespace, abcPath)             #Create new script Node

def importAnim():
    "Import selected alembic in the file dialog - Master fonction"
    basicFilter = "*.abc"
    listAbc = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=4)
    for abcPath in listAbc:
        abcLoad(abcPath)
