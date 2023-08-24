#! usr/bin/python
# -*- coding: ISO-8859-1 -*-
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
import importlib
importlib.reload(projects)



# Project variable initialisation
assetsDbDir = os.getenv("CURRENT_PROJECT_DIR")+"/assets/_database"#Something like B:\Teaser\assets\database #HACK paradise usually
assetsDir = os.getenv("CURRENT_PROJECT_DIR")+"/assets" #Something like B:\Teaser\assets

def mayaWarning(msg):
    """
    Display of maya warning
    """
    cmds.warning(msg)
    cmds.confirmDialog(title="Error",message=msg)



def createNewAsset():
    """
    Main function that drive the export
    """

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
    if not (split[-2]=="rigging"):
        msg = "Assets namespace does not match pattern: XX_assetName_rigging_lib \nCurrent name: %s"%(assetNamespace)
        mayaWarning(msg)
        sys.exit(msg)
    #Get the asset name
    try:
        if len(split)==4:  #HACK PARADISE
            assetName = assetNamespace.split("_")[0]+"_"+assetNamespace.split("_")[1] # "ch_asset" - Raise an error if [1] list index out of range
        if len(split)==3:
            assetName = assetNamespace.split("_")[0]
    except:
        msg = "%s is not matching the pattern: XX_assetName_XX:geoName"%(currentSelection)
        mayaWarning(msg)
        sys.exit(msg)
    if len(split)==4:
        assetDir = os.path.join(assetsDir,assetName)
    if len(split)==3:
        assetDir = os.path.join(assetsDir,"animProps",assetName)
    #Check if the asset dir exists
    if not os.path.exists(assetDir):
        msg = "Asset folder not found!\n%s \nIssue can come from: \n -Naming pattern of referenced rig: %s \n -Folder tree"%(assetDir,assetNamespace)
        mayaWarning(msg)
        sys.exit(msg)

    #Check asset data
    assetTxt = assetName+'.txt'
    print("assetDbDir"+assetsDbDir)

    assetDataPath = os.path.join(assetsDbDir,assetTxt) #Build .txt path

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

    assetShadingPath=""
    assetData = buildAssetData(assetName,currentSelection,assetShadingPath, attrList)
    writeAssetData(assetData,assetName,assetsDbDir)
    cmds.confirmDialog(title="it's worked",message="Succes !")

def buildAssetData(name, currentSelection, assetShadingPath, attrList):
    """
    Create a dictionnary with information about the asset:
    Name, Geometry list, Attributs list, Shading scene path
    """
    name = name
    geoList=[]
    geoList = currentSelection  #Get the current selected geometry in a list
    rig = currentSelection[0].split(":")[0]  #Get the rig namespace

    assetData = {"name":name,"geo":geoList,"rig":rig,"attr":"","shading":""}
    return assetData


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
createNewAsset()
