import maya.cmds as cmds


# 1-SELECT THE TOP GROUP OF THE GEO WITH SHADERS
# 2-SELECT TOP GROUP OF THE GEO WITHOUT SHADERS
#Note: both geo have to have namesapce
#Name must match




#INIT DIC
def flattenSet():
    counter=0
    """
    Using the cmds.transferShadingSets() command create set like "object.f[0:3300]""
    The set has an array with the face assigned.
    This function flatten into a simple set "objectShape" if the shader there is only one shader.
    """
    dic_sg={}

    #SELECT ALL SHADING ENGINE MINUS DEFAULT
    listShadingEngine = cmds.ls(type="shadingEngine")
    listShadingEngine.remove('initialParticleSE')
    listShadingEngine.remove('initialShadingGroup')

    #FIND ALL SHAPES OF A SHADING GROUP
    #Return a dictionary with key = sg name, value = list of shapes
    for sg in listShadingEngine:

        #GET THE SET
        set = cmds.sets(sg, query=True)
        setSimple = set
        if set:
            setSimple = [s.split(".")[0] for s in set]

        cmds.sets(setSimple, e=True, forceElement= sg)
        #BUILD A LIST OF PATH WITH FORWARD SLASH

def transferShaders() :
    fails = [""]
    sel = cmds.ls(selection=True)
    geoOld =  cmds.listRelatives( sel[0], allDescendents=True,fullPath=True )
    geoNew = cmds.listRelatives( sel[-1], allDescendents=True,fullPath=True )
    namespaceOld = sel[0].split(":")[0]
    namespaceNew  = sel[-1].split(":")[0]
    shaderDebug = cmds.shadingNode("aiStandardSurface", asShader=True, name ="debugShader")
    cmds.setAttr(shaderDebug+".baseColor",0.8,0.1,0.1)
    shadingGroup = cmds.sets(name="%sSG" % shaderDebug, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr("%s.outColor" % shaderDebug, "%s.surfaceShader" % shadingGroup)
    for geoN in geoNew:
        match = geoN.replace(namespaceNew,namespaceOld)
        if not cmds.objExists(match) and cmds.objectType(geoN, isType="mesh"):
            all_match = [f for f in geoOld if f in geoN]
            if len(all_match)>0:
                match = all_match[0]
                print("force match %s"%(match))

        if not cmds.objExists(match) and cmds.objectType(geoN, isType="mesh"):
            if "_Dup_" in geoN:
                print("it's a dup !")
                match= match.replace("_Dup_1","")
                match = match.replace("_Dup_2","")

        if not cmds.objExists(match) and cmds.objectType(geoN, isType="mesh"):
            parentNew = cmds.listRelatives(geoN, parent=True, fullPath=True)

            parentOld = parentNew[0].replace(namespaceNew,namespaceOld)
            parentOld = parentOld .replace("_Dup_1","")
            parentOld = parentOld.replace("_Dup_2","")
            if cmds.objExists(parentOld):
                matches = cmds.listRelatives(parentOld,fullPath=True, shapes=True)
                if len(matches) >0:
                    match= matches[0]
                    print("shape match from parent %s"%(match))

        if not cmds.objExists(match) and cmds.objectType(geoN, isType="mesh"):

            grossSel = cmds.ls(match.rstrip(match[-4])+"*")
            print (match.rstrip(match[-4])+"*")
            if len(grossSel)>1:
                match = grossSel[0]
                print("gross sel math:"+match)
                print("gross_sel!")

        try:
            if cmds.objectType(geoN, isType="mesh"):
                cmds.select(match)
                cmds.select(geoN,add=True)
                shadingGroup = cmds.listConnections(geoN + '.instObjGroups')[0]
                cmds.sets(geoN, remove=shadingGroup )
                cmds.transferShadingSets( sampleSpace=1 )
                print ("Transfer succeed!")
        except Exception as e:
            cmds.sets(geoN, e=True, forceElement= shadingGroup)
            print("-------------")
            print(e)
            fails.append(geoN )
            print("Transfer failed: ")
            print(geoN)
            print(match)
            print("-------------")

    print("\n ---FAILED LIST----")
    for fail in fails:
        print(fail)
    flattenSet()
