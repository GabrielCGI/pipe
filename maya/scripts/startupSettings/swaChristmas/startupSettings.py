import maya.cmds as cmds
import pymel.core as pm
import assetBrowser




def run():
    cmds.currentUnit(time='film')  # film: 24 fps, pal: 25 fps, ntsc: 30 fps
    cmds.currentUnit(linear='cm')

    # VIRUS SECURITY TOOL
    print("LOADING MAYA SECURITY TOOL... ")
    cmds.loadPlugin("MayaScanner.py")
    cmds.pluginInfo("MayaScanner.py", edit=True, autoload=True)

    cmds.loadPlugin("MayaScannerCB.py")
    cmds.pluginInfo("MayaScannerCB.py", edit=True, autoload=True)
    #SET AUTO Save to on

    # HACK TO FORCE PLUGIN PREFS AUTOLOADING

    cmds.evalDeferred(
        'for plug in ["bifmeshio.mll","bifrostGraph.mll","bifrostshellnode.mll","bifrostshellnode.mll","bifrostvisplugin.mll","Turtle.mll" ]:  cmds.pluginInfo(plug, edit=True, autoload=False ) if cmds.pluginInfo(plug, query=True, autoload=True) else print("Already no autoload: "+plug) ; cmds.pluginInfo(savePluginPrefs=True)',
        lp=True)


    try:
        ui.deleteLater()
    except:
        pass
    ui = assetBrowser.AssetBrowser()
    ui.create()
    ui.show()
    print("SETTING AUTO SAVE TO ON")
    #cmds.evalDeferred('cmds.autoSave(enable=True)')
    #cmds.evalDeferred('cmds.autoSave(limitBackups=True)')
    #cmds.evalDeferred('cmds.autoSave(maxBackups=5)')
    cmds.file(modified=False)
