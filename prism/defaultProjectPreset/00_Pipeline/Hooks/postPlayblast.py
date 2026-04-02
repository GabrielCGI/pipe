# This script will be executed after the execution of a playblast state in the Prism State Manager.
# You can use this file to define project specific actions, like modifying the created images.

# Example:
# print "Prism has created a playblast."

# If the main function exists in this script, it will be called.
# The "kwargs" argument is a dictionary with usefull information about Prism and the current export.
import PrismInit

pcore = PrismInit.pcore
dcc = pcore.appPlugin
dcc_name = dcc.pluginName

def main(*args, **kwargs):
    if dcc_name == 'Maya':
        import maya.cmds as cmds
        import maya.mel as mel

        for panel in cmds.getPanel(type="modelPanel"):
            cam_transform = cmds.modelEditor(panel, q=True, camera=True)
            cam_shape = cmds.listRelatives(cam_transform, shapes=True, type="camera")[0]
            
            if not "shotcam" in cam_shape.lower():    
                continue

            if cmds.attributeQuery("storedOverscan", node=cam_shape, exists=True):
                stored = cmds.getAttr(cam_shape + ".storedOverscan")
                cmds.setAttr(cam_shape + ".overscan", stored)

            # Force default lighting intensity
            mel.eval("""setAttr "hardwareRenderingGlobals.defaultLightIntensity" 1;""")