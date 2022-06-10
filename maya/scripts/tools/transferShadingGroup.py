import maya.cmds as cmds


# 1-SELECT THE TOP GROUP OF THE GEO WITH SHADERS 
# 2-SELECT TOP GROUP OF THE GEO WITHOUT SHADERS
#Note: both geo have to have namesapce
#Name must match

def transferShaders():
    sel = cmds.ls(selection=True)
    print(sel)
    
    geoOld =  cmds.listRelatives( sel[0], allDescendents=True )
    geoNew = cmds.listRelatives( sel[-1], allDescendents=True )
    namespaceNew  = sel[-1].split(":")[0]
    
    for geo in geoOld:
        match =namespaceNew+":"+geo.split(":")[-1]
        cmds.select(geo)
        cmds.select(match, add=True)
        if cmds.objectType(geo, isType='mesh' ):
            traceSets= cmds.getAttr(geo+".trace_sets")
            cmds.setAttr(match+".trace_sets",traceSets, type="string")
        cmds.transferShadingSets( sampleSpace=1 )