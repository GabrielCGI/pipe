from os import listdir
from os.path import isfile, join
import pprint
pp = pprint.PrettyPrinter(indent=4)
# Path to the folder
path = "B:\\trashtown_2112\\assets\\junkpack\\Urban_Junk_And_Trash_Collection_HD\\"

#Init Assets dic


#Template
mapTypes = ["Diffuse","Normal","Reflection","Glossiness","Height","ior"]

templateShader ={
    "color" : "BaseColor",
    "specRoughness" : "Roughness",
    "specular" : 0.7,
    "metalness" : "Metalness",
    "displace" : "Height",
    "aiDisplacementZeroValue" : 0,
    "aiSubdivIterations" : 2,
    "Normal" : "Normal"}

format = ".exr"

def buildAllAssetsDic():
    allAssetsDic = {}
    #List all files
    files = [f for f in listdir(path) if isfile(join(path, f))]

    #Build maps dictionary for all assets found
    for f in files:
        #check if there is a map keyword (diffuse, roughness, etc...)
        for mapType in mapTypes:
            if mapType in f:
                #Get the name of the asset
                assetName = f.split(mapType)[0]
                #Check if the asset already exist in the allAssetsDic
                if assetName in allAssetsDic :
                    shadingDic = allAssetsDic[assetName]
                    shadingDic[mapType]=f
                else:
                    shadingDic = {}
                    shadingDic[mapType]=f
                    allAssetsDic[assetName] = shadingDic
    pp.pprint(allAssetsDic)
    return allAssetsDic

