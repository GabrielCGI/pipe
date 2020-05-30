"""
ABC PIPELINE TOOLS V0.1

Allow to add an asset to the alembic pipeline.
Need a referenced rig matching the pattern XX_assetName_rig_lib
Export an alembic with custom attribut.
Export a dictionary as a .txt with asset data.
Create a shading scene.

"""
import maya.cmds as cmds
import os.path
import json
import sys
import projects as projects
reload(projects)

# Project variable initialisation
assetsDbDir = projects.getCurrentProjectData()["assetsDbDir"] #Something like B:\Teaser\assets\database
assetsDir = projects.getCurrentProjectData()["assetsDir"] #Something like B:\Teaser\assets\database

def mayaWarning(msg):
    """
    Display of maya warning
    """
    cmds.warning(msg)
    cmds.confirmDialog(title="Error",message=msg)

def buildCommand (abcPath, geoList, attrList):
   "Build Command for alembic export job"
   command = ""
   command += "-frameRange 1 1" #Frame Range
   command += " -uvWrite -writeUVSets -dataFormat ogawa "
   if attrList[0]:
       for attr in attrList:
           command += " -attr %s"%(attr)           #Attributs
   for geo in geoList:
       geoRootName = cmds.ls(geo, l=True)[0]     #Geo List
       command += " -root %s"%geoRootName

   command += " -file %s"%(abcPath)                #File Path
   return command

def exportAbc(abcPath, currentSelection, attrList):
    """Export an alembic of current selection.
       Return the path of the created alembic"""
    geoList = currentSelection
    # Add custom attribut to export with alembic.
    command = buildCommand(abcPath,geoList,attrList)
    print "------------------------\n------------ BEGGINING EXPORT %s ------------ \n %s"%(abcPath, command)
    cmds.refresh(suspend=True)
    cmds.AbcExport (j= command )
    cmds.refresh(suspend=False)
    print "------------ SUCCESS EXPORT ! ------------"
    return abcPath

