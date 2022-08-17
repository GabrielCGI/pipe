
import maya.mel as mel
import maya.cmds as cmds
import importlib
import os
import json


#Init variables
presets_folder = "R:\\pipeline\\pipe\\maya\\scripts\\tools\\presets_render_setting"
presetDic={}


# List renderable cameras
def getRenderableCameras():
    cameras = cmds.ls(type="camera")
    renderableCameras=[]
    for cam in cameras:
        if cmds.getAttr(cam+".renderable"):
            renderableCameras.append(cam)
    return renderableCameras


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
    try:
        activeCamType = cmds.getAttr(renderableCameras[0]+".ai_translator")
        if activeCamType == "lentil_camera":
            lentil_enable=1
        else:
            lentil_enable=0
    except:
        lentil_enable=0

    #----- Global Features Overrides --------

    cmds.frameLayout( label='Feature Overrides', labelAlign='bottom')
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)
    # -- DOF / MB / LENTIL

    # -- Ignore Overriedes
    #IGNORE SUBDIVISION
    ignore_subdiv_state= cmds.getAttr("defaultArnoldRenderOptions.ignoreSubdivision")
    cmds.checkBox("ignoreSubdivision", label="Ignore Subdivision", value=ignore_subdiv_state, changeCommand=lambda x:ignore("ignoreSubdivision",cmds.checkBox("ignoreSubdivision", query=True, value=True)))
    #IGNORE ATHMO
    ignoreAtmosphere_state= cmds.getAttr("defaultArnoldRenderOptions.ignoreAtmosphere")
    cmds.checkBox("ignoreAtmosphere", label="Ignore Athmosphere", value=ignoreAtmosphere_state, changeCommand=lambda x:ignore("ignoreAtmosphere",cmds.checkBox("ignoreAtmosphere", query=True, value=True)))
    #IGNORE DISPLACEMENT
    ignoreDisplacement_state= cmds.getAttr("defaultArnoldRenderOptions.ignoreDisplacement")
    cmds.checkBox("ignoreDisplacement", label="Ignore Displacment", value=ignoreDisplacement_state, changeCommand=lambda x:ignore("ignoreDisplacement",cmds.checkBox("ignoreDisplacement", query=True, value=True)))
    cmds.setParent("..")

    # -- AOVs Overriedes
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.checkBox("ignoreAov",label="Ignore AOVs", changeCommand=lambda x:aov_enabled(cmds.checkBox("ignoreAov",query=True,value=True)))

    aovList = cmds.ls(type = "aiAOV")
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
    cmds.checkBox("outputVarianceAOVs",label="Output Denoising AOVs",value=cmds.getAttr("defaultArnoldRenderOptions.outputVarianceAOVs"),changeCommand=lambda x:cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs", cmds.checkBox("outputVarianceAOVs", query=True,value=True)))
    cmds.setParent("..")
    cmds.setParent("..")

    #-----  Motion blur --------
    cmds.frameLayout( label='DOF', labelAlign='bottom')
    cmds.rowColumnLayout( numberOfColumns = 2)
    dof_state= cmds.getAttr(renderableCameras[0]+".enableDof")
    cmds.checkBox("aiEnableDOF", label="Depth of Field", value=dof_state, changeCommand=lambda x:dof())
    cmds.checkBox("lentil_enable", label="Lentil", value=lentil_enable, changeCommand=lambda x:changeCamType())
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.text("FStop ")
    cmds.intField("fStop",value=cmds.getAttr(cam+".fStop"), changeCommand=lambda x:cmds.setAttr(cam+".fStop",cmds.intField("fStop",query=True,value=True)))

    cmds.setParent("..")
    cmds.rowColumnLayout( numberOfColumns = 2)
    cmds.text("Samples Mult.")
    cmds.intField("bidirSampleMult",value=cmds.getAttr(cam+".bidirSampleMult"), changeCommand=lambda x:cmds.setAttr(cam+".bidirSampleMult",cmds.intField("bidirSampleMult",query=True,value=True)))
    cmds.setParent("..")
    cam = cmds.optionMenu("renderCamMenu", query = True, value=True)

    cmds.setParent("..")
    cmds.setParent("..")
    cmds.columnLayout(adjustableColumn= True, rowSpacing= 0)

    cmds.setParent("..")

    cmds.frameLayout( label='Motion blur', labelAlign='bottom')
    cmds.checkBox("motion_blur_enable", label="Enable", value=cmds.getAttr("defaultArnoldRenderOptions.motion_blur_enable"), changeCommand=lambda x:motion_blur_enable(cmds.checkBox("motion_blur_enable", query=True,value=True)))
    cmds.checkBox("ignoreMotionBlur", label="Instantaneaous Shutter", value=cmds.getAttr("defaultArnoldRenderOptions.ignoreMotionBlur"), changeCommand=lambda x:cmds.setAttr("defaultArnoldRenderOptions.ignoreMotionBlur",cmds.checkBox("ignoreMotionBlur", query=True, value=True)))
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"GISpecularSamples")
    cmds.intSliderGrp( "motion_steps", field=True, label="Keys", minValue=2, maxValue=10, fieldMinValue=0, fieldMaxValue=30, value=cmds.getAttr("defaultArnoldRenderOptions.motion_steps"), changeCommand=lambda x:updateSample("motion_steps") )
    cmds.floatSliderGrp( "motion_frames", field=True, label="Length", minValue=0, maxValue=1, sliderStep=0.01, precision=3,fieldMinValue=0, fieldMaxValue=1, value=cmds.getAttr("defaultArnoldRenderOptions.motion_frames"), changeCommand=lambda x:cmds.setAttr("defaultArnoldRenderOptions.motion_frames",cmds.floatSliderGrp("motion_frames",query=True,value=True )) )

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
    cmds.checkBox("enableProgressiveRender", label="Enable Progressive Render", value=cmds.getAttr("defaultArnoldRenderOptions.enableProgressiveRender"), changeCommand=lambda x:enableProgessiveRender())
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"AASamples")

    cmds.intSliderGrp( "AASamples", field=True, label="Camera (AA)", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=30, value=samples_value, changeCommand=lambda x:updateSample("AASamples") )

    #Diffuse
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"GIDiffuseSamples")
    cmds.intSliderGrp( "GIDiffuseSamples", field=True, label="Diffuse", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=30, value=samples_value, changeCommand=lambda x:updateSample("GIDiffuseSamples") )

    #Specualr
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"GISpecularSamples")
    cmds.intSliderGrp( "GISpecularSamples", field=True, label="Specular", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=30, value=samples_value, changeCommand=lambda x:updateSample("GISpecularSamples") )


    #Transmssion
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"GITransmissionSamples")
    cmds.intSliderGrp( "GITransmissionSamples", field=True, label="Transmission", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=30, value=samples_value, changeCommand=lambda x:updateSample("GITransmissionSamples") )

    #SSS
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"GISssSamples")
    cmds.intSliderGrp( "GISssSamples", field=True, label="SSS", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=30, value=samples_value, changeCommand=lambda x:updateSample("GISssSamples") )

    #Volume Indirect
    samples_value= cmds.getAttr("defaultArnoldRenderOptions."+"GIVolumeSamples")
    cmds.intSliderGrp( "GIVolumeSamples", field=True, label="Volume Indirect", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=30, value=samples_value, changeCommand=lambda x:updateSample("GIVolumeSamples") )

    cmds.separator( height=10, style='in' )

    #RAY DEPTH
    #Ray depth diffuse
    samples_value= cmds.getAttr("defaultArnoldRenderOptions.GIDiffuseDepth")
    cmds.intSliderGrp( "GIDiffuseDepth", field=True, label="Ray Depth Diffuse", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=12, value=samples_value, changeCommand=lambda x:updateSample("GIDiffuseDepth") )
    #Ray depth specular
    samples_value= cmds.getAttr("defaultArnoldRenderOptions.GISpecularDepth")
    cmds.intSliderGrp( "GISpecularDepth", field=True, label="Ray Depth Specular", minValue=0, maxValue=12, fieldMinValue=0, fieldMaxValue=12, value=samples_value, changeCommand=lambda x:updateSample("GISpecularDepth") )

    #ADAPTATIVE SAMPLING
    cmds.frameLayout( label='Adaptive Sampling', labelAlign='bottom')
    #Enable adaptative

    cmds.checkBox("enableAdaptiveSampling", label="Enable", value=cmds.getAttr("defaultArnoldRenderOptions.enableAdaptiveSampling"), changeCommand=lambda x:setAdaptatif())
    AASamplesMax_state = cmds.getAttr("defaultArnoldRenderOptions.AASamplesMax")
    cmds.intSliderGrp( "AASamplesMax", field=True, label="Max. Camera (AA)", minValue=0, maxValue=25, fieldMinValue=0, fieldMaxValue=40, value=AASamplesMax_state, changeCommand=lambda x:cmds.setAttr("defaultArnoldRenderOptions.AASamplesMax", cmds.intSliderGrp("AASamplesMax",query=True,value=True)) )

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
        cmds.checkBox("ignoreMotionBlur",edit= True, editable=state)
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
            print(param_dic)

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

