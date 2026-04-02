# This script will be executed before the execution of a playblast state in the Prism State Manager.
# You can use this file to define project specific actions, like preparing your scene/viewport for the playblast.

# Example:
# print "Prism is going to create a playblast now."

# If the main function exists in this script, it will be called.
# The "args" argument is a dictionary with usefull information about Prism and the current export.

import os
import PrismInit

pcore = PrismInit.pcore
dcc = pcore.appPlugin
dcc_name = dcc.pluginName

def main(*args, **kwargs):
    if dcc_name == 'Maya':
        import maya.cmds as cmds
        import maya.mel as mel

        # clear selection
        sel = cmds.ls(selection=True)
        cmds.select(clear=True)

        # Show only polygons and plugin shapes
        for panel in cmds.getPanel(type="modelPanel"):
            cam_transform = cmds.modelEditor(panel, q=True, camera=True)
            cam_shape = cmds.listRelatives(cam_transform, shapes=True, type="camera")[0]
                
            if not "shotcam" in cam_shape.lower():    
                continue
        
            cmds.modelEditor(panel, edit=True, wireframeOnShaded=False)

            cmds.modelEditor(panel, edit=True, allObjects=False)
            cmds.modelEditor(panel, edit=True,
                        polymeshes=True,
                        pluginShapes=True)
            
            # --- store current overscan in a custom attr ---
            if not cmds.attributeQuery("storedOverscan", node=cam_shape, exists=True):
                cmds.addAttr(cam_shape, ln="storedOverscan", at="double")

            current_overscan = cmds.getAttr(cam_shape + ".overscan")
            cmds.setAttr(cam_shape + ".storedOverscan", current_overscan)

            # --- break incoming connections ---
            connections = cmds.listConnections(cam_shape + ".overscan",
                                            source=True,
                                            destination=False,
                                            plugs=True) or []

            for src in connections:
                cmds.disconnectAttr(src, cam_shape + ".overscan")

            # --- unlock if needed ---
            if cmds.getAttr(cam_shape + ".overscan", lock=True):
                cmds.setAttr(cam_shape + ".overscan", lock=False)

            # --- set overscan to 1 ---
            cmds.setAttr(cam_shape + ".overscan", 1)

            # Regenerate All UV Tile Preview Texture
            # mel.eval("generateAllUvTilePreviews;")

            # Force default lighting intensity
            mel.eval("""setAttr "hardwareRenderingGlobals.defaultLightIntensity" 1;""")