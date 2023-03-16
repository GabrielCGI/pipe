
import maya.mel as mel
import maya.cmds as cmds
import importlib
import os
import json
import maya.app.renderSetup.model.override as mayaOv
import maya.app.renderSetup.model.renderSetup as renderSetup
import maya.app.renderSetup.model.utils as utils

from functools import partial
#Init variables
presets_folder = "R:\\pipeline\\pipe\\maya\\scripts\\tools\\presets_render_setting"
presetDic={}
bgColor = [0.4,0.2,0.1]
bgColorOff = [0.32,0.32,0.32]

labelPretty = {"ignoreSubdivision":"Ignore Subdivision",
                "ignoreDisplacement":"Ignore Displacement",
                "ignoreAtmosphere":"Ignore Athmosphere",
                "ignoreMotionBlur":"Instantaneous Shutter",
                "motion_blur_enable":"Enable",
                "enableProgressiveRender":"Progressive Render",
                "AASamples":"Camera (AA)",
                "GIDiffuseSamples":"Diffuse",
                "GISpecularSamples":"Specular",
                "GITransmissionSamples":"Transmission",
                "GISssSamples":"SSS", "GIVolumeSamples":"Volume Indirect",
                "GIDiffuseDepth":"Ray Depth Diffuse",
                 "GISpecularDepth":"Ray Depth Specular",
                 "enableAdaptiveSampling":"Enable",
                 "AASamplesMax":"Max. Camera (AA)",
                 "motion_steps":"Keys",
                 "motion_frames":"Motion step",
                 "ignoreMotion": "Ignore Motion",
                 "ignoreDof":"Ignore Depth of field"
                }

#FIX .aovName' is locked or connected and cannot be modified. #
cmds.lockNode('initialShadingGroup', lock=False, lu=False)
cmds.lockNode('initialParticleSE', lock=False, lu=False)
# List renderable cameras

def isLentilInstalled():
    return False
"""
    try:
        dof_state= cmds.getAttr(renderableCameras[0]+".enableDof")
        return True
    except:
        return False
"""
def getRenderableCameras():
    cameras = cmds.ls(type="camera")
    renderableCameras=[]
    for cam in cameras:
        if cmds.getAttr(cam+".renderable"):
            renderableCameras.append(cam)
    return renderableCameras

def hasOverride(param, node="defaultArnoldRenderOptions"):
    overides= cmds.ls(cmds.listHistory("defaultArnoldRenderOptions."+param, pruneDagObjects=True), type="applyOverride")

    if overides:
        overideFound =0
        for overide in overides:
            if param in overide:
                overideFound= 1
                print("found overide"+ param)
        if overideFound == 1:

            return True
        else:
            return False
    else:
        return False

def checkBoxCreate(param):

    state= cmds.getAttr("defaultArnoldRenderOptions."+param)
    if hasOverride(param):
        cmds.checkBox(param, enableBackground=True,label=labelPretty[param],
                            value=state, backgroundColor=bgColor,
                            changeCommand=lambda x:ignore(param,cmds.checkBox(param, query=True, value=True)))

    else:
            cmds.checkBox(param, label=labelPretty[param],
                        value=state, noBackground=1-hasOverride(param),
                        changeCommand=lambda x:ignore(param,cmds.checkBox(param, query=True, value=True)))
    popMenuItem(param,0)

def sliderCreate(param):
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+param)
    minValue= 0
    if param=="motion_steps": minValue= 2
    if hasOverride(param):
        cmds.intSliderGrp( param,  field=True, label=labelPretty[param], minValue=minValue,
                                maxValue=20, enableBackground=hasOverride(param), backgroundColor=bgColor,
                                 value=samples_value, changeCommand=lambda x:updateSample(param) )


    else:

        cmds.intSliderGrp( param,  field=True, label=labelPretty[param], minValue=minValue,
                                maxValue=20,
                                 value=samples_value, changeCommand=lambda x:updateSample(param) )


    popMenuItem(param,1)

