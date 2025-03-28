import maya.cmds as cmds
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as om
import assetBrowser


def switch_renderer():
    om.MGlobal.executeCommand("setRendererAndOverrideInModelPanel $gViewport2 arnoldViewOverride modelPanel4")
    pm.refresh()
    pm.mel.evalDeferred("setRendererInModelPanel $gViewport2 \"modelPanel4\";")


def run():
    cmds.currentUnit(time='pal')  # film: 24 fps, pal: 25 fps, ntsc: 30 fps
    cmds.currentUnit(linear='cm')

    # VIRUS SECURITY TOOL
    print("LOADING MAYA SECURITY TOOL... ")
    cmds.loadPlugin("MayaScanner.py")
    cmds.pluginInfo("MayaScanner.py", edit=True, autoload=True)

    cmds.loadPlugin("MayaScannerCB.py")
    cmds.pluginInfo("MayaScannerCB.py", edit=True, autoload=True)

    # HACK TO FORCE PLUGIN PREFS AUTOLOADING

    cmds.evalDeferred(
        'for plug in ["bifmeshio.mll","bifrostGraph.mll","bifrostshellnode.mll","bifrostshellnode.mll","bifrostvisplugin.mll","Turtle.mll" ]:  cmds.pluginInfo(plug, edit=True, autoload=False ) if cmds.pluginInfo(plug, query=True, autoload=True) else print("Already no autoload: "+plug) ; cmds.pluginInfo(savePluginPrefs=True)',
        lp=True)

    pm.scriptJob(runOnce=True, e=["idle", switch_renderer], permanent=True)

    try:
        ui.deleteLater()
    except:
        pass
    ui = assetBrowser.AssetBrowser()
    ui.create()
    ui.show()

    cmds.file(modified=False)
