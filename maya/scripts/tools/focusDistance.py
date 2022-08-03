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
    print("trung")
    try:
        print("tryin!")
        expression = "%s.aiApertureSize= %s.focalLength/10/%s.fStop/2;"%(cam[0],cam[0],cam[0])
        cmds.expression(s=expression)
    except:
        print("azzaaa")
    #Create locator for focus
    if not cmds.objExists('focus_locator_%s'%(cam[0])):
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

        cmds.connectAttr (distanceNode+".distance", cam[0]+".focusDist", f=True)
    #CONNECT FOCUS DIST ARNOLD TO LENTIL FOCUS DIST

        cmds.connectAttr (cam[0]+".aiFocusDistance", cam[0]+".focusDist", f=True)
        print ("Lentil focus distance connected !")

            #connect apperture size to fstop

            #connect apperture size to fStop (lentil)
        cmds.connectAttr(cam[0]+".fStop", cam[0]+".fstop", f=True)
            #connect focal length to focal length lentil
        cmds.connectAttr(cam[0]+".focalLength", cam[0]+".focalLengthLentil", f=True)

    else:
        print("DELETE focus_locator_%s FIRST !"%(cam[0]))







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