def floatSliderCreate(param):
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+param)
    if hasOverride(param):

        cmds.floatSliderGrp( param, backgroundColor=bgColor, enableBackground=hasOverride(param),
        field=True, label=labelPretty[param], minValue=0, maxValue=1,sliderStep=0.01, precision=3, value=samples_value, changeCommand=lambda x:updateSampleFloat(param) )

    else:


        cmds.floatSliderGrp(param, field=True, label=labelPretty[param],
        minValue=0, maxValue=1,sliderStep=0.01, precision=3, value=samples_value, changeCommand=lambda x:updateSampleFloat(param) )

    popMenuItem(param,2)


def isLentilEnable():
    cam = cmds.optionMenu("renderCamMenu", query = True, value=True)
    try:
        activeCamType = cmds.getAttr(cam+".ai_translator")
    except:
        activeCamType = "perspective"
    try:
        if activeCamType == "lentil_camera":
            lentil_enable=1
        else:
            lentil_enable=0
    except Exception as e :
        lentil_enable=0
        print (e)

    return lentil_enable

def createOidn():
    if not cmds.objExists("aiImagerDenoiserOidn1"):
        cmds.createNode( 'aiImagerDenoiserOidn', n='aiImagerDenoiserOidn1' )
createOidn()


def createOverride(param, type=0):
    try:
        already_exist = 0
        visibleLayer = renderSetup.instance().getVisibleRenderLayer()
        col = visibleLayer.renderSettingsCollectionInstance()
        for i in utils.getOverridesRecursive(visibleLayer):
            if param == i.attributeName():
                already_exist = 1
        if not already_exist:
            ov = col.createAbsoluteOverride('defaultArnoldRenderOptions',param)
            if type==0:
                cmds.checkBox(param, edit=True,noBackground=False)
                cmds.checkBox(param, edit=True,backgroundColor=bgColor)
            if type==1:
                cmds.intSliderGrp(param, edit=True, backgroundColor=bgColor)
            if type==2:
                cmds.floatSliderGrp(param, edit=True, backgroundColor=bgColor)

    except Exception as e:
        cmds.confirmDialog( title='Erreur', message="Not possible to create overide \n %s"%e, button=['ok'])
        print(e)
    #ov.setAttrValue(value)


def removeOverride(param,type=0):
    try:
        visibleLayer = renderSetup.instance().getVisibleRenderLayer()
        col = visibleLayer.renderSettingsCollectionInstance()
        for i in utils.getOverridesRecursive(visibleLayer):
            if param == i.attributeName():
                mayaOv.delete(i)
                if type==0:
                    cmds.checkBox(param, edit=True,backgroundColor=bgColorOff)
                    cmds.checkBox(param, edit=True,enableBackground=False)
                    cmds.checkBox(param, edit=True,noBackground=True)

                if type==1:
                    cmds.intSliderGrp(param, edit=True, backgroundColor=bgColorOff)
                    cmds.intSliderGrp(param, edit=True,enableBackground=False)
                if type==2:
                    cmds.floatSliderGrp(param, edit=True, backgroundColor=bgColorOff)
                    cmds.floatSliderGrp(param, edit=True,enableBackground=False)
    except Exception as e:
        print (e)
        cmds.confirmDialog( title='Erreur', message="Not possible to delete overide \n %s"%e, button=['ok'])
#ov.setAttrValue(value)


def popMenuItem(param, type=0):
    cmds.popupMenu(param)
    cmds.menuItem("Absolute override", c = lambda x: createOverride(param, type))
    cmds.menuItem("Remove override", c = lambda x: removeOverride(param, type))

