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
import importlib
import doctor_utils as doc
importlib.reload(doc)

report = {}
maxObj = 10

def mayaWarning(msg):
    """
    Display of maya warning
    """
    cmds.warning(msg)
    cmds.confirmDialog(title="Error",message=msg)

#Create my GUI
def createGUI():
    #window set up
    winWidth = 450
    winName = "doctorWindow"
    if cmds.window(winName, exists=True):
      cmds.deleteUI(winName)
    doctorWindow = cmds.window(winName,title="Doctor", width=winWidth, rtf=True)
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 10)
    cmds.text( label='Doctor',font='boldLabelFont')
    cmds.checkBox("texColorSpace", label="Check Texture colorspace", value=True)
    cmds.checkBox("optimize", label="Optimize scene size", value=True)
    cmds.checkBox("deleteUnknown", label="Delete Unknown node", value=True)
    cmds.checkBox("unknownPlugin", label="Remove Unknown Plugins", value=True)
    cmds.checkBox("delHistory", label="Delete Deformer History", value=False)
    cmds.checkBox("cam", label="Delete extra camera", value=False)
    #Remove CgAbBlastPanel Error because of a missing plugin that keep raising errors.
    cmds.checkBox("remove_CgAbBlastPanel", label="Remove CgAbBlastPanel Error", value=False)
    #cmds.checkBox("numObject", label="Objet Numbers", value=True)

    #cmds.checkBox("deleteXg", label="Delete Xgen expression", value=False)
    cmds.button( label='Run', width= 200, command=lambda x:doctor())

    cmds.showWindow(winName)

#query checkboxes
def doctor():
    if cmds.checkBox("deleteUnknown", query = True, value =True):
        doc.deleteUnknown()

    if cmds.checkBox("unknownPlugin", query = True, value =True):
        doc.unknownPlugin()

    if cmds.checkBox("remove_CgAbBlastPanel", query = True, value =True):

        doc.remove_CgAbBlastPanelOptChangeCallback()
    if cmds.checkBox("texColorSpace", query = True, value =True):

        doc.fixcolorSpaceUnknown()
        badColorSpaceTex = doc.getBadColorSpaceTex()
        doc.fixColorSpace(badColorSpaceTex)

    if cmds.checkBox("optimize", query = True, value =True):
        doc.cleanUpScene()

    if cmds.checkBox("delHistory", query = True, value =True):
        doc.delHistory()

    if cmds.checkBox("cam", query = True, value =True):
        doc.delCamera()

    #if cmds.checkBox("numObject", query = True, value =True):
    #    maxNumObject()



    #if cmds.checkBox("deleteXg", query = True, value =True):
    #    deleteXg()

    mayaWarning("Test finished.")
