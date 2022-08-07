import maya.cmds as cmds
import pymel.core as pm



def run():
    cmds.currentUnit( time='pal' )  #film: 24 fps, pal: 25 fps, ntsc: 30 fps
    print("time = pal 25FPS")
    cmds.currentUnit(linear='cm')
    print("unit = cm")



    # HACK TO FORCE PLUGIN PREFS AUTOLOADING
    cmds.evalDeferred('for plug in ["bifmeshio.mll","bifrostGraph.mll","bifrostshellnode.mll","bifrostshellnode.mll","bifrostvisplugin.mll","Turtle.mll" ]:  cmds.pluginInfo(plug, edit=True, autoload=False ) if cmds.pluginInfo(plug, query=True, autoload=True) else print("Already no autoload: "+plug) ; cmds.pluginInfo(savePluginPrefs=True)',lp=True)
    cmds.evalDeferred('cmds.setAttr(setAttr "defaultArnoldRenderOptions.renderUnit", 7)')
    print("Arnold render unit = cm")
    cmds.file( modified=False )
