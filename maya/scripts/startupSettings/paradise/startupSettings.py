
import maya.cmds as cmds
#import pymel.core as pm

"""
def killTurtle():
    try:
        pm.lockNode( 'TurtleDefaultBakeLayer', lock=False )
        pm.delete('TurtleDefaultBakeLayer')
    except:
        pass
    try:
        pm.lockNode( 'TurtleBakeLayerManager', lock=False )
        pm.delete('TurtleBakeLayerManager')
    except:
        pass
    try:
        pm.lockNode( 'TurtleRenderOptions', lock=False )
        pm.delete('TurtleRenderOptions')
    except:
        pass
    try:
        pm.lockNode( 'TurtleUIOptions', lock=False )
        pm.delete('TurtleUIOptions')
    except:
        pass
    pm.unloadPlugin("Turtle.mll")
    print "Turtle Killed"
"""



def run():
	cmds.file( modified=False )
	#cmds.currentUnit( time='pal' )  #film: 24 fps, pal: 25 fps, ntsc: 30 fps
	#print ("pal = 25FPS")
	cmds.currentUnit(linear='cm')

# HACK TO FORCE PLUGIN PREFS AUTOLOADING
cmds.evalDeferred('for plug in ["bifmeshio.mll","bifrostGraph.mll","bifrostshellnode.mll","bifrostshellnode.mll","bifrostvisplugin.mll"]:  cmds.pluginInfo(plug, edit=True, autoload=False ) if cmds.pluginInfo(plug, query=True, autoload=True) else print("Already no autoload: "+plug) ; cmds.pluginInfo(savePluginPrefs=True)',lp=True)






	#killTurtle()
