import maya.cmds as cmds
import maya.mel as mel
def killTurtle():
	types = cmds.pluginInfo('Turtle.mll', dependNode=True, q=True)
	nodes = cmds.ls(type=types, long=True)

	if nodes:
    		cmds.lockNode(nodes, lock=False)
    		cmds.delete(nodes)

	cmds.flushUndo()
	cmds.unloadPlugin('Turtle.mll')
