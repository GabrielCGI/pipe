import maya.cmds as cmds
import os
import sys
import importlib
#Load Abc Plugins
cmds.loadPlugin("AbcImport.mll", quiet=True)
cmds.loadPlugin("AbcExport.mll", quiet=True)
import maya.mel as mel
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
def createCharStandIn(name, anim_abc_path,abcv, asset_publish_path, asset_abc_path):
    name_standin_shape =abcv+"_00Shape"
    name_standin =abcv+"_00"
    if cmds.objExists(name_standin):
        result = cmds.confirmDialog( title='Confirm', message='The character already exist: %s'%name_standin,
        button=['Delete manually later',"Delete now"] )
        if result == "Delete now":
            cmds.delete(name_standin)
    a = cmds.createNode("aiStandIn",n=name_standin_shape)
    b= cmds.listRelatives(a,parent=True)
    c=cmds.rename(b,name_standin)
    abc_mod = [abc for abc in os.listdir(asset_abc_path) if abc.endswith("mod.abc")]
    if len(abc_mod) == 0:
        abc_mod = "none.abc"
        cmds.warning("Can't find modeling abc for %s"%name)
    else:
        abc_mod=abc_mod[0]
    abc_mod_path = os.path.join(asset_abc_path,abc_mod)
    cmds.setAttr(c+".dso",abc_mod_path,type="string")
    list = os.listdir(asset_publish_path)
    cmds.setAttr(c+".useFrameExtension", 1)
    operators = [o for o in list if o.endswith(".ass")]
    operators.sort()
    if operators:
        op = operators[-1]
        op_path= os.path.join(asset_publish_path,op)
        cmds.setAttr(c+".abc_layers", anim_abc_path , type="string")
        set_shader = cmds.createNode("aiIncludeGraph", n="aiIncludeGraph_"+abcv)
        cmds.setAttr(set_shader+".filename",op_path , type="string")
        #cmds.setAttr(set_shader+".target", "aiStandInShape/input_merge_op", type="string" )
        cmds.connectAttr(set_shader+".out",c+".operators[0]", f=True )
    return c
def abcLoad(anim_abc_path):
    "Import Abc from a directory"
    abc_filename = anim_abc_path.split("/")[-1]
    abcv = abc_filename.split(".")[0]
    dir=assetsDir
    name = nameFromAbc(abc_filename)
    #LEGACY WORKFLOW
    refNamespace = name +"_shading_lib_"+ abc_filename.split("_")[-1].split(".")[0]  #00 ou 01 ou 02










    shadingRefPath = assetsDic.get(name).get("shading")
    scriptNodeName = "scriptNode_" + refNamespace
    #LEGACY WORKFLOW  END
    asset_path= os.path.join(dir,name)
    asset_publish_path = os.path.join(asset_path,"publish")
    asset_abc_path = os.path.join(asset_path,"abc")
    if os.path.isdir(asset_publish_path):
        standin =createCharStandIn(name, anim_abc_path, abcv, asset_publish_path, asset_abc_path)
        return standin
    else:
        #LEGACY WORKFLOW
        if cmds.objExists(scriptNodeName):
            print("Updating animation for: %s \n %s"%(refNamespace, anim_abc_path))
            cmds.delete (scriptNodeName)                #Delete old script Node
            createScriptNode(refNamespace, abcPath)
           #Create new script Node
        else:
            print("LEGACY MODE !")
            print("Importing animation for: %s \n %s" % (refNamespace, anim_abc_path))
            importReference(shadingRefPath, refNamespace)               #Import Reference
            createScriptNode(refNamespace, anim_abc_path)
            #Create new script Node
def importAnim():
    "Import selected alembic in the file dialog - Master fonction"
    basicFilter = "*.abc"
    listAbc = cmds.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fileMode=4)
    list = []
    for abcPath in listAbc:
        standin = abcLoad(abcPath)
        list.append(standin)
    cmds.select(list)
