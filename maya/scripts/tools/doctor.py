"""

delete camera
optimize scene size
proxify
file gamma mode
hiearchy groupz = geo or rig or bs
polycount
number of object.
"""
import maya.mel as mel
import maya.cmds as cmds
report = {}
maxObj = 10

def mayaWarning(msg):
    """
    Display of maya warning
    """
    cmds.warning(msg)
    cmds.confirmDialog(title="Error",message=msg)

def maxNumObject():
    #Select all geometry
    objs = cmds.ls(geometry=True)
    #If there is more geometry in the scene than maxObj then raise an error
    if len(objs)>=maxObj:
        mayaWarning("There is %s object in the scene. You should combine some together"%str(len(objs)))


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

class FileTex:

    def __init__(self, name, path, colorSpace):

        self.name = name
        self.path = path
        self.colorSpace = colorSpace

def cleanUpScene():
    mel.eval("cleanUpScene 1;")

def getBadColorSpaceTex():
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
        colorSpaceList.append("Skip")
        confirm = cmds.confirmDialog( title='Color space conflict', message='%s\nTextures is referenced multiple time with different color space!\nOveride with: '%(key), button=colorSpaceList, defaultButton='Yes', cancelButton='Skip', dismissString='Skip' )
        if confirm is not "Skip":
            print (confirm)
            for file in dict[key]["files"]:
                cmds.setAttr(file.name+".colorSpace", confirm, type="string")
        else:
            print(("Skip %s"%(key)))

badColorSpaceTex = getBadColorSpaceTex()

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

def acesConvert():
    textures_file = cmds.ls(type="file") #List all textures
    listFile=[]
    colorSpaceKnown = ["Utility - Raw", "Utility - sRGB - Texture", "Utility - Linear - sRGB", "Raw", "sRGB","scene-linear Rec.709-sRGB","scene-linear Rec 709/sRGB" "ACEScg", ] #Authorized color space
    #Create a list of FileTex object with name and colorspace
    for tex in textures_file:
        texFile = FileTex(tex, cmds.getAttr(tex+".fileTextureName"), cmds.getAttr(tex+".colorSpace"))
        listFile.append(texFile)
    count = 0
    for f in listFile:
        #Check if the colorspace is not authorized
        if f.colorSpace not in colorSpaceKnown:
            # Create list of standard colorspace to replace unknown color space
            colorSpaceList = ["Raw","sRGB"]
            colorSpaceList.append("Skip")
            #Create a warning to let the user select the standard colorspace
            confirm = cmds.confirmDialog( title='Color space unknown', message='Unknown colorspace: %s\n\n Overide with:'%(f.colorSpace), button=colorSpaceList, defaultButton='Yes', cancelButton='Skip', dismissString='Skip' )
            if confirm is not "Skip":
                print("Change %s from %s to %s - %s"%(f.name,f.colorSpace,confirm, f.path))
                cmds.setAttr(f.name+".colorSpace", confirm, type="string")
                count += 1
            else:
                print("Skip %s"%(f.name))
        elif f.colorSpace == "Utility - Raw":
            print("Convert %s : Utility - Raw to Raw - %s"%(f.name,f.path))
            cmds.setAttr(f.name+".colorSpace", "Raw", type="string")
            count += 1
        elif f.colorSpace == "Utility - sRGB - Texture":
            print("Convert %s : Utility - sRGB - Texture to sRGB - %s"%(f.name,f.path))
            cmds.setAttr(f.name+".colorSpace", "sRGB", type="string")
            count += 1
        elif f.colorSpace == "Utility - Linear - sRGB":
            print("Convert %s : Utility - Linear - sRGB to scene-linear Rec.709-sRGB - %s"%(f.name,f.path))
            cmds.setAttr(f.name+".colorSpace", "scene-linear Rec.709-sRGB", type="string")
            count += 1
    cmds.warning("%s corrected !"%(count))




#Create my GUI
def createGUI():
    #window set up
    winWidth = 600
    winName = "doctorWindow"
    if cmds.window(winName, exists=True):
      cmds.deleteUI(winName)
    doctorWindow = cmds.window(winName,title="Doctor", width=winWidth, rtf=True)
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 10)
    cmds.text( label='Doctor',font='boldLabelFont')
    cmds.checkBox("texColorSpace", label="Texture with different color space", value=True)
    cmds.checkBox("acesConvert", label="Aces 2.0 converter", value=True)
    cmds.checkBox("optimize", label="Optimize scene size", value=True)
    cmds.checkBox("cam", label="Delete extra camera", value=True)
    #cmds.checkBox("numObject", label="Objet Numbers", value=True)
    cmds.checkBox("deleteUnknown", label="Delete Unknown node", value=True)
    cmds.checkBox("deleteXg", label="Delete Xgen expression", value=False)
    cmds.button( label='Run', width= 224, command=lambda x:doctor())

    cmds.showWindow(winName)


createGUI()

#query checkboxes
def doctor():
    if cmds.checkBox("texColorSpace", query = True, value =True):
        badColorSpaceTex = getBadColorSpaceTex()
        fixColorSpace(badColorSpaceTex)

    if cmds.checkBox("optimize", query = True, value =True):
        cleanUpScene()

    if cmds.checkBox("cam", query = True, value =True):
        delCamera()
    if cmds.checkBox("acesConvert", query = True, value =True):
        acesConvert()
    #if cmds.checkBox("numObject", query = True, value =True):
    #    maxNumObject()

    if cmds.checkBox("deleteUnknown", query = True, value =True):
        deleteUnknown()

    if cmds.checkBox("deleteXg", query = True, value =True):
        deleteXg()

    mayaWarning("Test finished.")