def createNewAsset():
    """
    Main function that drive the export
    """
    #Info window
    msg = "About this tool.\n\nThis tools add new assets into the database for easy export/import Alembic."
    msg +="\n\nImportant - Select only the geometry you want to export."
    msg +="\nThis maya scene need to have a referenced rig lib (Ch_assetName_rig_lib)"
    msg +="\nExport alembic, write data and automaticaly create the shading scene"
    confirm = cmds.confirmDialog( title='Abc pipeline Tools',
                                    message=msg,
                                    button=['Continue','Stop'], defaultButton='Continue', cancelButton='Stop', dismissString='Stop'                                    )
    if confirm == "Stop":
        msg = "Abort by user."
        mayaWarning(msg)
        sys.exit(msg)
    #End info window

    #Get current selection
    currentSelection = cmds.ls(selection=True)
    ##CHECKS BEGGING##
    #Check: Is something selected ?
    if not currentSelection:
        msg = "Nothing selected. \nSelect geo to export"
        mayaWarning(msg)
        sys.exit(msg)

    assetNamespace = currentSelection[0].split(":")[0] #Something like Ch_assetName_rig_lib
    split = assetNamespace.split("_") #Somethinh like ["Ch","assetName","Rig","lib"]
    #Check: Does it match the pattern XX_assetName_rig_lib ?
    if not (len(split) == 4 and split[2]=="rigging" and split[3]=="lib"):
        msg = "Asset namespace does not match pattern: XX_assetName_rigging_lib \nCurrent name: %s"%(assetNamespace)
        mayaWarning(msg)
        sys.exit(msg)
    #Get the asset name
    try:
        assetName = assetNamespace.split("_")[0]+"_"+assetNamespace.split("_")[1] # "ch_asset" - Raise an error if [1] list index out of range
    except:
        msg = "%s is not matching the pattern: XX_assetName_XX:geoName"%(currentSelection)
        mayaWarning(msg)
        sys.exit(msg)

    assetDir = os.path.join(assetsDir,assetName)
    #Check if the asset dir exists
    if not os.path.exists(assetDir):
        msg = "Asset folder not found!\n%s \nIssue can come from: \n -Naming pattern of referenced rig: %s \n -Folder tree"%(assetDir,assetNamespace)
        mayaWarning(msg)
        sys.exit(msg)

    assetAbcDir = os.path.join(assetDir, "abc", )
    # Create abc Directory if don't exist
    if not os.path.exists(assetAbcDir):
        os.mkdir(assetAbcDir)
        print("Directory " , assetAbcDir ,  " Created ")
    else:
        print("Directory " , assetAbcDir ,  " already exists")

    #Check is scene is save.
    confirm = "Yes"
    if cmds.file(q=True,anyModified=True):
        confirm = cmds.confirmDialog( title='Shading scene creation',
                                    message='Shading scene creation ready to start... \nThe current scene is not save. Continue ?',
                                    button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No'
                                    )
    if confirm == "No":
        msg = "Scene not save. \nAbort by user."
        mayaWarning(msg)
        sys.exit(msg)
    #CHECK IF FILE NOT ALREADY EXIST
    #Check abc
    num ="00" #Base number
    abcName = "%s_%s.abc"%(assetName,num)
    abcPath = os.path.join(assetAbcDir,abcName)
    if os.path.isfile(abcPath):  #Check if the abc file doesn't already exist
        msg = "File already exist! \n%s\nDelete or rename the existing file manually.\nCan't ovewrite, not safe... "%(abcPath)
        mayaWarning(msg)
        sys.exit(msg)
    #Check shading
    assetShadingPath = os.path.join(assetDir,"%s_shading_lib.mb"%(assetName))
    if os.path.isfile(assetShadingPath):  #Check if the shading file doesn't already exist
        msg = "File already exist! \n%s\nDelete or rename the existing file manually.\nCan't ovewrite, not safe... "%(assetShadingPath)
        mayaWarning(msg)
        sys.exit(msg)
    #Check asset data
    assetDataPath = os.path.join(assetsDbDir,assetName+".txt" ) #Build .txt path
    if not os.path.exists(assetsDbDir):
        msg="%s doesn't exist !\n ... "%(assetsDbDir)
        mayaWarning(msg)
        sys.exit(msg)
    if os.path.isfile(assetDataPath):  #Check if the file already exist
        msg="%s already exist !\nCan't ovewrite, not safe... "%(assetDataPath)
        mayaWarning(msg)
        sys.exit(msg)
    #END CHECK

    result = cmds.promptDialog(
                title='Custom attribut',
                message='Add custom attribut? If none, leave blank. \nSplit attribut with comma ","',
                button=['OK'],
                defaultButton='OK',
                dismissString='Cancel')
    attrString = cmds.promptDialog(query=True, text=True)
    attrList = attrString.split(",")

    exportAbc(abcPath, currentSelection, attrList) # Export the alembic and get the path
    createShadingScene(assetShadingPath, assetName, abcPath)
    assetData = buildAssetData(assetName,currentSelection,assetShadingPath, attrList)
    writeAssetData(assetData,assetName,assetsDbDir)

def buildAssetData(name, currentSelection, assetShadingPath, attrList):
    """
    Create a dictionnary with information about the asset:
    Name, Geometry list, Attributs list, Shading scene path
    """
    name = name
    geoList=[]
    geoList = currentSelection  #Get the current selected geometry in a list
    rig = currentSelection[0].split(":")[0]  #Get the rig namespace

    assetData = {"name":name,"geo":geoList,"rig":rig,"attr":attrList,"shading":assetShadingPath}
    return assetData

def createShadingScene(assetShadingPath, assetName, abcPath):
    cmds.file(f=True, new=True)
    cmds.file( abcPath, r=True, type="Alembic", namespace=assetName)
    cmds.file( rename=assetShadingPath )
    cmds.file( save=True, type='mayaBinary')

def writeAssetData(assetData,assetName,assetsDbDir):
    """
    Create a .txt with information about the asset.
    """
    assetDataPath = os.path.join(assetsDbDir,assetName+".txt" ) #Build .txt path

    if os.path.isfile(assetDataPath):  #Check if the file already exist
        mayaWarning('%s already exist !'%(assetDataPath))
    else:
        try:
            with open(assetDataPath,'w') as outfile:
                json.dump(assetData,outfile)
            #"f= open(assetDataPath,"w+")
            #f.write(json.dumps(assetData))  #Write the .txt with asset data
        except IOError:
            print("File not accessible")
            raise

    return
