import maya.mel as mel
import maya.cmds as cmds
import pymel.core as pm

report = {}
maxObj = 10

class FileTex:

    def __init__(self, name, path, colorSpace):

        self.name = name
        self.path = path
        self.colorSpace = colorSpace

def maxNumObject():
    #Select all geometry
    objs = cmds.ls(geometry=True)
    #If there is more geometry in the scene than maxObj then raise an error
    if len(objs)>=maxObj:
        mayaWarning("There is %s object in the scene. You should combine some together"%str(len(objs)))

def unknownPlugin():
    old_plug = cmds.unknownPlugin(query=True, list=True)
    if old_plug:
        for plug in old_plug:
            print("Removing:" + plug)
            try:
                cmds.unknownPlugin(plug,remove=True)
            except Exception as e:
                print(e)
    else:
        print("There is no unknown plugin in the scene !")
def delCamera():
    # Get all cameras first
    cameras = cmds.ls(type=('camera'), l=True)
    # Let's filter all startup / default cameras
    startup_cameras = [camera for camera in cameras if cmds.camera(cmds.listRelatives(camera, parent=True)[0], startupCamera=True, q=True)]
    # non-default cameras are easy to find now.
    non_startup_cameras = list(set(cameras) - set(startup_cameras))
    # Let's get their respective transform names, just in-case
    non_startup_cameras_transforms = [cmds.listRelatives(x, parent=True)[0] for x in non_startup_cameras]
    for c in non_startup_cameras_transforms:
        try:
            cmds.delete(c)
            #deleted.append(getAttr(""))
        except:
            errors["Camera %s"%(c)]="Can't delete camera"%(c)
def remove_CgAbBlastPanelOptChangeCallback():
    """
    Remove a reccuring errors raised by a missing plugings.
    """
    for model_panel in cmds.getPanel(typ="modelPanel"):

        # Get callback of the model editor
        callback = cmds.modelEditor(model_panel, query=True, editorChanged=True)

        # If the callback is the erroneous `CgAbBlastPanelOptChangeCallback`
        if callback == "CgAbBlastPanelOptChangeCallback":

            # Remove the callbacks from the editor
            cmds.modelEditor(model_panel, edit=True, editorChanged="")
    cmds.delete ("uiConfigurationScriptNode")
def cleanUpScene():
    # Source cleanUpScene.mel
    # to make scOpt_performOneCleanup available
    pm.mel.source('cleanUpScene')
    pm.mel.scOpt_performOneCleanup({
        "nurbsSrfOption",
        "setsOption",
        "transformOption",
        "renderLayerOption",
        "renderLayerOption",
        "animationCurveOption",
        "groupIDnOption",
        "unusedSkinInfsOption",
        "groupIDnOption",
        "shaderOption",
        "ptConOption",
        "pbOption",
        "snapshotOption",
        "unitConversionOption",
        "referencedOption",
        "brushOption",
        "unknownNodesOption",
        }
    )


def fixcolorSpaceUnknown():
    """
    Compare all colorspaces used in the scene with a list of authorized colorspace.
    """
    textures_file = cmds.ls(type="file") #List all textures
    listFile=[]
    colorSpaceKnown = ["Raw", "sRGB","scene-linear Rec.709-sRGB","scene-linear Rec 709/sRGB", "ACEScg", ]
    for tex in textures_file:
        texFile = FileTex(tex, cmds.getAttr(tex+".fileTextureName"), cmds.getAttr(tex+".colorSpace"))
        listFile.append(texFile)
    for f in listFile:
        #Check if the colorspace is not authorized
        if f.colorSpace not in colorSpaceKnown:
            # Create list of standard colorspace to replace unknown color space
            colorSpaceList = ["Raw","sRGB","ACEScg","scene-linear Rec.709-sRGB"]
            colorSpaceList.append("Cancel")
            #Create a warning to let the user select the standard colorspace
            confirm = cmds.confirmDialog( title='Color space unknown', message='-------------\n%s\nUnknown colorspace: %s\n------------- \n\n Overide with:'%(f.path,f.colorSpace), button=colorSpaceList, defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel' )
            if confirm is not "Cancel":
                print("Change %s from %s to %s - %s"%(f.name,f.colorSpace,confirm, f.path))
                cmds.setAttr(f.name+".colorSpace", confirm, type="string")

            else:
                print("Skip %s"%(f.name))

def getBadColorSpaceTex():
    "List all files with multiple colorSpace"
    listFile = []
    uniquePath = []
    duplicatePaths  = []
    dictionary_DiffColorSpace={}
    fileWithDuplicateColorSpace = []
    #fileWithDuplicatePath = []
    #list all texture file
    textures_file = cmds.ls(type="file")

    #Generate file object
    for tex in textures_file:
        texFile = FileTex(tex, cmds.getAttr(tex+".fileTextureName"), cmds.getAttr(tex+".colorSpace"))
        listFile.append(texFile)

    #Check if duplicate path
    for f in listFile:
        if f.path not in uniquePath:
            uniquePath.append(f.path)
        else:
            if f.path not in duplicatePaths: duplicatePaths.append(f.path)

    #Look in duplictate path
    for dp in duplicatePaths:
        listColorSpace = []
        #If a file object has a duplicate path then add to a list
        fileWithDuplicatePath = [ a for a in listFile if a.path == dp]
        #Check for duplicate color space
        for f in fileWithDuplicatePath:
            if f.colorSpace not in listColorSpace:
                listColorSpace.append(f.colorSpace)
        #If there is more than one colorspace for one file path
        if len(listColorSpace) > 1:
            #Build a dictionray by unique textures, file node using them, colorspace used.
            dictionary_DiffColorSpace[dp] = {"files":fileWithDuplicatePath, "colorSpace":listColorSpace}
    return dictionary_DiffColorSpace


def fixColorSpace(dict):
    for key in list(dict.keys()):
        colorSpaceList = [c for c in dict[key]["colorSpace"]]
        #colorSpaceList.append("Cancel")
        confirm = cmds.confirmDialog( title='Color space conflict', message='-------------\n%s\n-------------\n\nThe same texture file use multiple color space!\nPlease choose one. '%(key), button=colorSpaceList, defaultButton='Yes', cancelButton='Cancel', dismissString='Cancel' )
        if str(confirm) != "Cancel":
            for file in dict[key]["files"]:
                print(file.name +" - "+file.path + ": set colorspace " + confirm)
                cmds.setAttr(file.name+".colorSpace", confirm, type="string")
        else:
            print(("Skip %s"%(key)))



def deleteUnknown():
    print ("..................")
    print ("DELETE UNKNOWN NODES...:")

    unknown= cmds.ls(type="unknown")
    if unknown:
        print ("Unknown node found !")
        print (unknown)
        cmds.delete(unknown)
    else:
        print ("No unknown nodes found")

def deleteXg():
    xgenlists= cmds.ls("*:*xgm*","*:*:*xgm*","*xgm*")
    print ("..................")
    print ("XGEN CLEANING...")

    if len(xgenlists)>0:
        print ("Xgen found !")
        print (xgenlists)
        cmds.delete(xgenlists)
    else:
        print ("No xgen in scene")

def delHistory():
    mel.eval("DeleteAllHistory")
    print("Doctor -- Delete All History")