#Create my GUI
def createGUI():
    #window set up
    winWidth = 450
    winName = "TURBOTRON"
    if cmds.window(winName, exists=True):
      cmds.deleteUI(winName)
    window = cmds.window(winName,title="Control Room   ( ͡ಠ ʖ̯ ͡ಠ )", width=winWidth, rtf=True)

    #-----  CAMERA --------
    cmds.frameLayout( label='Camera', labelAlign='bottom' )
    cmds.columnLayout(adjustableColumn= True, rowSpacing=0)
    cmds.optionMenu("renderCamMenu", label='Renderable Camera')

    renderableCameras= getRenderableCameras()
    cam_number =len(renderableCameras)
    if cam_number == 0:
        cmds.warning("There is no renderable camera set in render settings. ")

    if cam_number > 1:
        too_many_cam = cam_number-1

        cmds.confirmDialog( title='Too many cam!', message='Did you know you have %s camera set a renderable?\nThat is %s too many !!!\n '%(len(renderableCameras),too_many_cam), button=['ok...'], defaultButton='Yes', cancelButton='No', dismissString='No' )
    for cam in renderableCameras:
        cmds.menuItem(label=cam)
    # Check camera type (lentil ou perspective)
    lentil_enable=isLentilEnable()

    #----- Global Features Overrides --------

    cmds.frameLayout( label='Feature Overrides', labelAlign='bottom')
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)
    # -- DOF / MB / LENTIL

    # -- Ignore Overriedes
    #IGNORE SUBDIVISION
    checkBoxCreate("ignoreSubdivision")
    checkBoxCreate("ignoreAtmosphere")
    checkBoxCreate("ignoreDisplacement")
    checkBoxCreate("ignoreMotion")
    checkBoxCreate("ignoreDof")
    cmds.setParent("..")
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)


    #IGNORE ATHMO

    # -- AOVs Overriedes
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.checkBox("ignoreAov",label="Ignore AOVs", changeCommand=lambda x:aov_enabled(cmds.checkBox("ignoreAov",query=True,value=True)))

    all_aovList = cmds.ls(type = "aiAOV")
    aovList = []
    for aov in all_aovList:
        if len(aov.split(":"))==1:
            aovList.append(aov)


    enabled_aov = []
    for aov in aovList:
        if cmds.getAttr(aov+".enabled")==1:
            enabled_aov.append(aov)
    enabled_aov_total = len(enabled_aov)
    aov_total = len(aovList)
    if enabled_aov_total == 0:
        cmds.checkBox("ignoreAov",e=True,value=True)
    text_aov_count = str(enabled_aov_total)+"/"+str(aov_total)


    cmds.text("aov_counter",label=text_aov_count, font="boldLabelFont")


    cmds.setParent("..")
    cmds.checkBox("outputVarianceAOVs",label="Output Denoising AOVs",value=cmds.getAttr("defaultArnoldRenderOptions.outputVarianceAOVs"),changeCommand=lambda x:denoise_on())
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")


    cmds.setParent("..")

    #-----  Motion blur --------
    cmds.frameLayout( label='DOF', labelAlign='bottom')
    cmds.rowColumnLayout( numberOfColumns = 2)
    try:
        dof_state= cmds.getAttr(renderableCameras[0]+".enableDof")
    except:
        dof_state= cmds.getAttr(renderableCameras[0]+".aiEnableDOF")
    cmds.checkBox("aiEnableDOF", label="Depth of Field", value=dof_state, changeCommand=lambda x:dof())
    if isLentilInstalled():
        lentilBoxVisible = True
    else:
        lentilBoxVisible =False
    cmds.checkBox("lentil_enable", label="Lentil", value=lentil_enable,visible=lentilBoxVisible, changeCommand=lambda x:changeCamType())
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.text("FStop ")
    cmds.floatField("fStop",precision=2,value=cmds.getAttr(cam+".fStop"), changeCommand=lambda x:cmds.setAttr(cam+".fStop",cmds.floatField("fStop",query=True,value=True)))

    cmds.setParent("..")
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.text("Samples Mult.")
    try:
        bidirSampleMult = getAttr(cam+".bidirSampleMult")
    except:
        bidirSampleMult =0
    cmds.intField("bidirSampleMult",value=bidirSampleMult, changeCommand=lambda x:cmds.setAttr(cam+".bidirSampleMult",cmds.intField("bidirSampleMult",query=True,value=True)))
    cmds.setParent("..")
    cam = cmds.optionMenu("renderCamMenu", query = True, value=True)

    cmds.setParent("..")
    cmds.setParent("..")
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)

    cmds.setParent("..")

    cmds.frameLayout( label='Motion blur', labelAlign='bottom')
    checkBoxCreate("motion_blur_enable")
    checkBoxCreate("ignoreMotionBlur")

    sliderCreate("motion_steps")
    floatSliderCreate("motion_frames")

    cmds.setParent("..")

    #-----  Render settings --------
    cmds.frameLayout( label='Image size', labelAlign='bottom')
    cmds.rowColumnLayout( numberOfColumns =1 )
    cmds.optionMenu("renderSize", label='Presets',changeCommand=lambda x:renderSizePreset(cmds.optionMenu("renderSize",query=True,value=True)))
    cmds.menuItem( label='HD_720' )
    cmds.menuItem( label='HD_1080' )
    cmds.menuItem( label='Custom' )
    renderWidth= cmds.getAttr("defaultResolution.width")
    renderHeight = cmds.getAttr("defaultResolution.height")
    cmds.rowColumnLayout( numberOfColumns =2 )
    cmds.text("Width:")
    cmds.intField("renderWidth",value=renderWidth, changeCommand=lambda x:updateSize(cmds.intField("renderWidth",query=True,value=True),"width"))
    cmds.text("Height:")
    cmds.intField("renderHeigth",value=renderHeight,  changeCommand=lambda x:updateSize(cmds.intField("renderHeigth",query=True,value=True),"height"))

    cmds.setParent("..")

    if renderWidth == 1280 and renderHeight == 720:
        cmds.optionMenu("renderSize", e=True, value='HD_720')
    elif renderWidth == 1920 and renderHeight == 1080:
        cmds.optionMenu("renderSize", e=True, value="HD_1080")
    else:
        cmds.optionMenu("renderSize", e=True, value="Custom")
    cmds.setParent( '..' )
    cmds.setParent( '..' )

    #SAMPLING
    cmds.frameLayout( label='Sampling', labelAlign='bottom')

    #CAMERA AA
    checkBoxCreate("enableProgressiveRender")
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"AASamples")

    #CREATE SLIDERS
    sliderList = ["AASamples", "GIDiffuseSamples","GISpecularSamples","GITransmissionSamples","GISssSamples","GIVolumeSamples","GIDiffuseDepth","GISpecularDepth",]
    for slider in sliderList:
        sliderCreate(slider)

    #ADAPTATIVE SAMPLING
    cmds.frameLayout( label='Adaptive Sampling', labelAlign='bottom')
    #Enable adaptative
    checkBoxCreate("enableAdaptiveSampling")
    sliderCreate( "AASamplesMax")

    #Enable AAAdaptiveThreshold
    AAAdaptiveThreshold_state = cmds.getAttr("defaultArnoldRenderOptions.AAAdaptiveThreshold")
    cmds.floatSliderGrp( "AAAdaptiveThreshold", field=True,precision=3, label="Adaptive Threshold", minValue=0, maxValue=1, fieldMinValue=0, fieldMaxValue=1,sliderStep=0.01,value=AAAdaptiveThreshold_state, changeCommand=lambda x:cmds.setAttr("defaultArnoldRenderOptions.AAAdaptiveThreshold", cmds.floatSliderGrp("AAAdaptiveThreshold",query=True,value=True)) )


    cmds.separator( height=10, style='in' )
    cmds.rowColumnLayout( numberOfColumns =4,columnSpacing=(20,20))
    cmds.button("fast", width=100,height=60, label="Fast",command=lambda x:apply_preset("fast"))
    cmds.button("lookdev",width=100,height=60, label="Look dev",  command=lambda x:apply_preset("lookdev"))
    cmds.button("md", width=100,height=60,label="MD",  command=lambda x:apply_preset("md"))
    cmds.button("hd", width=100,height=60,label="HD",  command=lambda x:apply_preset("hd"))
    cmds.setParent("..")
    cmds.rowColumnLayout( numberOfColumns =2,columnSpacing=(20,20))
    cmds.optionMenu("scenePreset", label='Apply preset', changeCommand=lambda x:apply_preset(cmds.optionMenu("scenePreset",query=True,value=True)) )
    presetDic = build_preset_dic()
    presetDic
    for preset in presetDic:
        cmds.menuItem(preset)
    cmds.button("save preset",label="Save New Preset",  command=lambda x:save_preset())

    cmds.showWindow(winName)

