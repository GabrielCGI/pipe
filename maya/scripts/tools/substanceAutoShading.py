import maya.cmds as cmds
import glob

"""
HOW TO USE
1)Select the object
2)Run the script
3)Select a folder with exported substance maps
Done.

Substance auto shading v0.1
Bloom Pictures Tools
"""

# Textures folder

def autoShading():
    chosenFolder = cmds.fileDialog2(dialogStyle=2, fileMode=2,)
    texPath = chosenFolder[0]
    templateShader = {
    "color" : "BaseColor",
    "specRoughness" : "Roughness",
    "specular" : 0.7,
    "metalness" : "Metalness",
    "displace" : "Height",
    "aiDisplacementZeroValue" : 0,
    "aiSubdivIterations" : 2,
    "Normal" : "Normal",
    }
    format = ".exr"

    # Scan for all textures by matching pattern
    colorTexAll = glob.glob(texPath+"\\*BaseColor*"+format)
    roughnessTexAll = glob.glob(texPath+"\\*Roughness*"+format)
    metalnessTexAll = glob.glob(texPath+"\\*Metalness*"+format)
    normalTexAll = glob.glob(texPath+"\\*Normal*"+format)
    displaceTexAll = glob.glob(texPath+"\\*Height*"+format)

    # Keep only the first occurence (if more than one it's mean there is UDIM)
    colorTexPath = colorTexAll[0]
    specRoughTexPath = roughnessTexAll[0]
    metalnessTexPath =metalnessTexAll[0]
    normalTexPath = normalTexAll[0]
    displaceTexPath = displaceTexAll[0]

    #Get selection
    selection = cmds.ls(sl=True)

    #Create shaders (color & displace)
    s = selection[0]
    shader = cmds.shadingNode ("aiStandardSurface", asShader=True, name="%sShader"%s)
    dispShader = cmds.shadingNode("displacementShader", asShader=True, name="%sDisplace"%s)

    #Set shaders
    cmds.setAttr("%s.aiDisplacementZeroValue" % dispShader, templateShader["aiDisplacementZeroValue"] )
    cmds.setAttr("%s.aiDisplacementAutoBump" % dispShader, 1)
    cmds.setAttr("%s.specular" % shader, templateShader["specular"] )
    cmds.setAttr("%s.base" % shader, 1)

    #Create textures & Connect
    ##########################
    #### Color ####
    colorTex = cmds.shadingNode("file", asTexture=True, name="%s_color" % s)
    cmds.setAttr("%s.fileTextureName" % colorTex , colorTexPath, type="string")
    if len(colorTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % colorTex , 3) #set to udim

    #Connect
    cmds.connectAttr("%s.outColor" %colorTex, "%s.baseColor" %shader)

    #### Displacement ####
    dispTex = cmds.shadingNode("file", asTexture=True, name="%s_disp" %s)
    cmds.setAttr("%s.fileTextureName" % dispTex, displaceTexPath, type="string")
    if len(displaceTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % dispTex , 3)

    #Connect
    cmds.connectAttr("%s.outColor.outColorR" %dispTex, "%s.displacement" % dispShader)

    #### Specular Roughness ####
    specRoughnessTex = cmds.shadingNode("file", asTexture=True, name="%s_specRoughness" % s)
    cmds.setAttr("%s.alphaIsLuminance" % specRoughnessTex, 0) #Tick Alpah is Luminance
    cmds.setAttr("%s.fileTextureName" % specRoughnessTex, specRoughTexPath, type="string")
    if len(roughnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % specRoughnessTex , 3) #set to udim

    #Connect
    cmds.connectAttr("%s.outColor.outColorR" % specRoughnessTex, "%s.specularRoughness" %shader)

    #Metalness
    metalTex = cmds.shadingNode("file", asTexture=True, name="%s_metalness" % s)
    cmds.setAttr("%s.fileTextureName" % metalTex, metalnessTexPath, type="string")
    if len(metalnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % metalTex , 3) #set to udim

    #Connect
    cmds.connectAttr("%s.outColor.outColorR" %metalTex, "%s.metalness" %shader)

    #Normal
    NormalTex = cmds.shadingNode("file", asTexture=True, name="%s_Normal" % s)
    aiNormalMap = cmds.shadingNode("aiNormalMap", asTexture=True, name="%s_aiNormalMap" % s)
    cmds.setAttr("%s.fileTextureName" % NormalTex, normalTexPath, type="string")
    if len(normalTexAll) >= 2:cmds.setAttr("%s.uvTilingMode" % NormalTex , 3)  #set to udim

    #Connect
    cmds.connectAttr("%s.outColor" %NormalTex, "%s.input" %aiNormalMap)
    cmds.connectAttr("%s.outValue" %aiNormalMap, "%s.normalCamera" %shader)

    #Create shading group & Assign
    shadingGroup = cmds.sets(name="%sSG" % shader, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % shadingGroup)                #color
    cmds.connectAttr("%s.displacement" % dispShader, "%s.displacementShader" % shadingGroup)   #displacement

    for obj in selection:

        #Arnold Subdivision attribut object
        cmds.setAttr("%s.aiSubdivType" % obj, 1)
        cmds.setAttr("%s.aiSubdivIterations" % obj, templateShader["aiSubdivIterations"])
        cmds.sets(obj, e=True, forceElement= shadingGroup)
autoShading()
