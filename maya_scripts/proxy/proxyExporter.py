import os
import maya.mel as mel
import maya.cmds as cmds
path = "D:/export"
reducePercent = 90
startF = 0.0
endF = 10
sel = cmds.ls(selection=True)
for s in sel:
    proxyPath = os.path.join(path,s)
    cmds.select(s)
    exportOpt = "-shadowLinks 0;-endFrame %s;-mask 24;-lightLinks 0;-frameStep 1.0;-compressed;-boundingBox;-startFrame %s"%(endF, startF)
    cmds.file(proxyPath, force=True, options=exportOpt, type="ASS Export", pr=True, es=True)
    cmds.polyReduce(n=s+"proxy", p=reducePercent, keepQuadsWeight=0)
    melCmd = 'polyCleanupArgList 4 { "0","1","1","0","0","0","0","0","1","1","0","1e-05","0","1e-05","0","-1","0","0" };'
    mel.eval(melCmd)
    
    cmds.delete(ch = True)
    cmds.setAttr(s+".ai_translator", "procedural",  type="string")
    cmds.setAttr(s+".dso", proxyPath+".####.ass.gz", type="string")
    cmds.rename(s, s+'_proxy')
    cmds.expression( s=s+'_proxy.aiFrameNumber = frame', o=s+'_proxy' )
    cmds.expression( s=s+'_proxy.aiFrameOffset = 95', o=s+'_proxy' )
    