def createShader(asset,shadingDic):


    try:
        colorTexPath = os.path.join(path + shadingDic["Diffuse"])
    except:
        print("no diffuse:"+asset)
        colorTexPath=""
    try:
        reflectionTexPath = os.path.join(path + shadingDic["Reflection"])
    except:
        print("no reflection:"+asset)
        reflectionTexPath=""
    #specRoughTexPath = os.path.join(path + shadingDic["Diffuse"])
    try:
        specGlossTexPath = os.path.join(path + shadingDic["Glossiness"])
    except:
        print("no gloss:"+asset)
        specGlossTexPath=""
    #metalnessTexPath = os.path.join(path + shadingDic["Diffuse"])
    try:
        normalTexPath = os.path.join(path + shadingDic["Normal"])
    except:
        print("no normal:"+asset)
        normalTexPath=""
    try:
        iorTexPath = os.path.join(path + shadingDic["ior"])
    except:
        print("no ior:"+asset)
        iorTexPath=""
    try:
        displaceTexPath = os.path.join(path + shadingDic["Height"])
    except:
        displaceTexPath =""
        print("no dispalce" + asset)
    shader = cmds.shadingNode ("aiStandardSurface", asShader=True, name="%sShader"%asset)
    dispShader = cmds.shadingNode("displacementShader", asShader=True, name="%sDisplace"%asset)

    #Set shaders
    cmds.setAttr("%s.aiDisplacementZeroValue" % dispShader, templateShader["aiDisplacementZeroValue"] )
    cmds.setAttr("%s.aiDisplacementAutoBump" % dispShader, 1)
    cmds.setAttr("%s.specular" % shader, templateShader["specular"] )
    cmds.setAttr("%s.base" % shader, 1)

    #Create textures & Connect
    ##########################
    #### Color ####

    colorTex = cmds.shadingNode("file", asTexture=True, name="%s_color" % asset)
    reflectionTex = cmds.shadingNode("file", asTexture=True, name="%s_reflection" % asset)
    addcolorTex = cmds.shadingNode("aiAdd", asTexture=True, name="%s_aiAddColor" % asset)
    blendcolorTex = cmds.shadingNode("blendColors", asTexture=True, name="%s_blendColors" % asset)

    cmds.setAttr("%s.fileTextureName" % colorTex , colorTexPath, type="string")
    cmds.setAttr("%s.fileTextureName" % reflectionTex , reflectionTexPath, type="string")
    cmds.setAttr("%s.color2" % blendcolorTex ,0,0,0, type="double3")
    #if len(colorTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % colorTex , 3) #set to udim

    #Blend Color connect
    cmds.connectAttr("%s.outColor" %reflectionTex, "%s.color1" %blendcolorTex)


    #Connect
    cmds.connectAttr("%s.outColor" %colorTex, "%s.input1" %addcolorTex)
    cmds.connectAttr("%s.output" %blendcolorTex, "%s.input2" %addcolorTex)
    cmds.connectAttr("%s.outColor" %addcolorTex, "%s.baseColor" %shader)

    #### Displacement ####
    dispTex = cmds.shadingNode("file", asTexture=True, name="%s_disp" % asset)
    cmds.setAttr("%s.fileTextureName" % dispTex, displaceTexPath, type="string")
    #if len(displaceTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % dispTex , 3)

    #Connect
    cmds.connectAttr("%s.outColor.outColorR" %dispTex, "%s.displacement" % dispShader)
    """
    #### Specular Roughness ####
    specRoughnessTex = cmds.shadingNode("file", asTexture=True, name="%s_specRoughness" % s)
    cmds.setAttr("%s.alphaIsLuminance" % specRoughnessTex, 0) #Tick Alpah is Luminance
    cmds.setAttr("%s.fileTextureName" % specRoughnessTex, specRoughTexPath, type="string")
    if len(roughnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % specRoughnessTex , 3) #set to udim
    """
    #### Specular Glossiness ####
    specGlossTex = cmds.shadingNode("file", asTexture=True, name="%s_specGloss" % asset)
    remapGloss =  cmds.shadingNode("remapValue", asTexture=True, name="%s_specGlossRemap" % asset)
    cmds.setAttr("%s.outputMin" % remapGloss, 1)
    cmds.setAttr("%s.outputMax" % remapGloss, 0)

    cmds.setAttr("%s.alphaIsLuminance" % specGlossTex, 0) #Tick Alpah is Luminance
    cmds.setAttr("%s.fileTextureName" % specGlossTex, specGlossTexPath, type="string")

    #if len(roughnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % specRoughnessTex , 3) #set to udim
    #Connect
    cmds.connectAttr("%s.outColor.outColorR" % specGlossTex, "%s.inputValue" %remapGloss)
    cmds.connectAttr("%s.outValue" % remapGloss, "%s.specularRoughness" %shader)
    """
    #Metalness
    metalTex = cmds.shadingNode("file", asTexture=True, name="%s_metalness" % s)
    cmds.setAttr("%s.fileTextureName" % metalTex, metalnessTexPath, type="string")
    if len(metalnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % metalTex , 3) #set to udim
    """
    #ior
    iorTex = cmds.shadingNode("file", asTexture=True, name="%s_ior" % asset)
    remapior =  cmds.shadingNode("remapValue", asTexture=True, name="%s_iorRemap" % asset)
    cmds.setAttr("%s.inputMax" % remapior, 0.6)
    cmds.setAttr("%s.outputMin" % remapior, 1)
    cmds.setAttr("%s.outputMax" % remapior, 0)

    cmds.setAttr("%s.fileTextureName" % iorTex, iorTexPath, type="string")

    #if len(metalnessTexAll) >= 2: cmds.setAttr("%s.uvTilingMode" % metalTex , 3) #set to udim

    #Connect
    cmds.connectAttr("%s.outColor.outColorR" % iorTex, "%s.inputValue" %remapior)
    cmds.connectAttr("%s.outValue" % remapior, "%s.metalness" %shader)
    cmds.connectAttr("%s.outValue" % remapior, "%s.blender" %blendcolorTex)

    #Normal
    NormalTex = cmds.shadingNode("file", asTexture=True, name="%s_Normal" % asset )
    aiNormalMap = cmds.shadingNode("aiNormalMap", asTexture=True, name="%s_aiNormalMap" % asset)
    cmds.setAttr("%s.fileTextureName" % NormalTex, normalTexPath, type="string")
    #if len(normalTexAll) >= 2:cmds.setAttr("%s.uvTilingMode" % NormalTex , 3)  #set to udim

    #Connect
    cmds.connectAttr("%s.outColor" %NormalTex, "%s.input" %aiNormalMap)
    cmds.connectAttr("%s.outValue" %aiNormalMap, "%s.normalCamera" %shader)

    #Create shading group & Assign
    shadingGroup = cmds.sets(name="%sSG" % shader, empty=True, renderable=True, noSurfaceShader=True)
    cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % shadingGroup)                #color
    cmds.connectAttr("%s.displacement" % dispShader, "%s.displacementShader" % shadingGroup)   #displacement



def run():
    allAssetsDic= buildAllAssetsDic()
    for asset in allAssetsDic:
        shadingDic= allAssetsDic[asset]
        createShader(asset,shadingDic)
run()
