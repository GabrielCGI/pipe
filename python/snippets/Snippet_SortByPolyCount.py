import maya.cmds as cmds
# List all geometry shape and sort by polycount
dic={}
sel = cmds.ls(type="geometryShape")
for s in sel:
    cmds.select(s, r=True)
    pCount = cmds.polyEvaluate(face=True)
    dic[s] = pCount

for key, value in sorted(dic.iteritems(), key=lambda(k,v):(v,k)):
    print "%s: %s" % (key, value)