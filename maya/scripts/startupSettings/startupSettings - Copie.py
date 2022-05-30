import maya.cmds as cmds
import pymel.core as pm

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
            print("CgAbBlastPanel error removed at startup!")
            cmds.modelEditor(model_panel, edit=True, editorChanged="")
    cmds.delete ("uiConfigurationScriptNode")

def run():
    #cmds.currentUnit( time='pal' )  #film: 24 fps, pal: 25 fps, ntsc: 30 fps
    #print("time = pal 25FPS")
    cmds.currentUnit(linear='cm')
    print("unit = cm")
    remove_CgAbBlastPanelOptChangeCallback()

    # HACK TO FORCE PLUGIN PREFS AUTOLOADING
    #cmds.evalDeferred('for plug in ["bifmeshio.mll","bifrostGraph.mll","bifrostshellnode.mll","bifrostshellnode.mll","bifrostvisplugin.mll","Turtle.mll" ]:  cmds.pluginInfo(plug, edit=True, autoload=False ) if cmds.pluginInfo(plug, query=True, autoload=True) else print("Already no autoload: "+plug) ; cmds.pluginInfo(savePluginPrefs=True)',lp=True)

    cmds.file( modified=False )



