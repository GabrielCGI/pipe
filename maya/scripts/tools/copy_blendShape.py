import maya.cmds as cmds
sel = cmds.ls(selection=True)

sel2 = cmds.ls(selection=True)

print(sel)
print(sel2)

for s in sel:
    print(s)
    s_strip=s.split(":")[-1]
    cmds.select(s, add=True )
    cmds.select(s_strip)
    
    bs= cmds.blendShape()
    print((bs[0]+"."+s_strip))
    cmds.setAttr(bs[0]+"."+s_strip,1)

