import maya.cmds as cmds

def proxy(mode):
    for i in cmds.ls(selection=True):
        try:
            cmds.setAttr(i+".mode",mode)
        except:
            pass

#visibility(0) off
#visibility(6) on

#import proxyVisibility as pV
#pV.proxy(0)
#pv.proxy(6)