def setAdaptatif():
    cmds.setAttr("defaultArnoldRenderOptions.enableAdaptiveSampling",cmds.checkBox("enableAdaptiveSampling", query=True, value=True))
    if cmds.checkBox("enableAdaptiveSampling", query=True, value=True) == True:
        if cmds.checkBox("enableProgressiveRender", query=True, value=True) == True:
            msg = cmds.confirmDialog( title='Disabling Progressive', message='Progressive render is not working well with Adaptative Sampling.', button=['Disable Progressive'], defaultButton='Disable Progressive', cancelButton='No', dismissString='No' )
            if msg == "Disable Progressive":
                cmds.checkBox("enableProgressiveRender", edit=True, value=False)

def enableProgessiveRender():
    cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender",cmds.checkBox("enableProgressiveRender", query=True, value=True))
    if cmds.checkBox("enableProgressiveRender", query=True, value=True) == True:
        if cmds.checkBox("enableAdaptiveSampling", query=True, value=True) == True:
            msg = cmds.confirmDialog( title='Disabling Adaptative', message='Adaptative sampling is not working well with Progressive render.', button=['Disable Adaptative'], defaultButton='Disable Adaptative', cancelButton='No', dismissString='No' )
            if msg == "Disable Adaptative":
                cmds.checkBox("enableAdaptiveSampling", edit=True, value=False)

