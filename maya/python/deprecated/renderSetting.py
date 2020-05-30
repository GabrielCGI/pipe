import maya.cmds as cmds


#driver = "aiAOVDriver1"
#aov = "aiAOV_crypto_object"
#cmds.connectAttr(driver+".message", aov+".outputs[0].driver", f=True)

imgFilePrefix = "<Scene>/<RenderLayer>/<Scene>_<RenderPass>"


def setRenderSetting():
    #Image file prefix
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", imgFilePrefix, type="string")
    #Half float
    cmds.setAttr("defaultArnoldDriver.halfPrecision", 1)




"""
setRenderSetting()
fullDriver = cmds.createNode( 'aiAOVDriver', n="fullDriver")
aovList = ["aiAOV_crypto_object","aiAOV_crypto_material","aiAOV_crypto_asset","aiAOV_Z"]
for aov in aovList:
    print aov
    cmds.connectAttr(fullDriver+".message", aov+".outputs[0].driver", f=True)
"""
