import maya.cmds as cmds
def setup_driver():

    if not cmds.objExists('varianceFilter'):
        varianceFilter = cmds.createNode( 'aiAOVFilter', n="varianceFilter")
    else:
        varianceFilter = "varianceFilter"
    if not cmds.objExists('varianceDriver'):
        varianceDriverExr= cmds.createNode( 'aiAOVDriver', n="varianceDriver")
    else:
        varianceDriverExr = "varianceDriver"

    cmds.setAttr(varianceDriverExr+".halfPrecision", 1)
    cmds.setAttr(varianceDriverExr+".mergeAOVs", 1)
    cmds.setAttr(varianceDriverExr+".prefix", "<RenderLayer>/<Scene>/variance_<Scene>", type="string")
    cmds.setAttr(varianceFilter+'.ai_translator', "variance", type="string")
    return varianceDriverExr, varianceFilter
def run():
    pass

def get_aovs():
    aovList = cmds.ls(type = "aiAOV")
    pretty_aov_list = []
    ok_list = ["sss","specular","direct","indirect","sheen","transmssion","coat","diffuse"]
    for aov in aovList:
            pretty_aov = aov.split("aiAOV_")[-1]
            if pretty_aov in ok_list or pretty_aov.startswith("RGBA_"):
                pretty_aov_list.append(pretty_aov)
    return pretty_aov_list

def createGUI():

    aovs= get_aovs()
    #window set up
    winWidth = 450
    winName = "aov"
    if cmds.window(winName, exists=True):
      cmds.deleteUI(winName)
    window = cmds.window(winName,title="Denoise Aovs", width=winWidth, rtf=True)
    cmds.frameLayout( label='Camera', labelAlign='bottom' )
    cmds.columnLayout(adjustableColumn= True, rowSpacing=0)
    cmds.textScrollList("aov_list",numberOfRows=20, allowMultiSelection=True, append=aovs, showIndexedItem=4 )
    cmds.button("add_denoise",label="Add denoising AOVs ",  command=lambda x:clicked())
    cmds.showWindow(winName)

def clicked():
    prettyAovList = cmds.textScrollList("aov_list", q=True,selectItem=True)
    aovList = []
    for prettyAov in prettyAovList:
        aov = "aiAOV_"+prettyAov
        aovList.append(aov)

    varianceDriverExr, varianceFilter= setup_driver()
    for aov in aovList:
        cmds.connectAttr(varianceDriverExr+".message", aov+'.outputs[1].driver', f=True)
        cmds.connectAttr(varianceFilter+".message", aov+'.outputs[1].filter', f=True)