##.................................................................##
#######################################################################



    def motion_blur_enable(state):
        cmds.setAttr("defaultArnoldRenderOptions.motion_blur_enable",state)
        cmds.checkBox("MotionBlur",edit= True, editable=state)
        cmds.intSliderGrp("motion_steps",edit= True,manage=state)
        cmds.floatSliderGrp("motion_frames",edit= True,manage=state)

    def save_preset():

        result = cmds.promptDialog(
                    title='Preset Name',
                    message='Preset name:',
                    button=['OK'],
                    defaultButton='OK',
                    dismissString='Cancel')
        attrString = cmds.promptDialog(query=True, text=True)
        print (attrString)
        if result == "OK":
            param_dic = {}

            param_list=["enableProgressiveRender","outputVarianceAOVs","AAAdaptiveThreshold","AASamplesMax","enableAdaptiveSampling","ignoreSubdivision","ignoreAtmosphere","ignoreDisplacement","motion_blur_enable","AASamples","GIDiffuseSamples","GISpecularSamples","GIDiffuseSamples","GITransmissionSamples","GISssSamples","GIDiffuseSamples","GIVolumeSamples","AASamplesMax","GIDiffuseDepth","GISpecularDepth"]
            for param in param_list:
                param_dic[param]=cmds.getAttr("defaultArnoldRenderOptions."+param )

            param_dic["render_size"]=cmds.optionMenu("renderSize", query=True,value=True)
            param_dic["lentil_enable"]=cmds.checkBox("lentil_enable",query=True,value=True)
            param_dic["aiEnableDOF"]=cmds.checkBox("aiEnableDOF",query=True,value=True)
            param_dic["AOV"]=(cmds.checkBox("ignoreAov",query=True,value=True))


            preset_path = os.path.join(presets_folder,attrString+".txt")

            with open(preset_path, "w") as f:
                f.write(json.dumps(param_dic))
            cmds.menuItem(parent = ( 'scenePreset'), label = attrString)
            cmds.optionMenu("scenePreset",e=True,value=attrString)
