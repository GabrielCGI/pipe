import maya.cmds as cmds
import os
import time
import shutil
import maya.mel as mel
import sys
import doctor_utils as doc
import replace_by_tx2

tasks = ["shading","fur","animation","anim","mod","modeling","model","fx","rigging","rig"]
def isInt(s):
    """
    Check if a string can be converted to int.
    """
    try:
        int(s)
        return True
    except ValueError:
        return False

def mayaWarningExit(msg):
    """
    Display of maya warning then exit the script.
    """
    cmds.warning(msg)
    cmds.confirmDialog(title="Error",message=msg)
    sys.exit(msg)

def isLib(sceneName):
    """
    Check if a maya file is a Lib (ch_assetName_lib)
    """
    try:
        if sceneName.split("_")[-1] == "lib":
            return True
        else:
            return False
    except:
        return False

def makeBackup(path):
    """
    Make a backup with time stamp in an oldLib folder
    """
    _sTargetDir = os.path.dirname(path) + '\\oldLib\\'
    sTimestamp = time.strftime("%Y-%m-%d %Hh%Mm%Ss")
    filename = os.path.basename(path)
    sTargetPath = _sTargetDir + '[' + sTimestamp + ']'+filename
    if os.path.exists(path):
        try:
            shutil.copyfile(path, sTargetPath)
            print("Backup SUCCESS")
            return True
        except IOError as io_err:
            print("%s doesn't exist. Creation !" %path)
            try:
                os.makedirs(_sTargetDir)
                shutil.copyfile(path, sTargetPath)
                print("Backup SUCCESS")
                return True
            except:
                cmds.error("Fail to backup %s" %(sTargetPath))
                return False
    else:
        return True

def wipSave():
    """
    Save a scene as WIP.
    If already a wip then only increment.
    If it is as lib then look for the last version in the corresponding WIP Folder
    and increment.
    """
    # Get the current scene path
    scenePath = cmds.file(q=True, sceneName=True)
    #Delete path, keep scene name
    fullSceneName = os.path.basename(scenePath)
    #Split scene name and extension
    sceneName, extension = os.path.splitext(fullSceneName)

    # If it is not a lib, then simply increment.
    if not isLib(sceneName):
        mel.eval('IncrementAndSave;')
        print("// Saved !")

    # If it a lib
    else:
        # Check if it match the pattern
        if not sceneName.split("_")[-2] in tasks:
            msg = "Something wrong. The task name in not:"+ str(tasks)
            mayaWarningExit(msg)
        sceneNameSplit = sceneName.split("_")
        task = sceneNameSplit[-2]
        taskDir = os.path.join(os.path.dirname(scenePath), task)
        sceneNameSplit.pop(-1)
        sep = "_"
        wipScene  = sep.join(sceneNameSplit)



        # Check if the wip directory of the task lib exist ch_asset/TASK
        if not os.path.exists(taskDir):
            confirm = cmds.confirmDialog( title="Folder doesn't exist ! ",
                                        message="%s \nFolder doens't exist. Create it ?"%(taskDir) ,
                                        button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No'
                                        )
            if confirm == "Yes":
                os.mkdir(taskDir)
            else:
                msg = "Abort by user!"
                mayaWarningExit(msg)

        #List existing file et look for the last version
        listFile = os.listdir(taskDir)
        increment = []

        for fullFile in listFile:
            #Separate the extention
            file, extension = os.path.splitext(fullFile)
            #Split name and version number  (ch_someAsset_modeling.006)
            split = file.split(wipScene+".")
            if len(split) > 0:

                if isInt(split[-1]):
                    increment.append(int(split[-1]))
        # Sort list ascending order
        increment.sort()
        #Get last version
        if len(increment)>0:
            lastVersion = increment[-1]
        else:
            lastVersion = "0000"
        # Increment last version
        if isInt(lastVersion):
            incrVersion = int(lastVersion)+1

            s = sceneNameSplit #Visually shorter
            # Build Name #ch_newName_task.006.ma
            newName = wipScene
            newName += '.%04d' % incrVersion + extension
            #Build the path to the TASK folder
            newPath = os.path.join(taskDir,newName)
            #Check if the file already exist
            if os.path.isfile(newPath ):
                msg = "File already exist! \n%s\nCan't ovewrite, not safe... "%(abcPath)
                mayaWarning(msg)
                sys.exit(msg)
            #Else, save file !
            cmds.file(rename=newPath)
            cmds.file(save=True, type="mayaBinary")
            print("Scene saved: " + newPath)
    return


def replace_references_path_with_variable():
    # Get all references in the scene
    all_references = cmds.ls(type='reference')

    for ref in all_references:
        # Skip the default reference and any reference not associated with a file
        if "sharedReferenceNode" in ref or "UNKNOWN" in ref:
            print("skip"+ref)
            continue

        ref_node = cmds.referenceQuery(ref, referenceNode=True)
        # Check if the reference is a top-level reference
        # If it has no parent reference, it's a top-level reference
        if cmds.referenceQuery(ref, parent=True, referenceNode=True) is None:
            # Get the file path of the reference
            ref_file = cmds.referenceQuery(ref, filename=True)

            # Replace "I:" with "$DISK_I" in the file path
            new_ref_file = ref_file.replace('I:', '$DISK_I')
            print ("Replaced ref path with: new_ref_file ")
            # Load the reference with the new path
            cmds.file(new_ref_file, loadReference=ref)


def libSave():
    """
    Save the file "on the spot". Make a backup in oldfile.
    If the scene is a Wip, transform as lib
    """

    wipSave()
    replace_references_path_with_variable()


    _sSourcePath = cmds.file(q=True, sceneName=True)
    # Get the current scene path
    filename = os.path.basename(_sSourcePath)
    raw_name, extension = os.path.splitext(filename)
      #make a wipSave just in case before autoclean

    if not isLib(raw_name):
        if not raw_name.split("_")[-1].split(".")[0] in tasks:
            msg = 'Something wrong. The task name in not '+ str(tasks)
            mayaWarningExit(msg)
        #Look for a lib file.
        #Get parent directory
        pardir =  os.path.abspath(os.path.join(_sSourcePath,"../.."))
        #Delete version .005
        assetName = raw_name.split(".")[0]
        libName = assetName+"_lib"+".mb"

        libpath = os.path.join(pardir,libName)
        print(libpath)
        if os.path.isfile(libpath):
            confirm = cmds.confirmDialog( title="Publish Lib?",
                                        message="%s \nPublish a new lib?" %libpath,
                                        button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No'
                                        )
            if confirm == "No":
                msg = "Abort by user"
                mayaWarningExit(msg)

        #Cleaning operation
        doc.delCamera()
        doc.cleanUpScene()
        doc.fixcolorSpaceUnknown()
        badColorSpaceTex = doc.getBadColorSpaceTex()
        doc.fixColorSpace(badColorSpaceTex)
        replace_by_tx2.all_to_tx()
        msg= "Auto cleaning the scene: Delete extra camera, Optimize scene size, Textures colorspaces checking"
        cmds.warning(msg)

        if makeBackup(libpath):
            cmds.file(rename=libpath)
            cmds.file(save=True, type="mayaBinary")
            print("// Result: %s"%(libpath))
        else:
            msg = "Save failed"
            mayaWarningExit(msg)
