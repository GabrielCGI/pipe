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
                if cmds.listConnections(aov+".outputs[1].driver"):
                    pretty_aov+=" (on)"

                pretty_aov_list.append(pretty_aov)
            #check if already connected

    return pretty_aov_list

def createGUI():

    aovs= get_aovs()
    #window set up
    winWidth = 300
    winName = "aov"
    if cmds.window(winName, exists=True):
      cmds.deleteUI(winName)
    window = cmds.window(winName,title="Denoise Aovs - Variance Filter", width=winWidth, rtf=True)
    cmds.frameLayout( label='Variance filter ', labelAlign='bottom' )
    cmds.columnLayout(adjustableColumn= True, rowSpacing=0)
    cmds.textScrollList("aov_list",numberOfRows=20, allowMultiSelection=True, append=aovs, showIndexedItem=4 )
    cmds.button("add_denoise_all",label="Add all",  command=lambda x:clicked("all"))
    cmds.button("add_denoise_selected",label="Add selected",  command=lambda x:clicked("selected"))

    cmds.button("remove_denoise",label="Remove all",  command=lambda x:remove())
    cmds.showWindow(winName)

def refresh_list():
    aovs= get_aovs()
    if cmds.window("aov", exists=True):
        cmds.textScrollList("aov_list", edit=True, removeAll=True)
        cmds.textScrollList("aov_list", edit=True, append=aovs)

def clicked(mode):
    if mode == "all":
        prettyAovList = cmds.textScrollList("aov_list", q=True,allItems=True)
    if mode == "selected":
        prettyAovList = cmds.textScrollList("aov_list", q=True,selectItem=True)
    aovList = []
    if prettyAovList:
        for prettyAov in prettyAovList:
            #Remove already connected AOV from aov list
            if not prettyAov.endswith(" (on)"):
                print(prettyAov)
                aov = "aiAOV_"+prettyAov
                aovList.append(aov)

        varianceDriverExr, varianceFilter= setup_driver()
        for aov in aovList:
            cmds.connectAttr(varianceDriverExr+".message", aov+'.outputs[1].driver', f=True)
            cmds.connectAttr(varianceFilter+".message", aov+'.outputs[1].filter', f=True)
    else:
        msg= "Nothing AOVs selected, skipping"
        cmds.confirmDialog( title='Nothing selected', message=msg, button=['ok'] )

    #setup Output Denoising AOVs
    cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",1)
    refresh_list()

def remove():
    aovList = cmds.ls(type = "aiAOV")
    for aov in aovList:
        filterList = cmds.listConnections(aov+".outputs[1].filter")
        driverList = cmds.listConnections(aov+".outputs[1].driver")

        if filterList:
            if filterList[0] == "varianceFilter":
                cmds.disconnectAttr(filterList[0]+".message", aov+".outputs[1].filter")
        if driverList:
            if driverList[0] == "varianceDriver":
                cmds.disconnectAttr(driverList[0]+".message", aov+".outputs[1].driver")
    #setup Output Denoising AOVs
    cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",0)
    refresh_list()
