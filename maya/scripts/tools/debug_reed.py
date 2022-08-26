import maya.cmds as cmds
import mtoa.aovs as aovs

def aovMaskBottle():
    if not cmds.objExists("aiAOV_mask_bottle"):


        cmds.lockNode('initialShadingGroup', lock=False, lu=False)

        cmds.lockNode('initialParticleSE', lock=False, lu=False)
        aovs.AOVInterface().addAOV("mask_bottle")
        cmds.setAttr("aiAOV_mask_bottle.type",4)
        fileMask = cmds.shadingNode("file",asTexture=True)
        remap = cmds.shadingNode("remapValue",asUtility=True)
        cmds.setAttr(remap+".inputMax", 0.504)

        userData = cmds.shadingNode("aiUserDataFloat",asUtility=True)
        cmds.setAttr(userData+".attribute","maskBottle",  type="string")

        blendColor= cmds.shadingNode("blendColors",asUtility=True)
        cmds.setAttr(blendColor+".color2", 0, 0, 0 , type="double3")

        cmds.setAttr(fileMask+".fileTextureName", "$DISK_I/guerlain_2206/assets/ch_beeBottleGold/textures/mask7/phong1SG_Base_color_ACES - ACEScg_1001.tx", type="string")
        cmds.setAttr(fileMask+".uvTilingMode", 3)

        cmds.setAttr(fileMask+".colorSpace", "Raw", type="string")

        cmds.connectAttr(userData+".outValue", blendColor+".blender", f=True)

        cmds.connectAttr(fileMask+".outColor",blendColor+".color1", f=True)

        cmds.connectAttr(blendColor+".output.outputR", remap+".inputValue", f=True)
        cmds.connectAttr(remap+".outValue", "aiAOV_mask_bottle.defaultValue", f=True)
        print("MASK BOTLLE CREATED !")

def run():
    aovMaskBottle()
    nodes=cmds.ls( type="aiStandIn" )
    for node in nodes:

        if "herbesA_ass" in node:
            print ("FIXED :"+ node)
            cmds.setAttr(node+".overrideShaders",0)


    dic = {"I:/guerlain_2206/assets/plantAmelanchier/houdini/export/trunckG.abc":"I:/guerlain_2206/assets/plantAmelanchier/ass/trunk_plantG.ass",
           "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/flowerG_instance2.abc":"I:/guerlain_2206/assets/plantAmelanchier/ass/flowerG_plantG.ass",
           "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/flowerA_instance2.abc":"I:/guerlain_2206/assets/plantAmelanchier/ass/flowerA_plantA.ass",
           "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/trunckA.abc":"I:/guerlain_2206/assets/plantAmelanchier/ass/trunk_plantA.ass",
           "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/leafA.abc":"I:/guerlain_2206/assets/plantAmelanchier/ass/leafA.ass",
           "I:/guerlain_2206/assets/plantAmelanchier/houdini/export/leafG.abc":"I:/guerlain_2206/assets/plantAmelanchier/ass/leafG.ass",
           "I:/guerlain_2206/assets/plantSyringa/ass/syringa_trunck6.ass":"I:/guerlain_2206/assets/plantSyringa/ass/syringa_trunck7.ass",
           }
    for node in nodes:
        dso=cmds.getAttr(node+".dso")
        if dso in dic:
            cmds.setAttr(node+".dso",  dic[dso], type="string")
            cmds.setAttr(node+".overrideShaders",0)
            print ("FIXED :"+ node)