def aov_enabled(value):
    aovList = cmds.ls(type = "aiAOV")
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
    print ("defaultArnoldRenderOptions."+sample)


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
                    msg = cmds.confirmDialog( title='Fix Z AOV ', message='Z AOV with lentil has a bug. Need to change data type. \n (RGB=Gaussian and VECTOR=Closet) ', button=['SET TO RGB'], defaultButton='SET To RGB', cancelButton='No', dismissString='No' )
                    if msg == "SET TO RGB":
                        print(msg)
                        cmds.setAttr("aiAOV_Z.type",5)
                    if msg == "SET TO VECTOR":
                        cmds.setAttr("aiAOV_Z.type",7)
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
        #LENTIL ON
        cmds.setAttr(cam+".ai_translator", "lentil_camera",  type="string")
        cmds.setAttr("aiImagerLentil1.enable",1)

        #turn off variance aov
        cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",0)
        cmds.checkBox("outputVarianceAOVs", e=True,value=False)

        #disable progressive
        cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender",0)
        cmds.checkBox("enableProgressiveRender",edit=True, value=0)
        aovZFix(1)
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
                #print("Oops!", e.__class__, "occurred.")
        cmds.setAttr("defaultArnoldRenderOptions.outputVarianceAOVs",1)
        cmds.checkBox("outputVarianceAOVs", e=True,value=True)
        cmds.setAttr("defaultArnoldRenderOptions.enableProgressiveRender",1)
        #cmds.checkBox("enableProgressiveRender",edit=True, value=1)
        aovZFix(0)
    cmds.select(cam)

def dof():
    cam = cmds.optionMenu("renderCamMenu", query = True, value=True)
    dof_value = cmds.checkBox("aiEnableDOF", query = True, value =True)
    cmds.setAttr(cam+".enableDof", dof_value)
    cmds.setAttr(cam+".aiEnableDOF", dof_value)

def ignore(ignore_name,ignore_value):
    cmds.setAttr("defaultArnoldRenderOptions."+ignore_name, ignore_value)
