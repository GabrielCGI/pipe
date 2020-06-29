import maya.cmds as cmds
import pymel.core as pm
 
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


def run():
	#Unit
	cmds.currentUnit( time='film' )  #film: 24 fps, pal: 25 fps, ntsc: 30 fps
	print "FPS = 24FPS"
	cmds.currentUnit( linear='cm' )
	print "UNIT = cm"
	killTurtle()