###Read preset folder and return a dictionary
def build_preset_dic():
    listPresets = os.listdir(presets_folder)
    for preset in listPresets:
        filepath = os.path.join(presets_folder,preset)
        with open(filepath) as json_file:
            preset_data = json.load(json_file)
        presetName, presetExtention = os.path.splitext(preset)
        presetDic[presetName]=preset_data
    return presetDic


### APPLY A PRESET
def apply_preset(preset):
    presetDic = build_preset_dic()
    preset = presetDic[preset]

    #Note: Changer la veleur du checkbox en script ne déclenche pas la fonction "onChange". Il faut donc la recopier pour que le changement affect maya (et pas que l'UI)...
    cmds.checkBox("lentil_enable",e=True,value=preset["lentil_enable"])
    changeCamType()

    cmds.checkBox("aiEnableDOF",e=True,value=preset["aiEnableDOF"])
    dof()

    cmds.checkBox("motion_blur_enable",e=True,value=preset["motion_blur_enable"])
    cmds.setAttr("defaultArnoldRenderOptions.motion_blur_enable",cmds.checkBox("motion_blur_enable", query=True, value=True))

    cmds.checkBox("ignoreDisplacement",e=True,value=preset["ignoreDisplacement"])
    ignore("ignoreDisplacement",cmds.checkBox("ignoreDisplacement", query=True, value=True))

    cmds.checkBox("ignoreAtmosphere",e=True,value=preset["ignoreAtmosphere"])
    ignore("ignoreAtmosphere",cmds.checkBox("ignoreAtmosphere", query=True, value=True))

    cmds.checkBox("ignoreSubdivision",e=True,value=preset["ignoreSubdivision"])
    ignore("ignoreSubdivision",cmds.checkBox("ignoreSubdivision", query=True, value=True))

    cmds.optionMenu("renderSize", e=True, value=preset["render_size"])
    renderSizePreset(cmds.optionMenu("renderSize",query=True,value=True))

    samples_list=["AASamples","GIDiffuseSamples","GISpecularSamples","GIDiffuseSamples","GITransmissionSamples","GISssSamples","GIDiffuseSamples","GIVolumeSamples","AASamplesMax","GIDiffuseDepth","GISpecularDepth"]
    for sample in samples_list:
        cmds.intSliderGrp(sample,e=True, value=preset[sample])
        updateSample(sample)
    cmds.floatSliderGrp("AAAdaptiveThreshold",e=True, value=preset["AAAdaptiveThreshold"])
    cmds.setAttr("defaultArnoldRenderOptions.AAAdaptiveThreshold", cmds.floatSliderGrp("AAAdaptiveThreshold",query=True,value=True))

    cmds.checkBox("enableAdaptiveSampling",e=True,value=preset["enableAdaptiveSampling"])
    cmds.setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling",preset["enableAdaptiveSampling"])

    aov_enabled(preset["AOV"])
    cmds.checkBox("ignoreAov",e=True,value=preset["AOV"])

    cmds.checkBox("enableProgressiveRender",e=True,value=preset["enableProgressiveRender"])
    cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender",preset["enableProgressiveRender"])

    cmds.checkBox("outputVarianceAOVs",e=True,value=preset["outputVarianceAOVs"])
    cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",preset["outputVarianceAOVs"])




