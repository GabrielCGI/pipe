import maya.cmds as cmds

def run():
	#Unit
	cmds.currentUnit( time='pal' )  #film: 24 fps, pal: 25 fps, ntsc: 30 fps
	print "FPS = 25FPS"
	cmds.currentUnit( linear='cm' )
	print "UNIT = cm"
