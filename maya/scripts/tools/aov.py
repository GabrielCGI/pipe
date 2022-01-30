"""
#Arnold AOV version 1.0.0
#Add AOV's to render.
#Handle 32bits and 16bits according to the AOV type
To run the script
import aov as aov
aov.createGUI()
"""

import maya.cmds as cmds
import mtoa.aovs as aovs
import maya.mel as mel
import re

#fullDriverName = "fullDriver"
imgFilePrefix = "<RenderLayer>/<Scene>/<Scene>"

aovDic = {
"default":
{
"N":{"bits":"half","type":"default","state":1,"action":""},
"P":{"bits":"half","type":"default","state":1,"action":""},
#"Z":{"bits":"half","type":"default","state":1,"action":""},
"motionvector":{"bits":"half","type":"default","state":1,"action":""},
"sheen":{"bits":"half","type":"default","state":1,"action":""},
"specular":{"bits":"half","type":"default","state":1,"action":""},
"transmission":{"bits":"half","type":"default","state":1,"action":""},
"sss":{"bits":"half","type":"default","state":1,"action":""},
"coat":{"bits":"half","type":"default","state":1,"action":""},
"volume":{"bits":"half","type":"default","state":1,"action":""},
"emission":{"bits":"half","type":"default","state":1,"action":""}


},
"crypto":
{
"crypto_asset":{"bits":"full","type":"default","state":1,"action":"makeCrypto('aiAOV_crypto_asset')"},
"crypto_material":{"bits":"full","type":"default","state":1,"action":"makeCrypto('aiAOV_crypto_material')"},
"crypto_object":{"bits":"full","type":"default","state":1,"action":"makeCrypto('aiAOV_crypto_object')"}
},
"utils":
{
"occlusion":{"bits":"half","type":"custom","state":1,"action":"makeOcclusion()"},
"UV":{"bits":"full","type":"custom","state":1,"action":"makeUV()"},

}
}

#RENDER SETTINGS
def setImgFilePrefix():
    #Image file prefix
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", imgFilePrefix, type="string")
    mel.eval('setMayaSoftwareFrameExt("3", 0);')


#AOV



def makeOcclusion():
    #Create Occlusion Shader and Connect
    occShader = cmds.createNode('aiAmbientOcclusion' , name = 'occMtl')
    cmds.setAttr(occShader + '.falloff' ,0)
    cmds.connectAttr(occShader + '.outColor' , "aiAOV_occlusion.defaultValue")

def makeCrypto(cryptoType):
    if not cmds.objExists('aov_cryptomate'):
        cmds.createNode("cryptomatte", n="aov_cryptomate")   #Create Cryptomatte shader
    cmds.connectAttr("aov_cryptomate.outColor", cryptoType+".defaultValue")


def makeUV():
    uvNode = cmds.createNode("aiUtility", n="aiUtiliy_uv")
    cmds.setAttr(uvNode + '.shadeMode' , 2)
    cmds.setAttr(uvNode + '.colorMode' , 3)
    #Create UV Shader
    cmds.connectAttr(uvNode + '.outColor' , 'aiAOV_UV.defaultValue')


def makeWireframe():
    #Create Shader and Connect
    wireShader = cmds.createNode('aiWireframe', name = 'wireframeMtl')
    cmds.setAttr(wireShader + '.edgeType' , 1)
    cmds.connectAttr(wireShader + '.outColor' , 'aiAOV_wireframe.defaultValue')

def makeEdgeLength():
    #Create Shader and Connect
    edgeLNode = cmds.createNode("aiUtility", n="aiUtility_edgeLength")
    cmds.setAttr(edgeLNode + '.shadeMode' , 2)
    cmds.setAttr(edgeLNode + '.colorMode' , 16)
    #Create UV Shader
    cmds.connectAttr(edgeLNode + '.outColor' , 'aiAOV_edgeLength.defaultValue')

def makeRimLight():
    #Create Ramp and sampler info
    ramp = cmds.shadingNode('ramp', name = 'rimLight_ramp', asTexture = True)
    samplerInfo = cmds.shadingNode('samplerInfo', asUtility = True)
    #set ramp up
    cmds.setAttr(ramp + '.colorEntryList[1].position', 1)
    cmds.setAttr(ramp + '.colorEntryList[1].color', 0, 0, 0, type = 'double3')
    cmds.setAttr(ramp + '.colorEntryList[0].position', 0)
    cmds.setAttr(ramp + '.colorEntryList[0].color', .9, .9, .9, type = 'double3')
    #connect sampler info to ramp
    cmds.connectAttr(samplerInfo + '.facingRatio', ramp + '.uCoord')
    cmds.connectAttr(samplerInfo + '.facingRatio', ramp + '.vCoord')
    #Create Shader and Connect
    rimShader = cmds.createNode('surfaceShader' , name = 'rimMtl')
    cmds.connectAttr(ramp + '.outColor' , rimShader + '.outColor' )
    cmds.connectAttr(ramp+ '.outColor' , 'aiAOV_facingRatio.defaultValue')


def mayaWarning(msg):
    """
    Display of maya warning
    """
    cmds.warning(msg)
    cmds.confirmDialog(title="Error",message=msg)

def addAOVDefault(aov,bits,type,action):
    #Driver work
    #Create 32bit driver if not exist
    #if not cmds.objExists('fullDriver'):