def aov_enabled(value):
    all_aovList = cmds.ls(type = "aiAOV")
    aovList = []
    for aov in all_aovList:
        if len(aov.split(":"))==1:
            aovList.append(aov)

    for aov in aovList:
        cmds.setAttr(aov+".enabled",1-value)
    #update text label enabled aov counter
    enabled_aov = []

    for aov in aovList:
        if cmds.getAttr(aov+".enabled")==1:
            enabled_aov.append(aov)
    enabled_aov_total = len(enabled_aov)
    aov_total = len(aovList)
    edited_text =  str(enabled_aov_total)+"/"+str(aov_total)
    cmds.text("aov_counter", e=True, label= edited_text)

def updateSample(sample):
    value= cmds.intSliderGrp(sample,query=True,value=True)
    cmds.setAttr("defaultArnoldRenderOptions."+sample,value)

def updateSampleFloat(sample):
    value= cmds.floatSliderGrp(sample,query=True,value=True)
    cmds.setAttr("defaultArnoldRenderOptions."+sample,value)

def updateSize(value, type):
    #Set width or height
    cmds.setAttr("defaultResolution."+type, value)
    cmds.evalDeferred('cmds.setAttr("defaultResolution.pixelAspect", 1)') #HACK TO PRESERVE PIXEL ASPECT RATION WITH DEFERRED EVA
    #Update preset format menu
    renderWidth= cmds.getAttr("defaultResolution.width")
    renderHeight = cmds.getAttr("defaultResolution.height")
    if renderWidth == 1280 and renderHeight == 720:
        cmds.optionMenu("renderSize", e=True, value="HD_720")
    elif renderWidth == 1920 and renderHeight == 1080:
        cmds.optionMenu("renderSize", e=True, value="HD_1080")
    else:
        cmds.optionMenu("renderSize", e=True, value="Custom")

def renderSizePreset(preset):
    if preset == "HD_720":
        cmds.setAttr("defaultResolution.height", 720)
        cmds.setAttr("defaultResolution.width", 1280)
        cmds.intField("renderWidth",e=True, value=1280)
        cmds.intField("renderHeigth",e=True, value=720)
        cmds.evalDeferred('cmds.setAttr("defaultResolution.pixelAspect", 1)') #HACK TO PRESERVE PIXEL ASPECT RATION WITH DEFERRED EVAL

    if preset == "HD_1080":
        cmds.setAttr("defaultResolution.height", 1080)
        cmds.setAttr("defaultResolution.width", 1920)
        cmds.intField("renderWidth",e=True, value=1920)
        cmds.intField("renderHeigth",e=True, value=1280)
        cmds.evalDeferred('cmds.setAttr("defaultResolution.pixelAspect", 1)') #HACK TO PRESERVE PIXEL ASPECT RATION WITH DEFERRED EVAL

