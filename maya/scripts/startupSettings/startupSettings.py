import maya.cmds as cmds
import pymel.core as pm
import assetBrowser
import webbrowser




def run():
    cmds.currentUnit(time='pal')  # film: 24 fps, pal: 25 fps, ntsc: 30 fps


    print("LOADING MAYA SECURITY TOOL... ")
    cmds.loadPlugin("MayaScanner.py")
    cmds.pluginInfo("MayaScanner.py", edit=True, autoload=True)

    cmds.loadPlugin("MayaScannerCB.py")
    cmds.pluginInfo("MayaScannerCB.py", edit=True, autoload=True)

    # HACK TO FORCE PLUGIN PREFS AUTOLOADING
    url = "https://illogic-studios.cg-wire.com/"  # Replace with your desired URL
    webbrowser.open(url)
	
	


    cmds.evalDeferred(
        'for plug in ["bifmeshio.mll","bifrostGraph.mll","bifrostshellnode.mll","bifrostshellnode.mll","bifrostvisplugin.mll","Turtle.mll" ]:  cmds.pluginInfo(plug, edit=True, autoload=False ) if cmds.pluginInfo(plug, query=True, autoload=True) else print("Already no autoload: "+plug) ; cmds.pluginInfo(savePluginPrefs=True)',lp=True)

    cmds.evalDeferred('cmds.currentUnit(time=\'pal\')', lp=True)
    cmds.evalDeferred('cmds.currentUnit(linear=\'cm\')', lp=True)
    cmds.evalDeferred('cmds.file(modified=False)', lp=True)
    cmds.file(modified=False)
