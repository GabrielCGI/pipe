import maya.cmds as cmds
import maya.mel as mel
imgFilePrefix = "<RenderLayer>/<Scene>/<Scene>"
def setImgFilePrefix():
    #Image file prefix
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", imgFilePrefix, type="string")
    mel.eval('setMayaSoftwareFrameExt("3", 0);')
    cmds.setAttr("defaultRenderGlobals.endFrame", 240)



    cmds.setAttr("defaultResolution.aspectLock", 0)
    cmds.setAttr("defaultResolution.width", 1920)
    cmds.setAttr("defaultResolution.height", 1080)