def aovZFix(state):
        if state ==1:
            if cmds.objExists("aiAOV_Z"):
                if cmds.getAttr("aiAOV_Z.type") != 5:
                    cmds.setAttr("aiAOV_Z.type",5)

        elif state==0:
            print("setting z back to float")
            if cmds.objExists("aiAOV_Z"):
                if cmds.getAttr("aiAOV_Z.type") == 5 or cmds.getAttr("aiAOV_Z.type") == 7:
                    cmds.setAttr("aiAOV_Z.type",4)

def changeCamType():
    cam = cmds.optionMenu("renderCamMenu", query = True, value=True)
    lentil_enable = cmds.checkBox("lentil_enable", query = True, value=True)
    if lentil_enable:
        if cmds.objExists("aiImagerLentil1"):
            cmds.connectAttr("aiImagerLentil1.message", "defaultArnoldRenderOptions.imagers[0]", f=True)
            cmds.setAttr("aiImagerLentil1.enable",1)
        else:
            cmds.createNode( 'aiImagerLentil', n='aiImagerLentil1' )
            cmds.connectAttr("aiImagerLentil1.message", "defaultArnoldRenderOptions.imagers[0]", f=True)
        if cmds.objExists("aiLentilOperator1"):
            cmds.connectAttr("aiLentilOperator1.message","defaultArnoldRenderOptions.operator")
        else:
            cmds.createNode( 'aiLentilOperator', n='aiLentilOperator1' )

        #LENTIL ON
        cmds.setAttr(cam+".ai_translator", "lentil_camera",  type="string")
        cmds.setAttr("aiImagerLentil1.enable",1)

        #turn off variance aov

        #cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",0)
        #cmds.checkBox("outputVarianceAOVs", e=True,value=False)

        #disable progressive
        cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender",0)
        cmds.checkBox("enableProgressiveRender",edit=True, value=0)
        #aovZFix(1)

    #LENTIL OFF
    else:
        #set all cam to prespective (otherwise lentil is still there and prevent progressive rendering)
        allcam = cmds.ls(type="camera")
        for c in allcam:
            try:
                cmds.setAttr(c+".ai_translator", "perspective",  type="string")
            except:
                print("Camera already set to prespective: %s" %c)
        imagerLentilList=cmds.ls( type="aiImagerLentil" )
        #disconnet Imager
        for imager in imagerLentilList:
            try:
                cmds.disconnectAttr("%s.message"%imager, "defaultArnoldRenderOptions.imagers[0]")
            except Exception as e:
                print ("Imager not connected: " + imager)
        try:
            cmds.disconnectAttr("aiLentilOperator1.message","defaultArnoldRenderOptions.operator")
        except Exception as e:
            print(e)
            print ("Lentil Operator not connected: ")

                #print("Oops!", e.__class__, "occurred.")
        #cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",1)
        #cmds.checkBox("outputVarianceAOVs", e=True,value=True)
        #cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender",1)
        #cmds.checkBox("enableProgressiveRender",edit=True, value=1)

        #aovZFix(0)
    #Checking on denoising since camera type change
    denoise_on()
    cmds.select(cam)

def dof():
    cam = cmds.optionMenu("renderCamMenu", query = True, value=True)
    dof_value = cmds.checkBox("aiEnableDOF", query = True, value =True)
    if isLentilInstalled():
        cmds.setAttr(cam+".enableDof", dof_value)
    cmds.setAttr(cam+".aiEnableDOF", dof_value)

def ignore(ignore_name,ignore_value):
    cmds.setAttr("defaultArnoldRenderOptions."+ignore_name, ignore_value)


### DENOISE UTILITAIRE
### DENOISE UTILITAIRE
### DENOISE UTILITAIRE
### DENOISE UTILITAIRE
### DENOISE UTILITAIRE
### DENOISE UTILITAIRE

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
    allAovsList = cmds.ls(type = "aiAOV")
    aovs = []
    ok_list = ["aiAOV_sss","aiAOV_specular","aiAOV_direct","aiAOV_indirect","aiAOV_sheen","aiAOV_transmssion","aiAOV_coat","aiAOV_diffuse","aiAOV_specular_direct", "aiAOV_specular_indirect", "aiAOV_diffuse_direct","aiAOV_diffuse_indirect"]
    for aov in allAovsList:
        if aov in ok_list or aov.startswith("aiAOV_RGBA_"):
            aovs.append(aov)
    return aovs