#        cmds.createNode( 'aiAOVDriver', n=fullDriverName)
    #Set prefix and merge
    #cmds.setAttr(fullDriverName+".prefix", "<Scene>_full",type="string")
    #cmds.setAttr("defaultArnoldDriver.prefix", "<Scene>_half",type="string")
    #cmds.setAttr(fullDriverName+".mergeAOVs", 0)
    cmds.setAttr("defaultArnoldDriver.mergeAOVs", 1)
    #Half float for color
    cmds.setAttr("defaultArnoldDriver.halfPrecision", 0)

    if cmds.objExists("aiAOV_"+aov):
        msg = "AOV '%s' already exist. Skip."%(aov)
        mayaWarning(msg)
    else:
        newAov = aovs.AOVInterface().addAOV(aov)
        #if bits == "full":
        #    cmds.connectAttr(fullDriverName+".message", "aiAOV_"+newAov.name+".outputs[0].driver", f=True)
        #if aov == "Z":
            #print("it's a z !")
            #cmds.connectAttr('defaultArnoldFilter.message', 'aiAOV_Z.outputs[1].filter')
            #cmds.connectAttr(fullDriverName+".message", 'aiAOV_Z.outputs[1].driver')
        if action:
            exec(action)


def getLights():
#Fetch the light is the scene
    lights = cmds.ls(type=["aiAreaLight","aiSkyDomeLight","directionalLight","pointLight","spotLight","aiPhotometricLight","aiMeshLight"])
    return lights

def aovLigths():
#Create a ligth aov for each lights and store in a dic for latter use.
    aovLigths = {}
    for light in getLights():
        aovName = re.sub('[:]', '', light) #Delete ":" from ref to avoid AOV naming error
        rgba_aovName = "RGBA_"+aovName
        aovLigths[rgba_aovName] = light
    return aovLigths

aovLigths = aovLigths()

#Create my GUI
def createGUI():
    mel.eval('setMayaSoftwareFrameExt("3", 0);')
    #window set up
    winWidth = 600
    winName = "aovWindow"
    if cmds.window(winName, exists=True):
      cmds.deleteUI(winName)
    aovWindow = cmds.window(winName,title="Custom Render Element", width=winWidth, rtf=True)

    cmds.columnLayout(adjustableColumn= True, rowSpacing= 10)
    cmds.text( label='AOV\'s',font='boldLabelFont')
    cmds.rowLayout(numberOfColumns=4,rowAttach=[(1, 'top', 0),(2, 'top', 0),(3, 'top', 0),(4, 'top', 0)])
    cmds.columnLayout()
    cmds.text( label='Default AOV',font='boldLabelFont' )
    #AOV Default
    for aov in list(aovDic["default"].keys()):
        cmds.checkBox(aov, label=aov, value=aovDic["default"][aov]["state"])
    cmds.setParent('..')
    cmds.columnLayout()
    #AOV Crypto
    cmds.text( label='Crypto',font='boldLabelFont'  )
    for aov in list(aovDic["crypto"].keys()):
        cmds.checkBox(aov, label=aov, value=aovDic["crypto"][aov]["state"])

    cmds.setParent('..')
    cmds.columnLayout()
    #AOV Light Groupe
    cmds.text( label="Light Group",font='boldLabelFont'  )
    for aovLigth in list(aovLigths.keys()):
        cmds.checkBox(aovLigth, label=aovLigth, value=True)

    cmds.setParent('..')
    cmds.columnLayout()
    cmds.text( label='Utilitaire AOV',font='boldLabelFont')

    for aov in list(aovDic["utils"].keys()):
        cmds.checkBox(aov, label=aov, value=aovDic["utils"][aov]["state"])

    cmds.setParent('..')
    cmds.setParent('..')
    cmds.text( label='Render setting',font='boldLabelFont')
    #cmds.checkBox("halfFloat", label="Half float Exr (16bits)", value=True)
    cmds.checkBox("prefix", label="File name prefix <Scene>/<RenderPass>/<Scene>.exr", value=True)
    cmds.button( label='Run', width= 224, command=lambda x:queryValues())
    cmds.columnLayout()
    cmds.button( label='Uncheck all', width= 100, command=lambda x:uncheck())


    cmds.showWindow('aovWindow')


def uncheck():
    for aovKind in list(aovDic.keys()):
        for aov in list(aovDic[aovKind].keys()):
            cmds.checkBox(aov, edit=True, value =False)
    for aovLigth in list(aovLigths.keys()):
        cmds.checkBox(aovLigth, edit=True, value =False)
#query checkboxes
def queryValues():
    for aovKind in list(aovDic.keys()):
        for aov in list(aovDic[aovKind].keys()):
            value = cmds.checkBox(aov, query = True, value =True)
            if value == True:
                bits = aovDic[aovKind][aov]["bits"]
                type = aovDic[aovKind][aov]["type"]
                action = aovDic[aovKind][aov]["action"]
                addAOVDefault(aov,bits,type,action)

    for aovLigth in list(aovLigths.keys()):
        if cmds.checkBox(aovLigth, query = True, value = True):
            addAOVDefault(aovLigth, bits="half", type="default", action="")
            aovLightExpr = aovLigth.split("RGBA_")[-1] #Delete RGBA_
            light = aovLigths[aovLigth] #Get the ligth associate with the aov
            cmds.setAttr(light +".aiAov", aovLightExpr, type="string")
    if cmds.checkBox("prefix", query = True, value =True):
        setImgFilePrefix()
    #if cmds.checkBox("halfFloat", query = True, value =True):
    #    setHalfFloat()


#Run the Script
