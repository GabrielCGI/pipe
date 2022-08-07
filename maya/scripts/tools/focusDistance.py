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

    distanceNode = cmds.shadingNode('distanceBetween',asUtility=True)
    #Create locator for focus
    if not cmds.objExists('focus_locator_%s'%(cam[0])):
        focus_distance_locator_list = cmds.spaceLocator(n='focus_locator_%s'%cam[0])
        focus_distance_locator = focus_distance_locator_list[0]
        cmds.connectAttr (focus_distance_locator+"Shape.worldPosition", distanceNode+".point1", f=True)

    else:

        focus_distance_locator='focus_locator_%s'%(cam[0])
        print ("LOCATOR HAS BEEN FOUND ! %s"%(focus_distance_locator))
        cmds.connectAttr (focus_distance_locator+".worldPosition", distanceNode+".point1", f=True)

        #Create distance Node

        #Create vectorProduct
    vectorNode = cmds.shadingNode('vectorProduct', asUtility=True)
    cmds.setAttr(vectorNode+".operation", 4)

        #Conect worldMatrix camera > vectorNode
    cmds.connectAttr (cam[0]+".worldMatrix", vectorNode+".matrix", f=True)
        #Connect distance node

    cmds.connectAttr (vectorNode+".output", distanceNode+".point2", f=True)

    cmds.connectAttr (distanceNode+".distance", cam[0]+".aiFocusDistance", f=True)
    cmds.connectAttr (distanceNode+".distance", cam[0]+".focusDistance", f= True)

    cmds.connectAttr (distanceNode+".distance", cam[0]+".focusDist", f=True)
    #CONNECT FOCUS DIST ARNOLD TO LENTIL FOCUS DIST

    cmds.connectAttr (cam[0]+".aiFocusDistance", cam[0]+".focusDist", f=True)
    #cmds.setAttr(cam[0]+".depthOfField",1)
    list = cmds.listConnections('%s.aiApertureSize'%cam[0])
    if list == None:
        expression = "%s.aiApertureSize= %s.focalLength/10/%s.fStop/2;"%(cam[0],cam[0],cam[0])
        cmds.expression(s=expression)
    else:
        cmds.delete(list[0])
        expression = "%s.aiApertureSize= %s.focalLength/10/%s.fStop/2;"%(cam[0],cam[0],cam[0])
        cmds.expression(s=expression)
        print ("New expression aiApertureSize !")

        #connect apperture size to fstop

        #connect apperture size to fStop (lentil)

    try:
        cmds.connectAttr(cam[0]+".fStop", cam[0]+".fstop", f=True)
    except:
        cmds.warning("Failed to connect Lentil Fstop !!!")
        #connect focal length to focal length lentil
    """
    try:
        cmds.connectAttr(cam[0]+".focalLength", cam[0]+".focalLengthLentil", f=True)

    except:

        cmds.warning("Failed to connect Lentil focal Length !!!")
    """
    cmds.select(cam[0])




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
