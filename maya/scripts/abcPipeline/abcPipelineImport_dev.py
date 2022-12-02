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
    # HACK SWAROVKI OLD=> childRef = cmds.referenceQuery("%sRN"%(refNamespace), rfn=True, ch=True)[0]     #HACK PROD NUTRO !!!! [-1] to get the ABC. [0] usualy
    childRefList = cmds.referenceQuery("%sRN"%(refNamespace), rfn=True, ch=True)
    for c in childRefList:
        if c.split(":")[-1].split("_")[0]=="ch":
            childRef = c

    script ='cmds.file ("%s", loadReference = "%s", type="Alembic")'%(abcPath, childRef)
    scriptNodeName = "scriptNode_"+refNamespace
    scriptNode = cmds.scriptNode (st= 1, n= scriptNodeName, bs=script, stp = "python")

    deferScript = 'cmds.file("%s", loadReference="%s", type="Alembic")'%(abcPath, childRef)        #Update the alembic.
    cmds.evalDeferred(deferScript)

def createCharStandIn(name,abc,asset_path_publish):
    a = cmds.createNode("aiStandIn",n=abc.split(".")[0]+"Shape")
    b= cmds.listRelatives(a,parent=True)
    c=cmds.rename(b,abc.split(".")[0])
    cmds.setAttr(c+".dso",abc,type="string")
    list = os.listdir(asset_path_publish)
    cmds.setAttr(a+".useFrameExtension", 1)
    operators = [o for o in list if o.endswith(".ass")]
    operators.sort()
    if operators:
        op = operators[-1]
        op_path= os.path.join(asset_path_publish,op)
        set_shader = cmds.createNode("aiIncludeGraph", n="aiIncludeGraph_"+abc.split(".")[0])
        cmds.setAttr(set_shader+".filename",op_path , type="string")
        cmds.setAttr(set_shader+".target", "aiStandInShape/input_merge_op", type="string" )
        cmds.connectAttr(set_shader+".out",c+".operators[0]", f=True )

def abcLoad(abcPath):
    "Import Abc from a directory"
    abc = abcPath.split("/")[-1]
    dir="B:/trashtown_2112/assets"
    name = nameFromAbc(abc)
    asset_path_publish= os.path.join(dir,name,"publish")
    if os.path.isdir(asset_path_publish):

        createCharStandIn(name, abc,asset_path_publish)

        refNamespace = name +"_shading_lib_"+ abc.split("_")[-1].split(".")[0]  #00 ou 01 ou 02
        print(name)
        shadingRefPath = assetsDic.get(name).get("shading")
        print(shadingRefPath)
        scriptNodeName = "scriptNode_" + refNamespace


    else:
        print(name + "FAIL: it's not V2")
def importAnim():
    "Import selected alembic in the file dialog - Master fonction"
    basicFilter = "*.abc"
    listAbc = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=4)
    for abcPath in listAbc:
        abcLoad(abcPath)
