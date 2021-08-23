# Select the camera before using the script !!!
# This script allow to set the focus distance for a camera using an locator.
# The distance beewteen the "focus_distance_locator" and "the camera" is set into the aiFocusDistance attribut.
# The DOF of the maya viewport is also set accordingly.


import maya.cmds as cmds

def isCam(cam):
    """
    Check if an object is a camera
    """
    #If a camera shape was selected
    if cam:
        if cmds.objectType (cam) == "camera":
            return True
        #If a camera transform was selected
        else:
            #Get the camera shape
            camShape = cmds.listRelatives(cam, shapes=True)
            if camShape:
                if cmds.objectType (camShape)  == "camera":
                   return True
        #It's not a camra
        return False


def setFocusDistance(cam):
    "Apply focus on a camera"

    #Create locator for focus
    if cmds.objExists('focus_locator_%s'%cam[0]):
        print('focus_distance_locator_%s already exist !'%cam[0])
        cmds.delete('focus_locator_%s'%cam[0])
    focus_distance_locator = cmds.spaceLocator(n='focus_locator_%s'%cam[0])

    #Create distance Node
    distanceNode = cmds.shadingNode('distanceBetween',asUtility=True)
    #Create vectorProduct
    vectorNode = cmds.shadingNode('vectorProduct', asUtility=True)
    cmds.setAttr(vectorNode+".operation", 4)

    #Conect worldMatrix camera > vectorNode
    cmds.connectAttr (cam[0]+".worldMatrix", vectorNode+".matrix", f=True)
    #Connect distance node
    cmds.connectAttr (focus_distance_locator[0]+"Shape.worldPosition", distanceNode+".point1", f=True)
    cmds.connectAttr (vectorNode+".output", distanceNode+".point2", f=True)

    cmds.connectAttr (distanceNode+".distance", cam[0]+".aiFocusDistance", f=True)
    cmds.connectAttr (distanceNode+".distance", cam[0]+".focusDistance", f= True)
    if cmds.getAttr("defaultRenderGlobals.currentRenderer") =="vray":
        try:
            cmds.setAttr (cam[0]+".vrayCameraPhysicalUseDof", 1)
            cmds.setAttr (cam[0]+".vrayCameraPhysicalSpecifyFocus", 1)
            cmds.connectAttr (distanceNode+".distance", cam[0]+".vrayCameraPhysicalFocusDistance", f= True)
        except:
            cmds.warning("ADD VRAY PHYSICAL CAMERA !")

    #DOF viewport
    cmds.setAttr(cam[0]+".depthOfField", 1)
    #If the camera as already an expression it's would raise an error.
    try:
        cmds.expression( s="%s.fStop = 2*(%s.focalLength*0.1)/(%s.aiApertureSize + 0.01);"%(cam[0],cam[0],cam[0]), o = cam[0], ae =True,)
    except:
        print("The camera F stop as already an expression")


def focus():
    """
    Check if a camera is selected then apply focus
    """
    cam = cmds.ls(sl=True)
    if cam: #Check if something is selected
        if isCam(cam[0]): #Check if it's a camera
            setFocusDistance(cam)
        else:
            cmds.confirmDialog(message="Select a camera first.", button=["ok"])
    else:
       cmds.confirmDialog(message="Select a camera first. Nothing is selected", button=["ok"])