def denoise_on():

    if cmds.checkBox("outputVarianceAOVs", query=True,value=True)==False:
        remove_denoise_persepective() #Remove all
        cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs", 0)
        remove_denoise_lentil()
    else:
        if not isLentilEnable():
            add_denoise_aovs_perspective() #SET ALL TO ON BY DEFAULT
            #remove_denoise_lentil() #DELETE LENTIL STUFF
            cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs", 1)
            remove_denoise_lentil()
        else:
            remove_denoise_persepective() #DELETE PRESPECTIVE STUFF
            add_denoise_aovs_lentil() #SET ALL TO ON BY DEFAULT
            cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs", 0)


def add_denoise_aovs_lentil():
    aovsNoPrefix = []

    aovs = get_aovs()
    for aov in aovs:
        aov_no_prefix= aov.split("aiAOV_")[-1]
        aovsNoPrefix.append(aov_no_prefix)
    #BUILD LAYER string
    layer_selection =""
    counter = 0
    for aov in aovsNoPrefix:
        if counter == 0:
            layer_selection = "RGBA or " + aov
        else:
            layer_selection=layer_selection+ " or "+aov
        counter += 1

    if cmds.objExists("aiImagerDenoiserOidn1"):
        cmds.connectAttr("aiImagerDenoiserOidn1.message", "defaultArnoldRenderOptions.imagers[1]", f=True)
        cmds.setAttr("aiImagerDenoiserOidn1.enable",1)
    else:
        cmds.createNode( 'aiImagerDenoiserOidn', n='aiImagerDenoiserOidn1' )
        cmds.connectAttr("aiImagerDenoiserOidn1.message", "defaultArnoldRenderOptions.imagers[1]", f=True)
    cmds.setAttr("aiImagerDenoiserOidn1.layer_selection",layer_selection,type="string")
    cmds.setAttr("aiImagerDenoiserOidn1.output_suffix","_denoised",type="string")
    print("Setting Oidn layer_selection to :"+ layer_selection)


def remove_denoise_lentil():
    listConnectionImagers = cmds.listConnections("defaultArnoldRenderOptions.imagers")
    #HACK TO PREVENT "NoneType" is not iterable
    if not listConnectionImagers:
        listConnectionImagers=[]
    #END HACK
    if "aiImagerDenoiserOidn1" in listConnectionImagers:
        cmds.disconnectAttr("aiImagerDenoiserOidn1.message", "defaultArnoldRenderOptions.imagers[1]")
        print(" aiImagerDenoiserOidn disconnected")
    cmds.setAttr("aiImagerDenoiserOidn1.layer_selection","",type="string")


def remove_denoise_persepective():
    allAovs = get_aovs()
    varianceDriverExr, varianceFilter= setup_driver()
    for aov in allAovs:
        try:
            disconnectVariance(aov)
            print (aov + "variance disconneted")
        except Exception as e:
            print (e)

def add_denoise_aovs_perspective():
    allAovs = get_aovs()
    varianceDriverExr, varianceFilter= setup_driver()

    for aov in allAovs:
        try:
            connectVariance(aov,varianceDriverExr,varianceFilter)
            print (aov + " variance connected")
        except Exception as e:
            print (e)



def connectVariance(aov,varianceDriverExr,varianceFilter):
    cmds.connectAttr(varianceDriverExr+".message", aov+'.outputs[1].driver', f=True)
    cmds.connectAttr(varianceFilter+".message", aov+'.outputs[1].filter', f=True)

def disconnectVariance(aov):
    filterList = cmds.listConnections(aov+".outputs[1].filter")
    driverList = cmds.listConnections(aov+".outputs[1].driver")
    if filterList:
        if filterList[0] == "varianceFilter":
            cmds.disconnectAttr(filterList[0]+".message", aov+".outputs[1].filter")
    if driverList:
        if driverList[0] == "varianceDriver":
            cmds.disconnectAttr(driverList[0]+".message", aov+".outputs[1].driver")
