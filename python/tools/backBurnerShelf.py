##===========================================================================##
##===========================================================================##
## To BackBurner. 1.2                                                        ##
## By Mariano Antico                                                         ##
## Barraca Post                                                              ##
## www.barraca.com.ar                                                        ##
## www.marianoantico.blogspot.com                                            ##
## Last Updated: January 20, 2012.                                           ##
## All Rights Reserved .                                                     ##
##                                                                           ##
## Description:                                                              ##
## Send to Backburner                                                        ##
##                                                                           ##
## Tutorials:                                                                ##
## www.marianoantico.blogspot.com                                            ##
## http://vimeo.com/34227651                                                 ##
##                                                                           ##
## Run:                                                                      ##
## backBurner()                                                              ##
##                                                                           ##
##===========================================================================##
##===========================================================================##

#import libraries

import maya.cmds as mc
import os
import webbrowser
import maya.mel as mm
import tempfile
import re

##---------------------------------------------------------------------------##
#Interface save window
def setRenderFolder():

    scenePath = mc.file(q=True, sceneName=True)
    sceneDir = os.path.abspath(os.path.join(scenePath, os.pardir))
    parentDir = os.path.abspath(os.path.join(sceneDir, os.pardir))
    renderOutDir = os.path.join(parentDir,"render_out")
    if not os.path.exists(renderOutDir):
        os.makedirs(renderOutDir)

    chosenFolder = mc.fileDialog2(dialogStyle=2, fileMode=2, dir=renderOutDir)
    mc.textField('renderFolder', edit=1, text=chosenFolder[0])

def backBurner():

    if mc.window("BburnWin", query=True, exists= True):
        mc.deleteUI("BburnWin")

    saveWindow = mc.confirmDialog( title='Save Scene', message='Before creating a Backburner job would you like to save current scene file?', button=['Yes', 'Ignore', 'No'], defaultButton='Yes', cancelButton='No', dismissString='Ignore' )
    if (saveWindow == 'Yes'):
        saveName = mc.file(query=True, sceneName=True)
        if(saveName == ''):
            mc.file( rename='untitled.mb' )
            mc.file( save=True)
        mc.file( save=True)
        bburnerWindow()
    elif (saveWindow == 'Ignore'):
        bburnerWindow()
    elif (saveWindow == 'No'):
        print ('Cancelled by user')

##---------------------------------------------------------------------------##
#Interface backburner

def bburnerWindow():

    #Interface

    if mc.window("BburnWin", query=True, exists= True):
        mc.deleteUI("BburnWin")

    #create window
    pikoWindow = mc.window( 'BburnWin', title="Send to BackBurner 1.2                           by Mariano Antico", sizeable = False)

    ##---------------------------------------------------------------------------##
    #menu bar
    menuBB = mc.menuBarLayout()
    m1 = mc.menu(label="File", enable=True)
    m1Item = mc.menuItem( label="Reset values", enable=True, command= 'defaultValuesBb()')
    m2 = mc.menu(label="Window", enable=True)
    m2Item1 = mc.menuItem( label="Render View", enable=True, command = "renderViewWindow()")
    m2Item2 = mc.menuItem( label="Render Settings", enable=True, command = "renderSettingsWindow()")
    m3 = mc.menu(label="Help", enable=True)
    m3Item = mc.menuItem( label="About", enable=True, command = "myBlog()")

    ##---------------------------------------------------------------------------##
    #frame job settings
    frameJob = mc.frameLayout( label='JOB SETTINGS:', borderStyle='out', collapsable=True, marginHeight=2)

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 10)])

    #Job Name
    mc.text(font="plainLabelFont",label="Job Name", align='right')
    jobName = mc.textField('jobNameTF',font="plainLabelFont", text= jobNameDef())
    mc.separator(style='none')

    #Description
    mc.text(font="plainLabelFont",label="Description", align='right')
    description = mc.textField('descriptionTF', font="plainLabelFont", text= "")
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 20)])
    #Render Out
    mc.text(font="plainLabelFont",label="Render folder", align='right')
    renderFolder = mc.textField('renderFolder', font="plainLabelFont", text= "")
    mc.button (label="...", command='setRenderFolder()')
    mc.separator(style='none')


    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 2, columnWidth=[(1, 90), (2, 200)], columnSpacing = (2, 5))

    #Range
    mc.text(font="plainLabelFont",label="Range", align='right')
    mc.radioButtonGrp('rangeRB', numberOfRadioButtons=2, labelArray2=['Frame Range', 'Frames'], select=1, changeCommand='switchFrames()')

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 4, columnWidth=[(1, 90), (2, 90), (3, 110)], columnSpacing = (3, 5))

    #Start Frame
    mc.text('startFrameTX', font="plainLabelFont",label="Start Frame", align='right')
    startFrame = mc.intField('startFrameIF', value=0)

    # timeline Range Btn
    timelineBtn = mc.button('timelineBTN', label = 'Timeline Range', command='timelineRange()')
    mc.separator(style='none')

    #End Frame
    mc.text('endFrameTX', font="plainLabelFont",label="End Frame", align='right')
    endFrame = mc.intField('endFrameIF', value=100)

    # Render Range Btn
    renderBtn = mc.button('renderBTN', label = 'Render Range', command='renderRange()')
    mc.separator(style='none')

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 205)])

    # Frames
    mc.text('framesTX', font="plainLabelFont", enable=False, label="Frames", align='right')
    frames = mc.textField('framesTF', enable=False, font="plainLabelFont", text= "")
    mc.text('exampleTX', font="plainLabelFont", enable=False, label=" (e.g. 1,3,5-12)", align='left')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 90), (3, 200)], columnSpacing = (3, 5))

    #Priority
    mc.text(font="plainLabelFont",label="Priority", align='right')
    priority = mc.intField('priorityIF', value=50)

    #Critical
    mc.checkBox('criticalCB', label='Critical', value=False )

    #Task Size
    mc.text('taskSizeTX', font="plainLabelFont",label="Task Size", align='right')
    taskSize = mc.intField('taskSizeIF', value=1)

    #Skip Existing Files
    mc.checkBox('skipExistingFilesCB', label='Skip Existing Files', value=False, changeCommand='skipBtn()')

    #Frame Padding
    mc.text(font="plainLabelFont",label="Frame Padding", align='right')
    framePadding = mc.intField('framePaddingIF', value=4)
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 4, columnWidth=[(1, 90), (2, 90), (3, 85)])

    #Renderer
    mc.text(font="plainLabelFont",label="Renderer", align='right')
    mc.optionMenu('rendererOM' )
    mc.menuItem( label='Scene Renderer' )
    mc.menuItem( label='Mental Ray      ' )
    mc.menuItem( label='Maya Software   ' )
    mc.menuItem( label='Maya Hardware      ' )
    mc.menuItem( label='Vector      ' )

    #Verbosity
    mc.text(font="plainLabelFont",label=" Verbosity ", align='right')
    mc.optionMenu('verbosityOM')
    mc.menuItem( label='0 - No Messages')
    mc.menuItem( label='1 - Fatal' )
    mc.menuItem( label='2 - Error' )
    mc.menuItem( label='3 - Warning' )
    mc.menuItem( label='4 - Info' )
    mc.menuItem( label='5 - Progress' )
    mc.menuItem( label='6 - Detailed' )
    mc.optionMenu('verbosityOM', edit=True, select=6)

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 10)])

    #Additional Options
    mc.text(font="plainLabelFont",label="Additional Options", align='right')
    mc.textField('additionalOptionsTF', font="plainLabelFont", text= "")
    mc.separator(style='none')

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 2, columnWidth=[(1, 90), (2, 280)], columnSpacing = (2, 5))

    #Render Mode
    mc.text(font="plainLabelFont",label="Render Mode", align='right')
    mc.radioButtonGrp('renderModeRB', numberOfRadioButtons=3, labelArray3=['Renderable Layers', 'Each Render Layers', 'Current'], select=2, changeCommand = 'switchRenderMode()')

    mc.setParent('..')
    mc.setParent('..')

    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##

    #frame backburner settings
    frameBburn = mc.frameLayout( label='BACKBURNER SETTINGS:', borderStyle='out', collapsable=True, marginHeight=2)
    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 10)])

    #Manager Name
    mc.text(font="plainLabelFont",label="Manager Name", align='right')
    managerName = mc.textField('managerNameTF', font="plainLabelFont", text= "192.168.0.39")
    mc.separator(style='none')

    #Server List
    mc.text('serverListTX', font="plainLabelFont",label="Server List", align='right')
    serverList = mc.textField('serverListTF', font="plainLabelFont", text= "", changeCommand='switchServer()')
    mc.separator(style='none')

    #Server Group
    mc.text('serverGroupTX', font="plainLabelFont",label="Server Group", align='right')
    serverGroup = mc.textField('serverGroupTF', font="plainLabelFont", text= "", changeCommand='switchServer()')
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 60)])

    #Server Count
    mc.text(font="plainLabelFont",label="Server Count", align='right')
    serverCount = mc.intField('serverCountIF', value=0)
    mc.separator(style='none')

    #Server Port
    mc.text(font="plainLabelFont",label="Port", align='right')
    portBb = mc.intField('portIF', value=3234)
    mc.separator(style='none')

    # timeout
    mc.text(font="plainLabelFont",label="Timeout", align='right')
    timeoutTF = mc.intField('timeoutIF', value=600)
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 60)],columnSpacing = (2, 5))

    #Manually Start
    mc.text(font="plainLabelFont",label="Manually Start Job", align='right')
    mc.checkBox('manualStartCB', label='' )
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 270), (3, 25)])

    # Render Path
    mc.text(font="plainLabelFont",label="Render Path", align='right')
    renderPath = mc.textField('renderPathTF', font="plainLabelFont", text= "C:/Program Files/Autodesk/Maya2019/bin/Render")
    renderPathBtn = mc.button( label = '...', command= 'renderPathDialog()')

    # Backburner Path
    mc.text(font="plainLabelFont",label="Backburner Path", align='right')
    bburnerPath = mc.textField('bburnerPathTF', font="plainLabelFont", text= "C:/Program Files (x86)/Autodesk/Backburner/cmdjob.exe")
    bburnerPathBtn = mc.button( label = '...', command= 'backburnerPathDialog()')

    mc.setParent('..')
    mc.setParent('..')

    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##

    #frame backburner settings
    frameHelp = mc.frameLayout( label='HELP:', borderStyle='out', collapsable=True, collapse=True, marginHeight=2)

    mc.rowColumnLayout( numberOfColumns = 1)

    mc.separator(style='none', height=2)
    mc.text(font="boldLabelFont",label="Command Line Help:", align='left')
    mc.separator(style='none', height=4)

    helpScrollField = mc.scrollField('helpST', font="plainLabelFont", wordWrap=True, editable=False, height=420)

    helpText = 'Usage: render [options] filename:\n'
    helpText += '       where "filename" is a Maya ASCII or a Maya binary file.\n\n'

    helpText += 'Common options:\n'
    helpText += '\n'
    helpText += '  -help                          Print help\n'
    helpText += '  -test                          Print Mel commands but do not execute them\n'
    helpText += '  -verb                         Print Mel commands before they are executed\n'
    helpText += '  -keepMel                   Keep the temporary Mel file\n'
    helpText += '  -listRenderers           List all available renderers\n'
    helpText += '  -renderer string        Use this specific renderer\n'
    helpText += '  -r string                    Same as -renderer\n'
    helpText += '  -proj string               Use this Maya project to load the file\n'
    helpText += '  -log string                 Save output into the given file\n'

    helpText += '\n'
    helpText += 'Specific options for renderer "default": Use the renderer stored in the Maya file\n'

    helpText += '\n'
    helpText += 'General purpose flags:\n'
    helpText += '\n'
    helpText += '  -rd path                    Directory in which to store image file\n'
    helpText += '  -of string                  Output image file format. See the Render Settings\n'
    helpText += '                                   window to find available formats\n'
    helpText += '  -im filename              Image file output name\n'

    helpText += '\n'
    helpText += 'Frame numbering options:\n'
    helpText += '\n'
    helpText += '  -s float                     Starting frame for an animation sequence\n'
    helpText += '  -e float                     End frame for an animation sequence\n'
    helpText += '  -b float                     By frame (or step) for an animation sequence\n'
    helpText += '  -pad int                    Number of digits in the output image frame file\n'
    helpText += '                                  name extension\n'
    helpText += '  -rfs int                      Renumber Frame Start: number for the first image\n'
    helpText += '                                  when renumbering frames\n'
    helpText += '  -rfb int                     Renumber Frame By (or step) used for renumbering\n'
    helpText += '                                  frames\n'
    helpText += '  -fnc int                     File Name Convention: any of name, name.ext, ... \n'
    helpText += '                                  See the Render Settings window to find available\n'
    helpText += '                                  options.Use namec and namec.ext for Multi Frame\n'
    helpText += '                                  Concatenated formats. As a shortcut, numbers 1,\n'
    helpText += '                                  2, ... can also be used\n'

    helpText += '\n'
    helpText += 'Camera options:\n'
    helpText += '\n'
    helpText += '  -cam name              Specify which camera to be rendered\n'
    helpText += '  -rgb boolean           Turn RGB output on or off\n'
    helpText += '  -alpha boolean        Turn Alpha output on or off\n'
    helpText += '  -depth boolean       Turn Depth output on or off\n'
    helpText += '  -iip                           Ignore Image Planes. Turn off all image planes\n'
    helpText += '                                  before rendering\n'

    helpText += '\n'
    helpText += 'Resolution options:\n'
    helpText += '\n'
    helpText += '  -x int                                 Set X resolution of the final image\n'
    helpText += '  -y int                                 Set Y resolution of the final image\n'
    helpText += '  -percentRes float             Renders the image using percent of the\n'
    helpText += '                                           resolution\n'
    helpText += '  -ard float                          Device aspect ratio for the rendered image\n'
    helpText += '  -par float                          Pixel aspect ratio for the rendered image\n'

    helpText += '\n'
    helpText += 'Render Layers and Passes:\n'
    helpText += '\n'
    helpText += '  -rl boolean|name(s)          Render each render layer separately\n'
    helpText += '  -rp boolean|name(s)        Render passes separately. \'all\' will render all\n'
    helpText += '                                           passes\n'
    helpText += '  -sel boolean|name(s)       Selects which objects, groups and/or sets to\n'
    helpText += '                                           render\n'
    helpText += '  -l boolean|name(s)           Selects which display and render layers to\n'
    helpText += '                                           render\n'

    helpText += '\n'
    helpText += 'Mel callbacks:\n'
    helpText += '\n'
    helpText += '  -preRender string             Mel code executed before rendering\n'
    helpText += '  -postRender string           Mel code executed after rendering\n'
    helpText += '  -preLayer string                Mel code executed before each render layer\n'
    helpText += '  -postLayer string              Mel code executed after each render layer\n'
    helpText += '  -preFrame string               Mel code executed before each frame\n'
    helpText += '  -postFrame string             Mel code executed after each frame\n'
    helpText += '  -pre string                         Obsolete flag\n'
    helpText += '  -post string                       Obsolete flag\n'

    helpText += '\n'
    helpText += 'Specific options for the layers who use Maya software renderer:\n'

    helpText += '\n'
    helpText += 'Anti-aliasing quality only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:eaa int                   The anti-aliasing quality of EAS (Abuffer). One\n'
    helpText += '                                       of: highest(0), high(1), medium(2), low(3)\n'
    helpText += '  -sw:ss int                     Global number of shading samples per surface in a\n'
    helpText += '                                       pixel\n'
    helpText += '  -sw:mss int                   Maximum number of adaptive shading samples\n'
    helpText += '                                       per surface in a pixel\n'
    helpText += '  -sw:mvs int                   Number of motion blur visibility samples\n'
    helpText += '  -sw:mvm int                  Maximum number of motion blur visibility samples\n'
    helpText += '  -sw:pss int                    Number of particle visibility samples\n'
    helpText += '  -sw:vs int                     Global number of volume shading samples\n'
    helpText += '  -sw:ufil boolean            If true, use the multi-pixel filtering; otherwise\n'
    helpText += '                                       use single pixel filtering\n'
    helpText += '  -sw:pft int                    When useFilter is true, identifies one of the\n'
    helpText += '                                       following filters: box(0), triangle(2), gaussian(4),\n'
    helpText += '                                       quadratic(5)\n'
    helpText += '  -sw:pfx float                 When useFilter is true, defines the X size of the\n'
    helpText += '                                       filter\n'
    helpText += '  -sw:pfy float                 When useFilter is true, defines the Y size of the\n'
    helpText += '                                       filter\n'
    helpText += '  -sw:rct float                  Red channel contrast threshold\n'
    helpText += '  -sw:gct float                 Green channel contrast threshold\n'
    helpText += '  -sw:bct float                  Blue channel contrast threshold\n'
    helpText += '  -sw:cct float                  Pixel coverage contrast threshold (default is\n'
    helpText += '                                       1.0/8.0)\n'

    helpText += '\n'
    helpText += 'Raytracing quality only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:ert boolean            Enable ray tracing\n'
    helpText += '  -sw:rfl int                      Maximum ray-tracing reflection level\n'
    helpText += '  -sw:rfr int                     Maximum ray-tracing refraction level\n'
    helpText += '  -sw:sl int                       Maximum ray-tracing shadow ray depth\n'

    helpText += '\n'
    helpText += 'Field Options only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:field boolean         Enable field rendering. When on, images are\n'
    helpText += '                                       interlaced\n'
    helpText += '  -sw:pal                         When field rendering is enabled, render even field\n'
    helpText += '                                       first (PAL)\n'
    helpText += '  -sw:ntsc                       When field rendering is enabled, render odd field\n'
    helpText += '                                       first (NTSC)\n'

    helpText += '\n'
    helpText += 'Motion Blur only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:mb boolean                 Motion blur on/off\n'
    helpText += '  -sw:mbf float                     Motion blur by frame\n'
    helpText += '  -sw:sa float                       Shutter angle for motion blur (1-360)\n'
    helpText += '  -sw:mb2d boolean             Motion blur 2D on/off\n'
    helpText += '  -sw:bll float                       2D motion blur blur length\n'
    helpText += '  -sw:bls float                      2D motion blur blur sharpness\n'
    helpText += '  -sw:smv int                       2D motion blur smooth value\n'
    helpText += '  -sw:smc boolean               2D motion blur smooth color on/off\n'
    helpText += '  -sw:kmv boolean               Keep motion vector for 2D motion blur on/off\n'

    helpText += '\n'
    helpText += 'Render Options only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:ifg boolean                Use the film gate for rendering if false\n'
    helpText += '  -sw:edm boolean             Enable depth map usage\n'
    helpText += '  -sw:g float                       Gamma value\n'
    helpText += '  -sw:premul boolean         Premultiply color by the alpha value\n'
    helpText += '  -sw:premulthr float          When premultiply is on, defines the threshold \n'
    helpText += '                                           used to determine whether to premultiply\n'
    helpText += '                                           or not\n'

    helpText += '\n'
    helpText += 'Memory and Performance only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:uf boolean                 Use the tessellation file cache\n'
    helpText += '  -sw:oi boolean                  Dynamically detects similarly tessellated\n'
    helpText += '                                           surfaces\n'
    helpText += '  -sw:rut boolean                Reuse render geometry to generate depth\n'
    helpText += '                                           maps\n'
    helpText += '  -sw:udb boolean              Use the displacement bounding box scale to\n'
    helpText += '                                           optimize\n'
    helpText += '                                           displacement-map performance\n'
    helpText += '  -sw:mm int                        Renderer maximum memory use\n'
    helpText += '                                           (in Megabytes)\n'

    helpText += '\n'
    helpText += 'Specific options for the layers who use Maya hardware renderer:\n'
    helpText += '\n'
    helpText += 'Quality flags only for Maya hardware renderer:\n'
    helpText += '\n'
    helpText += '  -hw:ehl boolean                Enable high quality lighting\n'
    helpText += '  -hw:ams boolean              Accelerated multi sampling\n'
    helpText += '  -hw:ns int                         Number of samples per pixel\n'
    helpText += '  -hw:tsc boolean               Transparent shadow maps\n'
    helpText += '  -hw:ctr int                        Color texture resolution\n'
    helpText += '  -hw:btr int                        Bump texture resolution\n'
    helpText += '  -hw:tc boolean                 Enable texture compression\n'

    helpText += '\n'
    helpText += 'Render options only for Maya hardware renderer:\n'
    helpText += '\n'
    helpText += '  -hw:c boolean                              Culling mode.\n'
    helpText += '                0: per object.\n'
    helpText += '                1: all double sided.\n'
    helpText += '                2: all single sided\n'
    helpText += '  -hw:sco boolean                           Enable small object culling\n'
    helpText += '  -hw:ct float                                   Small object culling threshold\n'

    helpText += '\n'
    helpText += 'Mel callbacks only for Maya hardware renderer:\n'
    helpText += '\n'
    helpText += '  -hw:mb boolean                 Enable motion blur\n'
    helpText += '  -hw:mbf float                     Motion blur by frame\n'
    helpText += '  -hw:ne int                          Number of exposures\n'
    helpText += '  -hw:egm boolean               Enable geometry mask\n'

    helpText += '\n'
    helpText += 'Specific options for the layers who use Mentalray renderer\n'
    helpText += '\n'
    helpText += 'Other only for Mentalray renderer:\n'
    helpText += '\n'
    helpText += '  -mr:v/mr:verbose int           Set the verbosity level.\n'
    helpText += '        0 - to turn off messages\n'
    helpText += '        1 - for fatal errors only\n'
    helpText += '        2 - for all errors\n'
    helpText += '        3 - for warnings\n'
    helpText += '        4 - for informational messages\n'
    helpText += '        5 - for progress messages\n'
    helpText += '        6 - for detailed debugging messages\n'
    helpText += '\n'
    helpText += '   -mr:rt/mr:renderThreads int            Specify the number of rendering.\n'
    helpText += '                                                            threads.\n'
    helpText += '   -mr:art/mr:autoRenderThreads       Automatically determine the number\n'
    helpText += '                                                            of rendering threads.\n'
    helpText += '   -mr:mem/mr:memory int                   Set the memory limit (in MB).\n'
    helpText += '   -mr:aml/mr:autoMemoryLimit           Compute the memory limit\n'
    helpText += '                                                            automatically.\n'
    helpText += '   -mr:ts/mr:taskSize int                       Set the pixel width/height of the\n'
    helpText += '                                                            render tiles.\n'
    helpText += '   -mr:at/mr:autoTiling                         Automatically determine optimal tile\n'
    helpText += '                                                            size.\n'
    helpText += '   -mr:fbm/mr:frameBufferMode int     Set the frame buffer mode.\n'
    helpText += '        0 in-memory framebuffers\n'
    helpText += '        1 memory mapped framebuffers\n'
    helpText += '        2 cached framebuffers\n'
    helpText += '  -mr:rnm boolean                Network rendering option. If true, mental ray\n'
    helpText += '                                            renders almost everything on slave machines,\n'
    helpText += '                                            thus reducing the workload on the\n'
    helpText += '        master machine\n'
    helpText += '  -mr:lic string                       Specify satellite licensing option. mu/unlimited\n'
    helpText += '                                            or mc/complete.\n'
    helpText += '  -mr:reg int int int int          Set sub-region pixel boundary of the final\n'
    helpText += '                                            image: left, right, bottom, top\n'

    helpText += '\n'
    helpText += '\n'
    helpText += ' *** Remember to place a space between option flags and their arguments. ***\n'
    helpText += 'Any boolean flag will take the following values as TRUE: on, yes, true, or 1.'
    helpText += 'Any boolean flag will take the following values as FALSE: off, no, false, or 0.\n'

    helpText += '                 e.g. -s 1 -e 10 -x 512 -y 512 -cam persp -mr:v 5 file.\n'
    helpText += '\n'
    helpText += '\n'

    helpText += 'Send to Backburner 1.2 by Mariano Antico   \n'
    helpText += 'www.marianoantico.blogspot.com'

    mc.scrollField('helpST', edit=True, text=helpText)

    mc.setParent('..')
    mc.setParent('..')

    ##---------------------------------------------------------------------------##
    #Submit buttons

    mc.rowColumnLayout( numberOfColumns = 3)

    submitCloseBtn = mc.button( label = 'Submit Job and Close', command='submitCloseBtn()')
    submitBtn = mc.button( label = 'Submit', command='submitBtn()')
    closeBtn = mc.button( label = 'Close', command='closeBtn()')

    mc.showWindow( pikoWindow )

##---------------------------------------------------------------------------##
##---------------------------------------------------------------------------##
##---------------------------------------------------------------------------##

#Child def
# my Blog
def myBlog():
    url = 'http://www.marianoantico.blogspot.com/'
    webbrowser.open_new(url)

# render view window
def renderViewWindow():
    mm.eval('RenderViewWindow;')

# render settings window
def renderSettingsWindow():
    mm.eval('unifiedRenderGlobalsWindow;')

# job Name window
def jobNameDef():
    fileName = mc.file(query=True, shortName=True, sceneName=True)
    fileName = fileName.split(".")[0] + fileName.split(".")[-2]
    if (fileName == '_'):
        fileName = 'untitled'
    return(fileName)

# default window
def defaultValuesBb():
    mc.textField('jobNameTF', edit=True, text= jobNameDef())
    mc.textField('descriptionTF', edit=True, text= "")
    mc.textField('renderOut', edit=True, text= "B://test/")
    mc.radioButtonGrp('rangeRB', edit=True, select=1)
    switchFramesDefault()
    mc.intField('priorityIF', edit=True, value=50)
    mc.checkBox('criticalCB', edit=True, value=False )
    mc.text('taskSizeTX', edit=True, enable=True)
    mc.intField('taskSizeIF', edit=True, value=1, enable=True)
    mc.intField('framePaddingIF', edit=True, value=4)
    mc.optionMenu('rendererOM', edit=True, select=1)
    mc.optionMenu('verbosityOM', edit=True, select=6)
    mc.textField('additionalOptionsTF', edit=True, text= "")
    mc.radioButtonGrp('renderModeRB', edit=True, select= 2)
    mc.checkBox('skipExistingFilesCB', edit=True, value=False)
    switchRenderMode()

    mc.textField('managerNameTF', edit=True, text= "")
    mc.text('serverListTX', edit=True, enable=True)
    mc.textField('serverListTF', edit=True, text= "", enable=True)
    mc.text('serverGroupTX', edit=True, enable=True)
    mc.textField('serverGroupTF', edit=True, text= "", enable=True)
    mc.intField('serverCountIF', edit=True, value= 0)
    mc.intField('portIF', edit=True, value= 0)
    mc.intField('timeoutIF', edit=True, value= 600)
    mc.checkBox('manualStartCB', edit=True, value=False )
    mc.textField('renderPathTF', edit=True, text= "C:/Program Files/Autodesk/Maya2011/bin/Render")
    mc.textField('bburnerPathTF', edit=True, text= "C:/Program Files (x86)/Autodesk/Backburner/cmdjob.exe")

# error Message Text Field
def errorMessageTF(property=None, errorName=None):
    if (mc.textField(property, query=True, text=True ) == ''):
        mc.error('Please complete ' + errorName + ' field.')
        errorReturnTF = ''
    errorReturnTF = mc.textField(property, query=True, text=True )
    return errorReturnTF

# error Message Integer Field
def errorMessageIF(property=None, errorName=None):
    if (mc.intField(property, query=True, value=True ) == ''):
        mc.error('Please complete ' + errorName + ' field.')
        errorReturnIF = ''
    errorReturnIF = mc.intField(property, query=True, value=True )
    return errorReturnIF

# switchFrames Default window
def switchFramesDefault():
    rangeSelected = mc.radioButtonGrp('rangeRB', query=True, select=True)
    if (rangeSelected == 1):
        mc.text('startFrameTX', edit=True, enable=True)
        mc.text('endFrameTX', edit=True, enable=True)
        mc.intField('startFrameIF', edit=True, enable=True, value=0)
        mc.intField('endFrameIF', edit=True, enable=True, value=100)
        mc.button('timelineBTN', edit=True, enable=True)
        mc.button('renderBTN', edit=True, enable=True)

        mc.text('framesTX', edit=True, enable=False)
        mc.textField('framesTF', edit=True, enable=False, text= "")
    else:
        mc.text('startFrameTX', edit=True, enable=False)
        mc.text('endFrameTX', edit=True, enable=False)
        mc.intField('startFrameIF', edit=True, enable=False, value=0)
        mc.intField('endFrameIF', edit=True, enable=False, value=100)
        mc.button('timelineBTN', edit=True, enable=False)
        mc.button('renderBTN', edit=True, enable=False)

        mc.text('framesTX', edit=True, enable=True)
        mc.textField('framesTF', edit=True, enable=True, text= "")

# switchFrames window
def switchFrames():
    rangeSelected = mc.radioButtonGrp('rangeRB', query=True, select=True)
    if (rangeSelected == 1):
        mc.text('startFrameTX', edit=True, enable=True)
        mc.text('endFrameTX', edit=True, enable=True)
        mc.intField('startFrameIF', edit=True, enable=True)
        mc.intField('endFrameIF', edit=True, enable=True)
        mc.button('timelineBTN', edit=True, enable=True)
        mc.button('renderBTN', edit=True, enable=True)

        mc.text('framesTX', edit=True, enable=False)
        mc.textField('framesTF', edit=True, enable=False, text= "")
    else:
        mc.text('startFrameTX', edit=True, enable=False)
        mc.text('endFrameTX', edit=True, enable=False)
        mc.intField('startFrameIF', edit=True, enable=False)
        mc.intField('endFrameIF', edit=True, enable=False)
        mc.button('timelineBTN', edit=True, enable=False)
        mc.button('renderBTN', edit=True, enable=False)

        mc.text('framesTX', edit=True, enable=True)
        mc.textField('framesTF', edit=True, enable=True, text= "")

# switch server list - group toggle
def switchServer():
    checkServerList = mc.textField('serverListTF', query=True, text=True)
    checkServerGroup = mc.textField('serverGroupTF', query=True, text=True)

    if (len(checkServerList) > 0 and len(checkServerGroup) == 0):
        mc.text('serverListTX', edit=True, enable=True)
        mc.textField('serverListTF', edit=True, enable=True)
        mc.text('serverGroupTX', edit=True, enable=False)
        mc.textField('serverGroupTF', edit=True, enable=False, text='')
    elif (len(checkServerList) == 0 and len(checkServerGroup) > 0):
        mc.text('serverListTX', edit=True, enable=False)
        mc.textField('serverListTF', edit=True, enable=False, text='')
        mc.text('serverGroupTX', edit=True, enable=True)
        mc.textField('serverGroupTF', edit=True, enable=True)
    else:
        mc.text('serverListTX', edit=True, enable=True)
        mc.textField('serverListTF', edit=True, enable=True, text='')
        mc.text('serverGroupTX', edit=True, enable=True)
        mc.textField('serverGroupTF', edit=True, enable=True, text='')

# timeline Range button
def timelineRange():
    minTimelineFrame = mc.playbackOptions(query=True, minTime=True)
    maxTimelineFrame = mc.playbackOptions(query=True, maxTime=True)
    mc.intField('startFrameIF', edit=True, enable=True, value=minTimelineFrame)
    mc.intField('endFrameIF', edit=True, enable=True, value=maxTimelineFrame)

# Render Range button
def renderRange():
    minRenderFrame = mc.getAttr('defaultRenderGlobals.startFrame')
    maxRenderFrame = mc.getAttr('defaultRenderGlobals.endFrame')
    mc.intField('startFrameIF', edit=True, enable=True, value=minRenderFrame)
    mc.intField('endFrameIF', edit=True, enable=True, value=maxRenderFrame)

# Render Path dialog window
def renderPathDialog():
    dirName = mc.workspace( q=True, rootDirectory=True )
    openFileNameR = mc.fileDialog2(caption="Render Path", fileMode=1, startingDirectory=dirName, fileFilter='*.*')
    mc.textField('renderPathTF', edit=True, text=openFileNameR[0])

# Backburner Path dialog window
def backburnerPathDialog():
    dirName = mc.workspace( q=True, rootDirectory=True )
    openFileNameB = mc.fileDialog2(caption="Render Path", fileMode=1, startingDirectory=dirName, fileFilter='*.*')
    mc.textField('bburnerPathTF', edit=True, text=openFileNameB[0])

# Task List Name
def taskListName():
    taskList = mc.textField('jobNameTF', query=True, text=True)
    tempDir = tempfile.gettempdir()
    tempDir = tempDir.replace("\\", '/')
    tempDir += '/' + taskList + '.txt'
    return tempDir

# Create Task List
def createTaskList():
    filename = taskListName()
    taskListFile = open(filename, 'w')
    if (taskListFile == 0):
        mc.error('You dont have privilages')

    startFrame = mc.intField('startFrameIF', query=True, value=True)
    endFrame = mc.intField('endFrameIF', query=True, value=True)
    taskSize = mc.intField('taskSizeIF', query=True, value=True)

    if (taskSize == 0):
        mc.error('Task size should be greater than 0.')

    numberTasks = (float(endFrame) - float(startFrame)) / float(taskSize)
    if (numberTasks > int(numberTasks)):
        numberTasks = int(numberTasks) + 1

    startTaskFrame = startFrame
    lastTaskFrame = startFrame + taskSize - 1
    for task in range(int(numberTasks) + 1):
        if (lastTaskFrame >= endFrame):
            taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(endFrame) + "\t" + str(startTaskFrame) + "\t" + str(endFrame) + "\n")
            break
        taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(lastTaskFrame) + "\t" + str(startTaskFrame) + "\t" + str(lastTaskFrame) + "\n")
        startTaskFrame += taskSize
        lastTaskFrame += taskSize
    taskListFile.close()
    return filename

# Create Frames Task List
def createFramesTaskList():
    filename = taskListName()
    taskListFile = open(filename, 'w')
    if (taskListFile == 0):
        mc.error('You dont have privilages')

    frames = mc.textField('framesTF', query=True, text=True)
    taskSize = mc.intField('taskSizeIF', query=True, value=True)
    listB = frames.split(',')
    listA = []

    for each in listB:
        listA.append(each.replace(' ', ''))


    taskStartFrame = []
    taskEndFrame = []

    if (frames == ''):
        mc.error('Please complete Frames field.')

    if (taskSize == 0):
        mc.error('Task size should be greater than 0.')

    for task in range(len(listA)):
        if (listA[task].isdigit()):
            taskStartFrame.append(int(listA[task]))
            taskEndFrame.append(int(listA[task]))
        else:
            taskSeq = listA[task]
            taskSeq = taskSeq.split('-')
            if (len(taskSeq) == 0):
                result = re.sub("\d", "", taskSeq)
                mc.error('"' + result + '" is not an Integer.')
            else:
                seqFrames = []
                for seq in range(len(taskSeq)):
                    if (taskSeq[seq].isdigit()):
                        seqFrames.append(taskSeq[seq])
                    else:
                        result = re.sub("\d", "", taskSeq[seq])
                        mc.error('"' + result + '" is not an Integer.')
                if (int(seqFrames[1]) < int(seqFrames[0])):
                    mc.error('First frame is greater than second frame in sequence. ("' + seqFrames[0] + '" - "' + seqFrames[1] + '") ')
                taskStartFrame.append(int(seqFrames[0]))
                taskEndFrame.append(int(seqFrames[1]))

    for taskFrame in range(len(taskStartFrame)):
        if (taskStartFrame[taskFrame] == taskEndFrame[taskFrame]):
            taskListFile.write("frameRange " + str(taskStartFrame[taskFrame]) + "-" + str(taskEndFrame[taskFrame]) + "\t" + str(taskStartFrame[taskFrame]) + "\t" + str(taskEndFrame[taskFrame]) + "\n")
        else:
            numberTasks = (float(taskEndFrame[taskFrame]) - float(taskStartFrame[taskFrame])) / float(taskSize)
            if (numberTasks > int(numberTasks)):
                numberTasks = int(numberTasks) + 1
            startTaskFrame = taskStartFrame[taskFrame]
            lastTaskFrame = taskStartFrame[taskFrame] + taskSize - 1
            for task in range(int(numberTasks) + 1):
                if (lastTaskFrame >= taskEndFrame[taskFrame]):
                    taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(taskEndFrame[taskFrame]) + "\t" + str(startTaskFrame) + "\t" + str(taskEndFrame[taskFrame]) + "\n")
                    break
                taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(lastTaskFrame) + "\t" + str(startTaskFrame) + "\t" + str(lastTaskFrame) + "\n")
                startTaskFrame += taskSize
                lastTaskFrame += taskSize

    taskListFile.close()
    return filename

# Send Job
def sendJob(sendLayer=None):

    if (mc.radioButtonGrp('rangeRB', query=True, select=True) == 1):
        if (mc.checkBox('skipExistingFilesCB', query=True, value=True )):
            taskList = createSkipFramesTaskList(frameList=checkExistingFrames(checkLayer=sendLayer), layer=sendLayer)
        else:
            taskList = createTaskList()
    else:
        if (mc.checkBox('skipExistingFilesCB', query=True, value=True )):
            taskList = createSkipFramesTaskList(frameList=framesCheckExistingFrames(checkLayer=sendLayer), layer=sendLayer)
        else:
            taskList = createFramesTaskList()

    bburnerPathBB = errorMessageTF(property='bburnerPathTF', errorName='Backburner Path')
    jobNameBB = errorMessageTF(property='jobNameTF', errorName='Job Name')
    descriptionBB = mc.textField('descriptionTF', query=True, text=True )
    managerBB = errorMessageTF(property='managerNameTF', errorName='Manager Name')
    priorityBB = errorMessageIF(property='priorityIF', errorName='Priority')
    timeoutBB = errorMessageIF(property='timeoutIF', errorName='Timeout')
    renderPathBB = errorMessageTF(property='renderPathTF', errorName='Render Path')

    suspended = ''
    if (mc.checkBox('manualStartCB', query=True, value=True )):
        suspended = '-suspended '

    priority = priorityBB
    if (mc.checkBox('criticalCB', query=True, value=True )):
        priority = '0'

    rendererBB = ''
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 1 ):
        rendererBB = mc.getAttr("defaultRenderGlobals.currentRenderer")
        if (rendererBB == 'mayaHardware' ):rendererBB = 'hw'
        if (rendererBB == 'mayaSoftware' ):rendererBB = 'sw'
        if (rendererBB == 'mentalRay' ):rendererBB = 'mr'
        if (rendererBB == 'mayaVector' ):rendererBB = 'vr'

    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 2 ):rendererBB = 'mr'
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 3 ):rendererBB = 'sw'
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 4 ):rendererBB = 'hw'
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 5 ):rendererBB = 'vr'

    projectBB = mc.workspace( q=True, rootDirectory=True )

    verbosityBB = ''
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 2 ):
        verbosityBB = '-v ' + str(mc.optionMenu('verbosityOM', query=True, select=True) - 1)

    framePaddingBB = mc.intField('framePaddingIF', query=True, value=True )

    fileNameBB = mc.file(query=True, sceneName=True)
    if(fileNameBB == ''):
        mc.error('Save current file.')

    additionalOptionsBB = mc.textField('additionalOptionsTF', query=True, text=True )

    portBB = mc.intField('portIF', query=True, value=True )
    if (portBB == 0):
        portFlagBB = ''
    else:
        portFlagBB = ' -port ' + str(portBB)

    serverListBB = mc.textField('serverListTF', query=True, text=True )
    if (len(serverListBB)):
        serverListBB = ' -servers "' + serverListBB + '"'

    serverGroupBB = mc.textField('serverGroupTF', query=True, text=True )
    if (len(serverGroupBB)):
        serverGroupBB = ' -group "' + serverGroupBB + '"'

    serverCountBB = mc.intField('serverCountIF', query=True, value=True )
    if (serverCountBB == 0):
        serverCountFlagBB = ''
    else:
        serverCountFlagBB = ' -serverCount ' + serverCountBB

    renderFolderPath = mc.textField("renderFolder", query=True, text=True)

    renderLayerBB = ''
    layerJobName = sendLayer
    if (sendLayer != ''):
        renderLayerBB = (' -rl ' + sendLayer)
        layerJobName = ('_' + sendLayer)

    sendBB = ('"\\"\\"' + bburnerPathBB + '\\" -jobName \\"' + jobNameBB + layerJobName + '\\" -description \\"' + descriptionBB + '\\" -manager ')
    sendBB += (managerBB + portFlagBB + serverListBB + serverGroupBB + serverCountFlagBB +' ' + suspended + '-priority ')
    sendBB += (str(priority) + ' -taskList \\"' + taskList + '\\" -taskName 1 -timeout ' + str(timeoutBB))
    sendBB += (' \\"' + renderPathBB + '\\" -r ' + rendererBB + ' -s %tp2 -e %tp3 -proj \\"' + projectBB + '\\" -rd \\"' + renderFolderPath +'\\" ' + verbosityBB)
    sendBB += (renderLayerBB + ' -pad ' + str(framePaddingBB) + ' ' + additionalOptionsBB + ' \\"' + fileNameBB +'\\""')
    print sendBB
    return sendBB


#Close button
def closeBtn():
    mc.deleteUI("BburnWin")

# Submit button
def submitBtn():
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 1 ):
        send= sendJob(sendLayer='')
        print ('Backburner 1.0 by Mariano Antico.')
        print ('system (' + send + ')')
        printSend = mm.eval('system (' + send + ')')
        print printSend

    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 2 ):
        allLay = mc.ls(type='renderLayer')
        for layer in allLay:
            try:
                print layer
                if layer[0:3] != "rs_":
                    mc.select(layer) #DELETE OLD RENDERLAYER FROM IMPORTED OBJECT
                    mc.delete()
            except:
                pass
        allLay = mc.ls(type='renderLayer')
        for layer in allLay:                       
            renderableLayer = False
            if layer[0:3] == "rs_" or layer[0:3] == "def": #HACK TO GET ONLY RENDERLAYER FROM COLLECTION & DEFAULT RENDERLAYER
                renderableLayer = mc.getAttr(layer + '.renderable')
            if (renderableLayer):
                send= sendJob(sendLayer=layer)
                print ('Backburner 1.2 by Mariano Antico.')
                print ('system (' + send + ')')
                printSend = mm.eval('system (' + send + ')')
                print printSend

    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 3 ):
        currentLay = mc.editRenderLayerGlobals(query=True, currentRenderLayer=True)
        send= sendJob(sendLayer=currentLay)
        print ('Backburner 1.2 by Mariano Antico.')
        print ('system (' + send + ')')
        printSend = mm.eval('system (' + send + ')')
        print printSend
    print 'Done!'

# Submit and Close
def submitCloseBtn():
    submitBtn()
    closeBtn()

# skip button disable task size
def skipBtn():
    if (mc.checkBox('skipExistingFilesCB', query=True, value=True )):
        mc.intField('taskSizeIF', edit=True, value=1, enable=False)
        mc.text('taskSizeTX', edit=True, enable=False)
    else:
        mc.intField('taskSizeIF', edit=True, enable=True)
        mc.text('taskSizeTX', edit=True, enable=True)

# Layer Task List Name
def taskListLayerName(Tasklayer=''):
    taskList = mc.textField('jobNameTF', query=True, text=True)
    tempDir = tempfile.gettempdir()
    tempDir = tempDir.replace("\\", '/')
    tempDir += '/' + taskList + '_' + Tasklayer + '.txt'
    return tempDir

# replace name from File Name Prefix
def replaceNamePrefix(fileName=None, replaceLayer=''):

    passes = listPasses(layerPass=replaceLayer)
    if passes:
        if not re.search('<RenderPass>', fileName):
            fileName = 'MasterBeauty/' + fileName

    cams = listRenderCameras(layerCam=replaceLayer)
    if len(cams) > 1:
        if not re.search('<Camera>', fileName):
            fileName = '<Camera>/' + fileName

    if not re.search('<RenderLayer>', fileName):
        fileName = replaceLayer + '/' + fileName

    directoryReplace = fileName.split('/')
    renderCams = []

    index = -1
    for directory in directoryReplace:
        index += 1
        if re.search('<Scene>', directory):
            sceneName = mc.file(query=True, shortName=True, sceneName=True)
            sceneName = sceneName.split(".")
            sceneNamePeriod = ''
            if len(sceneName) >= 1:
                for index in range(len(sceneName) - 1):
                    sceneNamePeriod += sceneName[index] + '.'
                sceneName = sceneNamePeriod
                sceneName = sceneName[:(len(sceneName)-1)]
            else :
                sceneName = sceneName.split(".")[0]
            if (sceneName == ''):
                sceneName = 'untitled'
            directoryReplace[index] = directoryReplace[index].replace('<Scene>',sceneName)
        if re.search('<RenderLayer>', directory):
            currentLay = replaceLayer
            if currentLay == 'defaultRenderLayer':
                currentLay = 'masterLayer'
            directoryReplace[index] = directoryReplace[index].replace('<RenderLayer>',currentLay)
        if re.search('<Camera>', directory):
            camRender = replaceCameras(layerCam=replaceLayer)
            if camRender:
                directoryReplace[index] = directoryReplace[index].replace('<Camera>',camRender)
            else :
                cameras = mc.ls(cameras=True)
                for cam in cameras:
                    renderableCam = mc.getAttr(cam + '.renderable')
                    if renderableCam:
                        mc.select(cam, replace=True)
                        camTransform = str(mc.pickWalk( direction='up' )[0])
                        renderCams.append(camTransform)
                directoryReplace[index] = directoryReplace[index].replace('<Camera>',renderCams[0])
        if re.search('<RenderPassFileGroup>', directory):
            directoryReplace[index] = directoryReplace[index].replace('<RenderPassFileGroup>','Beauties')
        if re.search('<RenderPass>', directory):
            directoryReplace[index] = directoryReplace[index].replace('<RenderPass>','MasterBeauty')
        if re.search('<RenderPassType>', directory):
            directoryReplace[index] = directoryReplace[index].replace('<RenderPassType>','BEAUTY')
        if re.search('<Extension>', directory):
            outFormat = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.outFormatControl')
            if outFormat == 2:
                outFormatExt = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.outFormatExt')
                directoryReplace[index] = directoryReplace[index].replace('<Extension>',outFormatExt)
            elif outFormat == 0:
                extension = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.imfPluginKey')
                directoryReplace[index] = directoryReplace[index].replace('<Extension>',extension)
            else :
                directoryReplace[index] = directoryReplace[index].replace('<Extension>','')
        if re.search('<Version>', directory):
            version = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.renderVersion')
            directoryReplace[index] = directoryReplace[index].replace('<Version>',version)

    imageDir = ''
    for dir in range(len(directoryReplace)):
        if dir == (len(directoryReplace) - 1):
            imageDir += directoryReplace[dir]
            break
        imageDir += directoryReplace[dir] + '/'

    return imageDir

def replaceCameras(layerCam=''):
    valueExtOverride = ''
    renderCam = ''
    overrides = mc.listConnections(layerCam + '.adjs', destination=False, source=True, plugs=True)
    if overrides:
        for index in range(len(overrides)):
            if re.search('.renderable', overrides[index]):
                valueExtOverride = mc.getAttr(layerCam + '.adjs[' + str(index) + '].value')
                if valueExtOverride:
                    mc.select(overrides[index].split('.')[0], replace=True)
                    camTransform = str(mc.pickWalk( direction='up' )[0])
                    renderCam = camTransform
                    return renderCam
                    break
    return renderCam

def listRenderCameras(layerCam=''):
    mc.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
    valueExtOverride = ''
    renderCam = []
    overrides = mc.listConnections(layerCam + '.adjs', destination=False, source=True, plugs=True)
    if overrides:
        for index in range(len(overrides)):
            if re.search('.renderable', overrides[index]):
                valueExtOverride = mc.getAttr(layerCam + '.adjs[' + str(index) + '].value')
                if valueExtOverride:
                    mc.select(overrides[index].split('.')[0], replace=True)
                    camTransform = str(mc.pickWalk( direction='up' )[0])
                    renderCam.append(camTransform)
    return renderCam

def overrideCheckParameter(layerPrefix='', propPrefix=''):
    mc.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
    valueExtOverride = ''
    overrides = mc.listConnections(layerPrefix + '.adjs', destination=False, source=True, plugs=True)
    switch = 0
    if overrides:
        for index in range(len(overrides)):
            valueExtOverride = mc.getAttr(layerPrefix + '.adjs[' + str(index) + '].value')
            if re.search(propPrefix, overrides[index]):
                valueExtOverride = mc.getAttr(layerPrefix + '.adjs[' + str(index) + '].value')
                switch = 1
                #mc.editRenderLayerGlobals(currentRenderLayer=layerPrefix)
                break
    if not switch:
        valueExtOverride = mc.getAttr(propPrefix)
        #mc.editRenderLayerGlobals(currentRenderLayer=layerPrefix)
    return valueExtOverride

def listPasses(layerPass=''):
    passes = mc.ls(type='renderPass')
    hasPass = 0
    if passes:
        associatePass = mc.listConnections(layerPass + ".renderPass")
        if associatePass:
            hasPass = 1
    return hasPass

# Cheack Existing Frames
def checkExistingFrames(checkLayer=''):

    projectBB = mc.workspace( q=True, rootDirectory=True )

    imagesWorkSpace = mc.workspace( q=True, fileRule=True )
    imagesDir = ''
    count = 0
    for directory in imagesWorkSpace:
        count += 1
        if re.search('images', directory):
            imagesDir = imagesWorkSpace[count] + '/'
            break

    output = replaceNamePrefix(fileName = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imageFilePrefix'), replaceLayer=checkLayer)
    outputFile = output.split('/')[-1]

    outputDirSplit = output.split('/')
    outputDir = ''
    for dir in range(len(outputDirSplit) - 1):
        outputDir += outputDirSplit[dir] + '/'

    currentLay = checkLayer
    extension = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imfPluginKey')
    stratFrame = mc.intField('startFrameIF', query=True, value=True)
    endFrame = mc.intField('endFrameIF', query=True, value=True)

    outFormat = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatControl')
    animation = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.animation')
    putFrameBefore = mc.getAttr('defaultRenderGlobals.putFrameBeforeExt')
    periodInExt = mc.getAttr('defaultRenderGlobals.periodInExt')
    padding = mc.intField('framePaddingIF', query=True, value=True)
    outFormatExt = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatExt')
    frameList = []

    if (outFormat == 1 and animation == 0):
        # file format ('name (single)')
        outputFiles = outputFile
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 0):
        # file format ('name.ext (single)')
        outputFiles = outputFile + '.' + extension
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.ext')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.ext.%')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + extension + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 1 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.ext')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.ext')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))

    if (outFormat == 2 and animation == 0):
        # file format ('name.outFormatExt (single)')
        outputFiles = outputFile + '.' + outFormatExt
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.outFormatExt')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.outFormatExt.%')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + outFormatExt + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.outFormatExt')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.outFormatExt')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))

    return frameList

# Create Seq Task List and skip existing frames
def createSkipFramesTaskList(frameList=[], layer=''):
    if not frameList:
        mc.error(layer + ': All frames you wanto to render. Already exists. Disable Skip Existing Frames if you wanto to overwrite.')
    if frameList[0] == 'single':
        mc.error('You are trying to render a sequence, but you have set to render a Single Frame not an Animation.')
    filename = taskListLayerName(Tasklayer=layer)
    taskListFile = open(filename, 'w')
    if (taskListFile == 0):
        mc.error('You dont have privilages')

    startFrame = frameList[0]
    endFrame = frameList[-1]
    taskSize = 1

    taskFrame = startFrame
    for task in range(len(frameList)):
        taskFrame = frameList[task]
        taskListFile.write("frameRange " + str(taskFrame) + "-" + str(taskFrame) + "\t" + str(taskFrame) + "\t" + str(taskFrame) + "\n")
    taskListFile.close()
    return filename

# Create Frames List Skip Existing Files
def createListFramesSkipTaskList():
    frames = mc.textField('framesTF', query=True, text=True)
    taskSize = 1
    listB = frames.split(',')
    listA = []
    frameList = []

    for each in listB:
        listA.append(each.replace(' ', ''))

    taskStartFrame = []
    taskEndFrame = []

    if (frames == ''):
        mc.error('Please complete Frames field.')

    if (taskSize == 0):
        mc.error('Task size should be greater than 0.')

    for task in range(len(listA)):
        if (listA[task].isdigit()):
            taskStartFrame.append(int(listA[task]))
            taskEndFrame.append(int(listA[task]))
        else:
            taskSeq = listA[task]
            taskSeq = taskSeq.split('-')
            if (len(taskSeq) == 0):
                result = re.sub("\d", "", taskSeq)
                mc.error('"' + result + '" is not an Integer.')
            else:
                seqFrames = []
                for seq in range(len(taskSeq)):
                    if (taskSeq[seq].isdigit()):
                        seqFrames.append(taskSeq[seq])
                    else:
                        result = re.sub("\d", "", taskSeq[seq])
                        mc.error('"' + result + '" is not an Integer.')
                if (int(seqFrames[1]) < int(seqFrames[0])):
                    mc.error('First frame is greater than second frame in sequence. ("' + seqFrames[0] + '" - "' + seqFrames[1] + '") ')
                taskStartFrame.append(int(seqFrames[0]))
                taskEndFrame.append(int(seqFrames[1]))

    for taskFrame in range(len(taskStartFrame)):
        if (taskStartFrame[taskFrame] == taskEndFrame[taskFrame]):
            frameList.append(taskStartFrame[taskFrame])
        else:
            numberTasks = (float(taskEndFrame[taskFrame]) - float(taskStartFrame[taskFrame])) / float(taskSize)
            if (numberTasks > int(numberTasks)):
                numberTasks = int(numberTasks) + 1
            startTaskFrame = taskStartFrame[taskFrame]
            lastTaskFrame = taskStartFrame[taskFrame] + taskSize - 1
            for task in range(int(numberTasks) + 1):
                if (lastTaskFrame >= taskEndFrame[taskFrame]):
                    frameList.append(startTaskFrame)
                    break
                frameList.append(startTaskFrame)
                startTaskFrame += taskSize
                lastTaskFrame += taskSize

    return frameList

# Cheack Existing Frames for frame render mode
def framesCheckExistingFrames(checkLayer=''):
    projectBB = mc.workspace( q=True, rootDirectory=True )

    imagesWorkSpace = mc.workspace( q=True, fileRule=True )
    imagesDir = ''
    count = 0
    for directory in imagesWorkSpace:
        count += 1
        if re.search('images', directory):
            imagesDir = imagesWorkSpace[count] + '/'
            break

    output = replaceNamePrefix(fileName = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imageFilePrefix'), replaceLayer=checkLayer)
    outputFile = output.split('/')[-1]

    outputDirSplit = output.split('/')
    outputDir = ''
    for dir in range(len(outputDirSplit) - 1):
        outputDir += outputDirSplit[dir] + '/'

    currentLay = checkLayer
    extension = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imfPluginKey')
    frames = createListFramesSkipTaskList()

    outFormat = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatControl')
    animation = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.animation')
    putFrameBefore = mc.getAttr('defaultRenderGlobals.putFrameBeforeExt')
    periodInExt = mc.getAttr('defaultRenderGlobals.periodInExt')
    padding = mc.intField('framePaddingIF', query=True, value=True)
    outFormatExt = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatExt')
    frameList = []

    if (outFormat == 1 and animation == 0):
        # file format ('name (single)')
        outputFiles = outputFile
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 0):
        # file format ('name.ext (single)')
        outputFiles = outputFile + '.' + extension
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.ext.%')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + extension + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 1 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))

    if (outFormat == 2 and animation == 0):
        # file format ('name.ext (single)')
        outputFiles = outputFile + '.' + outFormatExt
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.ext.%')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + outFormatExt + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))

    return frameList

#switch Render Mode - Skip Existing Frames
def switchRenderMode():
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 1 ):
        mc.checkBox('skipExistingFilesCB', edit=True, value=False, enable=False)
        mc.intField('taskSizeIF', edit=True, enable=True)
        mc.text('taskSizeTX', edit=True, enable=True)
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 2 ):
        mc.checkBox('skipExistingFilesCB', edit=True, enable=True)
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 3 ):
        mc.checkBox('skipExistingFilesCB', edit=True, enable=True)
backBurner()
setRenderFolder()
##===========================================================================##
##===========================================================================##
## To BackBurner. 1.2                                                        ##
## By Mariano Antico                                                         ##
## Barraca Post                                                              ##
## www.barraca.com.ar                                                        ##
## www.marianoantico.blogspot.com                                            ##
## Last Updated: January 20, 2012.                                           ##
## All Rights Reserved .                                                     ##
##                                                                           ##
## Description:                                                              ##
## Send to Backburner                                                        ##
##                                                                           ##
## Tutorials:                                                                ##
## www.marianoantico.blogspot.com                                            ##
## http://vimeo.com/34227651                                                 ##
##                                                                           ##
## Run:                                                                      ##
## backBurner()                                                              ##
##                                                                           ##
##===========================================================================##
##===========================================================================##

#import libraries

import maya.cmds as mc
import os
import webbrowser
import maya.mel as mm
import tempfile
import re

##---------------------------------------------------------------------------##
#Interface save window
def setRenderFolder():

    scenePath = mc.file(q=True, sceneName=True)
    sceneDir = os.path.abspath(os.path.join(scenePath, os.pardir))
    parentDir = os.path.abspath(os.path.join(sceneDir, os.pardir))
    renderOutDir = os.path.join(parentDir,"render_out")
    if not os.path.exists(renderOutDir):
        os.makedirs(renderOutDir)

    chosenFolder = mc.fileDialog2(dialogStyle=2, fileMode=2, dir=renderOutDir)
    mc.textField('renderFolder', edit=1, text=chosenFolder[0])

def backBurner():

    if mc.window("BburnWin", query=True, exists= True):
        mc.deleteUI("BburnWin")

    saveWindow = mc.confirmDialog( title='Save Scene', message='Before creating a Backburner job would you like to save current scene file?', button=['Yes', 'Ignore', 'No'], defaultButton='Yes', cancelButton='No', dismissString='Ignore' )
    if (saveWindow == 'Yes'):
        saveName = mc.file(query=True, sceneName=True)
        if(saveName == ''):
            mc.file( rename='untitled.mb' )
            mc.file( save=True)
        mc.file( save=True)
        bburnerWindow()
    elif (saveWindow == 'Ignore'):
        bburnerWindow()
    elif (saveWindow == 'No'):
        print ('Cancelled by user')

##---------------------------------------------------------------------------##
#Interface backburner

def bburnerWindow():

    #Interface

    if mc.window("BburnWin", query=True, exists= True):
        mc.deleteUI("BburnWin")

    #create window
    pikoWindow = mc.window( 'BburnWin', title="Send to BackBurner 1.2                           by Mariano Antico", sizeable = False)

    ##---------------------------------------------------------------------------##
    #menu bar
    menuBB = mc.menuBarLayout()
    m1 = mc.menu(label="File", enable=True)
    m1Item = mc.menuItem( label="Reset values", enable=True, command= 'defaultValuesBb()')
    m2 = mc.menu(label="Window", enable=True)
    m2Item1 = mc.menuItem( label="Render View", enable=True, command = "renderViewWindow()")
    m2Item2 = mc.menuItem( label="Render Settings", enable=True, command = "renderSettingsWindow()")
    m3 = mc.menu(label="Help", enable=True)
    m3Item = mc.menuItem( label="About", enable=True, command = "myBlog()")

    ##---------------------------------------------------------------------------##
    #frame job settings
    frameJob = mc.frameLayout( label='JOB SETTINGS:', borderStyle='out', collapsable=True, marginHeight=2)

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 10)])

    #Job Name
    mc.text(font="plainLabelFont",label="Job Name", align='right')
    jobName = mc.textField('jobNameTF',font="plainLabelFont", text= jobNameDef())
    mc.separator(style='none')

    #Description
    mc.text(font="plainLabelFont",label="Description", align='right')
    description = mc.textField('descriptionTF', font="plainLabelFont", text= "")
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 20)])
    #Render Out
    mc.text(font="plainLabelFont",label="Render folder", align='right')
    renderFolder = mc.textField('renderFolder', font="plainLabelFont", text= "")
    mc.button (label="...", command='setRenderFolder()')
    mc.separator(style='none')


    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 2, columnWidth=[(1, 90), (2, 200)], columnSpacing = (2, 5))

    #Range
    mc.text(font="plainLabelFont",label="Range", align='right')
    mc.radioButtonGrp('rangeRB', numberOfRadioButtons=2, labelArray2=['Frame Range', 'Frames'], select=1, changeCommand='switchFrames()')

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 4, columnWidth=[(1, 90), (2, 90), (3, 110)], columnSpacing = (3, 5))

    #Start Frame
    mc.text('startFrameTX', font="plainLabelFont",label="Start Frame", align='right')
    startFrame = mc.intField('startFrameIF', value=0)

    # timeline Range Btn
    timelineBtn = mc.button('timelineBTN', label = 'Timeline Range', command='timelineRange()')
    mc.separator(style='none')

    #End Frame
    mc.text('endFrameTX', font="plainLabelFont",label="End Frame", align='right')
    endFrame = mc.intField('endFrameIF', value=100)

    # Render Range Btn
    renderBtn = mc.button('renderBTN', label = 'Render Range', command='renderRange()')
    mc.separator(style='none')

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 205)])

    # Frames
    mc.text('framesTX', font="plainLabelFont", enable=False, label="Frames", align='right')
    frames = mc.textField('framesTF', enable=False, font="plainLabelFont", text= "")
    mc.text('exampleTX', font="plainLabelFont", enable=False, label=" (e.g. 1,3,5-12)", align='left')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 90), (3, 200)], columnSpacing = (3, 5))

    #Priority
    mc.text(font="plainLabelFont",label="Priority", align='right')
    priority = mc.intField('priorityIF', value=50)

    #Critical
    mc.checkBox('criticalCB', label='Critical', value=False )

    #Task Size
    mc.text('taskSizeTX', font="plainLabelFont",label="Task Size", align='right')
    taskSize = mc.intField('taskSizeIF', value=1)

    #Skip Existing Files
    mc.checkBox('skipExistingFilesCB', label='Skip Existing Files', value=False, changeCommand='skipBtn()')

    #Frame Padding
    mc.text(font="plainLabelFont",label="Frame Padding", align='right')
    framePadding = mc.intField('framePaddingIF', value=4)
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 4, columnWidth=[(1, 90), (2, 90), (3, 85)])

    #Renderer
    mc.text(font="plainLabelFont",label="Renderer", align='right')
    mc.optionMenu('rendererOM' )
    mc.menuItem( label='Scene Renderer' )
    mc.menuItem( label='Mental Ray      ' )
    mc.menuItem( label='Maya Software   ' )
    mc.menuItem( label='Maya Hardware      ' )
    mc.menuItem( label='Vector      ' )

    #Verbosity
    mc.text(font="plainLabelFont",label=" Verbosity ", align='right')
    mc.optionMenu('verbosityOM')
    mc.menuItem( label='0 - No Messages')
    mc.menuItem( label='1 - Fatal' )
    mc.menuItem( label='2 - Error' )
    mc.menuItem( label='3 - Warning' )
    mc.menuItem( label='4 - Info' )
    mc.menuItem( label='5 - Progress' )
    mc.menuItem( label='6 - Detailed' )
    mc.optionMenu('verbosityOM', edit=True, select=6)

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 10)])

    #Additional Options
    mc.text(font="plainLabelFont",label="Additional Options", align='right')
    mc.textField('additionalOptionsTF', font="plainLabelFont", text= "")
    mc.separator(style='none')

    mc.setParent('..')
    mc.rowColumnLayout( numberOfColumns = 2, columnWidth=[(1, 90), (2, 280)], columnSpacing = (2, 5))

    #Render Mode
    mc.text(font="plainLabelFont",label="Render Mode", align='right')
    mc.radioButtonGrp('renderModeRB', numberOfRadioButtons=3, labelArray3=['Renderable Layers', 'Each Render Layers', 'Current'], select=2, changeCommand = 'switchRenderMode()')

    mc.setParent('..')
    mc.setParent('..')

    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##

    #frame backburner settings
    frameBburn = mc.frameLayout( label='BACKBURNER SETTINGS:', borderStyle='out', collapsable=True, marginHeight=2)
    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 280), (3, 10)])

    #Manager Name
    mc.text(font="plainLabelFont",label="Manager Name", align='right')
    managerName = mc.textField('managerNameTF', font="plainLabelFont", text= "192.168.0.39")
    mc.separator(style='none')

    #Server List
    mc.text('serverListTX', font="plainLabelFont",label="Server List", align='right')
    serverList = mc.textField('serverListTF', font="plainLabelFont", text= "", changeCommand='switchServer()')
    mc.separator(style='none')

    #Server Group
    mc.text('serverGroupTX', font="plainLabelFont",label="Server Group", align='right')
    serverGroup = mc.textField('serverGroupTF', font="plainLabelFont", text= "", changeCommand='switchServer()')
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 60)])

    #Server Count
    mc.text(font="plainLabelFont",label="Server Count", align='right')
    serverCount = mc.intField('serverCountIF', value=0)
    mc.separator(style='none')

    #Server Port
    mc.text(font="plainLabelFont",label="Port", align='right')
    portBb = mc.intField('portIF', value=3234)
    mc.separator(style='none')

    # timeout
    mc.text(font="plainLabelFont",label="Timeout", align='right')
    timeoutTF = mc.intField('timeoutIF', value=600)
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 60)],columnSpacing = (2, 5))

    #Manually Start
    mc.text(font="plainLabelFont",label="Manually Start Job", align='right')
    mc.checkBox('manualStartCB', label='' )
    mc.separator(style='none')

    mc.setParent('..')

    mc.rowColumnLayout( numberOfColumns = 3, columnWidth=[(1, 90), (2, 270), (3, 25)])

    # Render Path
    mc.text(font="plainLabelFont",label="Render Path", align='right')
    renderPath = mc.textField('renderPathTF', font="plainLabelFont", text= "C:/Program Files/Autodesk/Maya2019/bin/Render")
    renderPathBtn = mc.button( label = '...', command= 'renderPathDialog()')

    # Backburner Path
    mc.text(font="plainLabelFont",label="Backburner Path", align='right')
    bburnerPath = mc.textField('bburnerPathTF', font="plainLabelFont", text= "C:/Program Files (x86)/Autodesk/Backburner/cmdjob.exe")
    bburnerPathBtn = mc.button( label = '...', command= 'backburnerPathDialog()')

    mc.setParent('..')
    mc.setParent('..')

    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##
    ##---------------------------------------------------------------------------##

    #frame backburner settings
    frameHelp = mc.frameLayout( label='HELP:', borderStyle='out', collapsable=True, collapse=True, marginHeight=2)

    mc.rowColumnLayout( numberOfColumns = 1)

    mc.separator(style='none', height=2)
    mc.text(font="boldLabelFont",label="Command Line Help:", align='left')
    mc.separator(style='none', height=4)

    helpScrollField = mc.scrollField('helpST', font="plainLabelFont", wordWrap=True, editable=False, height=420)

    helpText = 'Usage: render [options] filename:\n'
    helpText += '       where "filename" is a Maya ASCII or a Maya binary file.\n\n'

    helpText += 'Common options:\n'
    helpText += '\n'
    helpText += '  -help                          Print help\n'
    helpText += '  -test                          Print Mel commands but do not execute them\n'
    helpText += '  -verb                         Print Mel commands before they are executed\n'
    helpText += '  -keepMel                   Keep the temporary Mel file\n'
    helpText += '  -listRenderers           List all available renderers\n'
    helpText += '  -renderer string        Use this specific renderer\n'
    helpText += '  -r string                    Same as -renderer\n'
    helpText += '  -proj string               Use this Maya project to load the file\n'
    helpText += '  -log string                 Save output into the given file\n'

    helpText += '\n'
    helpText += 'Specific options for renderer "default": Use the renderer stored in the Maya file\n'

    helpText += '\n'
    helpText += 'General purpose flags:\n'
    helpText += '\n'
    helpText += '  -rd path                    Directory in which to store image file\n'
    helpText += '  -of string                  Output image file format. See the Render Settings\n'
    helpText += '                                   window to find available formats\n'
    helpText += '  -im filename              Image file output name\n'

    helpText += '\n'
    helpText += 'Frame numbering options:\n'
    helpText += '\n'
    helpText += '  -s float                     Starting frame for an animation sequence\n'
    helpText += '  -e float                     End frame for an animation sequence\n'
    helpText += '  -b float                     By frame (or step) for an animation sequence\n'
    helpText += '  -pad int                    Number of digits in the output image frame file\n'
    helpText += '                                  name extension\n'
    helpText += '  -rfs int                      Renumber Frame Start: number for the first image\n'
    helpText += '                                  when renumbering frames\n'
    helpText += '  -rfb int                     Renumber Frame By (or step) used for renumbering\n'
    helpText += '                                  frames\n'
    helpText += '  -fnc int                     File Name Convention: any of name, name.ext, ... \n'
    helpText += '                                  See the Render Settings window to find available\n'
    helpText += '                                  options.Use namec and namec.ext for Multi Frame\n'
    helpText += '                                  Concatenated formats. As a shortcut, numbers 1,\n'
    helpText += '                                  2, ... can also be used\n'

    helpText += '\n'
    helpText += 'Camera options:\n'
    helpText += '\n'
    helpText += '  -cam name              Specify which camera to be rendered\n'
    helpText += '  -rgb boolean           Turn RGB output on or off\n'
    helpText += '  -alpha boolean        Turn Alpha output on or off\n'
    helpText += '  -depth boolean       Turn Depth output on or off\n'
    helpText += '  -iip                           Ignore Image Planes. Turn off all image planes\n'
    helpText += '                                  before rendering\n'

    helpText += '\n'
    helpText += 'Resolution options:\n'
    helpText += '\n'
    helpText += '  -x int                                 Set X resolution of the final image\n'
    helpText += '  -y int                                 Set Y resolution of the final image\n'
    helpText += '  -percentRes float             Renders the image using percent of the\n'
    helpText += '                                           resolution\n'
    helpText += '  -ard float                          Device aspect ratio for the rendered image\n'
    helpText += '  -par float                          Pixel aspect ratio for the rendered image\n'

    helpText += '\n'
    helpText += 'Render Layers and Passes:\n'
    helpText += '\n'
    helpText += '  -rl boolean|name(s)          Render each render layer separately\n'
    helpText += '  -rp boolean|name(s)        Render passes separately. \'all\' will render all\n'
    helpText += '                                           passes\n'
    helpText += '  -sel boolean|name(s)       Selects which objects, groups and/or sets to\n'
    helpText += '                                           render\n'
    helpText += '  -l boolean|name(s)           Selects which display and render layers to\n'
    helpText += '                                           render\n'

    helpText += '\n'
    helpText += 'Mel callbacks:\n'
    helpText += '\n'
    helpText += '  -preRender string             Mel code executed before rendering\n'
    helpText += '  -postRender string           Mel code executed after rendering\n'
    helpText += '  -preLayer string                Mel code executed before each render layer\n'
    helpText += '  -postLayer string              Mel code executed after each render layer\n'
    helpText += '  -preFrame string               Mel code executed before each frame\n'
    helpText += '  -postFrame string             Mel code executed after each frame\n'
    helpText += '  -pre string                         Obsolete flag\n'
    helpText += '  -post string                       Obsolete flag\n'

    helpText += '\n'
    helpText += 'Specific options for the layers who use Maya software renderer:\n'

    helpText += '\n'
    helpText += 'Anti-aliasing quality only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:eaa int                   The anti-aliasing quality of EAS (Abuffer). One\n'
    helpText += '                                       of: highest(0), high(1), medium(2), low(3)\n'
    helpText += '  -sw:ss int                     Global number of shading samples per surface in a\n'
    helpText += '                                       pixel\n'
    helpText += '  -sw:mss int                   Maximum number of adaptive shading samples\n'
    helpText += '                                       per surface in a pixel\n'
    helpText += '  -sw:mvs int                   Number of motion blur visibility samples\n'
    helpText += '  -sw:mvm int                  Maximum number of motion blur visibility samples\n'
    helpText += '  -sw:pss int                    Number of particle visibility samples\n'
    helpText += '  -sw:vs int                     Global number of volume shading samples\n'
    helpText += '  -sw:ufil boolean            If true, use the multi-pixel filtering; otherwise\n'
    helpText += '                                       use single pixel filtering\n'
    helpText += '  -sw:pft int                    When useFilter is true, identifies one of the\n'
    helpText += '                                       following filters: box(0), triangle(2), gaussian(4),\n'
    helpText += '                                       quadratic(5)\n'
    helpText += '  -sw:pfx float                 When useFilter is true, defines the X size of the\n'
    helpText += '                                       filter\n'
    helpText += '  -sw:pfy float                 When useFilter is true, defines the Y size of the\n'
    helpText += '                                       filter\n'
    helpText += '  -sw:rct float                  Red channel contrast threshold\n'
    helpText += '  -sw:gct float                 Green channel contrast threshold\n'
    helpText += '  -sw:bct float                  Blue channel contrast threshold\n'
    helpText += '  -sw:cct float                  Pixel coverage contrast threshold (default is\n'
    helpText += '                                       1.0/8.0)\n'

    helpText += '\n'
    helpText += 'Raytracing quality only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:ert boolean            Enable ray tracing\n'
    helpText += '  -sw:rfl int                      Maximum ray-tracing reflection level\n'
    helpText += '  -sw:rfr int                     Maximum ray-tracing refraction level\n'
    helpText += '  -sw:sl int                       Maximum ray-tracing shadow ray depth\n'

    helpText += '\n'
    helpText += 'Field Options only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:field boolean         Enable field rendering. When on, images are\n'
    helpText += '                                       interlaced\n'
    helpText += '  -sw:pal                         When field rendering is enabled, render even field\n'
    helpText += '                                       first (PAL)\n'
    helpText += '  -sw:ntsc                       When field rendering is enabled, render odd field\n'
    helpText += '                                       first (NTSC)\n'

    helpText += '\n'
    helpText += 'Motion Blur only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:mb boolean                 Motion blur on/off\n'
    helpText += '  -sw:mbf float                     Motion blur by frame\n'
    helpText += '  -sw:sa float                       Shutter angle for motion blur (1-360)\n'
    helpText += '  -sw:mb2d boolean             Motion blur 2D on/off\n'
    helpText += '  -sw:bll float                       2D motion blur blur length\n'
    helpText += '  -sw:bls float                      2D motion blur blur sharpness\n'
    helpText += '  -sw:smv int                       2D motion blur smooth value\n'
    helpText += '  -sw:smc boolean               2D motion blur smooth color on/off\n'
    helpText += '  -sw:kmv boolean               Keep motion vector for 2D motion blur on/off\n'

    helpText += '\n'
    helpText += 'Render Options only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:ifg boolean                Use the film gate for rendering if false\n'
    helpText += '  -sw:edm boolean             Enable depth map usage\n'
    helpText += '  -sw:g float                       Gamma value\n'
    helpText += '  -sw:premul boolean         Premultiply color by the alpha value\n'
    helpText += '  -sw:premulthr float          When premultiply is on, defines the threshold \n'
    helpText += '                                           used to determine whether to premultiply\n'
    helpText += '                                           or not\n'

    helpText += '\n'
    helpText += 'Memory and Performance only for Maya software renderer:\n'
    helpText += '\n'
    helpText += '  -sw:uf boolean                 Use the tessellation file cache\n'
    helpText += '  -sw:oi boolean                  Dynamically detects similarly tessellated\n'
    helpText += '                                           surfaces\n'
    helpText += '  -sw:rut boolean                Reuse render geometry to generate depth\n'
    helpText += '                                           maps\n'
    helpText += '  -sw:udb boolean              Use the displacement bounding box scale to\n'
    helpText += '                                           optimize\n'
    helpText += '                                           displacement-map performance\n'
    helpText += '  -sw:mm int                        Renderer maximum memory use\n'
    helpText += '                                           (in Megabytes)\n'

    helpText += '\n'
    helpText += 'Specific options for the layers who use Maya hardware renderer:\n'
    helpText += '\n'
    helpText += 'Quality flags only for Maya hardware renderer:\n'
    helpText += '\n'
    helpText += '  -hw:ehl boolean                Enable high quality lighting\n'
    helpText += '  -hw:ams boolean              Accelerated multi sampling\n'
    helpText += '  -hw:ns int                         Number of samples per pixel\n'
    helpText += '  -hw:tsc boolean               Transparent shadow maps\n'
    helpText += '  -hw:ctr int                        Color texture resolution\n'
    helpText += '  -hw:btr int                        Bump texture resolution\n'
    helpText += '  -hw:tc boolean                 Enable texture compression\n'

    helpText += '\n'
    helpText += 'Render options only for Maya hardware renderer:\n'
    helpText += '\n'
    helpText += '  -hw:c boolean                              Culling mode.\n'
    helpText += '                0: per object.\n'
    helpText += '                1: all double sided.\n'
    helpText += '                2: all single sided\n'
    helpText += '  -hw:sco boolean                           Enable small object culling\n'
    helpText += '  -hw:ct float                                   Small object culling threshold\n'

    helpText += '\n'
    helpText += 'Mel callbacks only for Maya hardware renderer:\n'
    helpText += '\n'
    helpText += '  -hw:mb boolean                 Enable motion blur\n'
    helpText += '  -hw:mbf float                     Motion blur by frame\n'
    helpText += '  -hw:ne int                          Number of exposures\n'
    helpText += '  -hw:egm boolean               Enable geometry mask\n'

    helpText += '\n'
    helpText += 'Specific options for the layers who use Mentalray renderer\n'
    helpText += '\n'
    helpText += 'Other only for Mentalray renderer:\n'
    helpText += '\n'
    helpText += '  -mr:v/mr:verbose int           Set the verbosity level.\n'
    helpText += '        0 - to turn off messages\n'
    helpText += '        1 - for fatal errors only\n'
    helpText += '        2 - for all errors\n'
    helpText += '        3 - for warnings\n'
    helpText += '        4 - for informational messages\n'
    helpText += '        5 - for progress messages\n'
    helpText += '        6 - for detailed debugging messages\n'
    helpText += '\n'
    helpText += '   -mr:rt/mr:renderThreads int            Specify the number of rendering.\n'
    helpText += '                                                            threads.\n'
    helpText += '   -mr:art/mr:autoRenderThreads       Automatically determine the number\n'
    helpText += '                                                            of rendering threads.\n'
    helpText += '   -mr:mem/mr:memory int                   Set the memory limit (in MB).\n'
    helpText += '   -mr:aml/mr:autoMemoryLimit           Compute the memory limit\n'
    helpText += '                                                            automatically.\n'
    helpText += '   -mr:ts/mr:taskSize int                       Set the pixel width/height of the\n'
    helpText += '                                                            render tiles.\n'
    helpText += '   -mr:at/mr:autoTiling                         Automatically determine optimal tile\n'
    helpText += '                                                            size.\n'
    helpText += '   -mr:fbm/mr:frameBufferMode int     Set the frame buffer mode.\n'
    helpText += '        0 in-memory framebuffers\n'
    helpText += '        1 memory mapped framebuffers\n'
    helpText += '        2 cached framebuffers\n'
    helpText += '  -mr:rnm boolean                Network rendering option. If true, mental ray\n'
    helpText += '                                            renders almost everything on slave machines,\n'
    helpText += '                                            thus reducing the workload on the\n'
    helpText += '        master machine\n'
    helpText += '  -mr:lic string                       Specify satellite licensing option. mu/unlimited\n'
    helpText += '                                            or mc/complete.\n'
    helpText += '  -mr:reg int int int int          Set sub-region pixel boundary of the final\n'
    helpText += '                                            image: left, right, bottom, top\n'

    helpText += '\n'
    helpText += '\n'
    helpText += ' *** Remember to place a space between option flags and their arguments. ***\n'
    helpText += 'Any boolean flag will take the following values as TRUE: on, yes, true, or 1.'
    helpText += 'Any boolean flag will take the following values as FALSE: off, no, false, or 0.\n'

    helpText += '                 e.g. -s 1 -e 10 -x 512 -y 512 -cam persp -mr:v 5 file.\n'
    helpText += '\n'
    helpText += '\n'

    helpText += 'Send to Backburner 1.2 by Mariano Antico   \n'
    helpText += 'www.marianoantico.blogspot.com'

    mc.scrollField('helpST', edit=True, text=helpText)

    mc.setParent('..')
    mc.setParent('..')

    ##---------------------------------------------------------------------------##
    #Submit buttons

    mc.rowColumnLayout( numberOfColumns = 3)

    submitCloseBtn = mc.button( label = 'Submit Job and Close', command='submitCloseBtn()')
    submitBtn = mc.button( label = 'Submit', command='submitBtn()')
    closeBtn = mc.button( label = 'Close', command='closeBtn()')

    mc.showWindow( pikoWindow )

##---------------------------------------------------------------------------##
##---------------------------------------------------------------------------##
##---------------------------------------------------------------------------##

#Child def
# my Blog
def myBlog():
    url = 'http://www.marianoantico.blogspot.com/'
    webbrowser.open_new(url)

# render view window
def renderViewWindow():
    mm.eval('RenderViewWindow;')

# render settings window
def renderSettingsWindow():
    mm.eval('unifiedRenderGlobalsWindow;')

# job Name window
def jobNameDef():
    fileName = mc.file(query=True, shortName=True, sceneName=True)
    fileName = fileName.split(".")[0]
    if (fileName == '_'):
        fileName = 'untitled'
    return(fileName)

# default window
def defaultValuesBb():
    mc.textField('jobNameTF', edit=True, text= jobNameDef())
    mc.textField('descriptionTF', edit=True, text= "")
    mc.textField('renderOut', edit=True, text= "B://test/")
    mc.radioButtonGrp('rangeRB', edit=True, select=1)
    switchFramesDefault()
    mc.intField('priorityIF', edit=True, value=50)
    mc.checkBox('criticalCB', edit=True, value=False )
    mc.text('taskSizeTX', edit=True, enable=True)
    mc.intField('taskSizeIF', edit=True, value=1, enable=True)
    mc.intField('framePaddingIF', edit=True, value=4)
    mc.optionMenu('rendererOM', edit=True, select=1)
    mc.optionMenu('verbosityOM', edit=True, select=6)
    mc.textField('additionalOptionsTF', edit=True, text= "")
    mc.radioButtonGrp('renderModeRB', edit=True, select= 2)
    mc.checkBox('skipExistingFilesCB', edit=True, value=False)
    switchRenderMode()

    mc.textField('managerNameTF', edit=True, text= "")
    mc.text('serverListTX', edit=True, enable=True)
    mc.textField('serverListTF', edit=True, text= "", enable=True)
    mc.text('serverGroupTX', edit=True, enable=True)
    mc.textField('serverGroupTF', edit=True, text= "", enable=True)
    mc.intField('serverCountIF', edit=True, value= 0)
    mc.intField('portIF', edit=True, value= 0)
    mc.intField('timeoutIF', edit=True, value= 600)
    mc.checkBox('manualStartCB', edit=True, value=False )
    mc.textField('renderPathTF', edit=True, text= "C:/Program Files/Autodesk/Maya2011/bin/Render")
    mc.textField('bburnerPathTF', edit=True, text= "C:/Program Files (x86)/Autodesk/Backburner/cmdjob.exe")

# error Message Text Field
def errorMessageTF(property=None, errorName=None):
    if (mc.textField(property, query=True, text=True ) == ''):
        mc.error('Please complete ' + errorName + ' field.')
        errorReturnTF = ''
    errorReturnTF = mc.textField(property, query=True, text=True )
    return errorReturnTF

# error Message Integer Field
def errorMessageIF(property=None, errorName=None):
    if (mc.intField(property, query=True, value=True ) == ''):
        mc.error('Please complete ' + errorName + ' field.')
        errorReturnIF = ''
    errorReturnIF = mc.intField(property, query=True, value=True )
    return errorReturnIF

# switchFrames Default window
def switchFramesDefault():
    rangeSelected = mc.radioButtonGrp('rangeRB', query=True, select=True)
    if (rangeSelected == 1):
        mc.text('startFrameTX', edit=True, enable=True)
        mc.text('endFrameTX', edit=True, enable=True)
        mc.intField('startFrameIF', edit=True, enable=True, value=0)
        mc.intField('endFrameIF', edit=True, enable=True, value=100)
        mc.button('timelineBTN', edit=True, enable=True)
        mc.button('renderBTN', edit=True, enable=True)

        mc.text('framesTX', edit=True, enable=False)
        mc.textField('framesTF', edit=True, enable=False, text= "")
    else:
        mc.text('startFrameTX', edit=True, enable=False)
        mc.text('endFrameTX', edit=True, enable=False)
        mc.intField('startFrameIF', edit=True, enable=False, value=0)
        mc.intField('endFrameIF', edit=True, enable=False, value=100)
        mc.button('timelineBTN', edit=True, enable=False)
        mc.button('renderBTN', edit=True, enable=False)

        mc.text('framesTX', edit=True, enable=True)
        mc.textField('framesTF', edit=True, enable=True, text= "")

# switchFrames window
def switchFrames():
    rangeSelected = mc.radioButtonGrp('rangeRB', query=True, select=True)
    if (rangeSelected == 1):
        mc.text('startFrameTX', edit=True, enable=True)
        mc.text('endFrameTX', edit=True, enable=True)
        mc.intField('startFrameIF', edit=True, enable=True)
        mc.intField('endFrameIF', edit=True, enable=True)
        mc.button('timelineBTN', edit=True, enable=True)
        mc.button('renderBTN', edit=True, enable=True)

        mc.text('framesTX', edit=True, enable=False)
        mc.textField('framesTF', edit=True, enable=False, text= "")
    else:
        mc.text('startFrameTX', edit=True, enable=False)
        mc.text('endFrameTX', edit=True, enable=False)
        mc.intField('startFrameIF', edit=True, enable=False)
        mc.intField('endFrameIF', edit=True, enable=False)
        mc.button('timelineBTN', edit=True, enable=False)
        mc.button('renderBTN', edit=True, enable=False)

        mc.text('framesTX', edit=True, enable=True)
        mc.textField('framesTF', edit=True, enable=True, text= "")

# switch server list - group toggle
def switchServer():
    checkServerList = mc.textField('serverListTF', query=True, text=True)
    checkServerGroup = mc.textField('serverGroupTF', query=True, text=True)

    if (len(checkServerList) > 0 and len(checkServerGroup) == 0):
        mc.text('serverListTX', edit=True, enable=True)
        mc.textField('serverListTF', edit=True, enable=True)
        mc.text('serverGroupTX', edit=True, enable=False)
        mc.textField('serverGroupTF', edit=True, enable=False, text='')
    elif (len(checkServerList) == 0 and len(checkServerGroup) > 0):
        mc.text('serverListTX', edit=True, enable=False)
        mc.textField('serverListTF', edit=True, enable=False, text='')
        mc.text('serverGroupTX', edit=True, enable=True)
        mc.textField('serverGroupTF', edit=True, enable=True)
    else:
        mc.text('serverListTX', edit=True, enable=True)
        mc.textField('serverListTF', edit=True, enable=True, text='')
        mc.text('serverGroupTX', edit=True, enable=True)
        mc.textField('serverGroupTF', edit=True, enable=True, text='')

# timeline Range button
def timelineRange():
    minTimelineFrame = mc.playbackOptions(query=True, minTime=True)
    maxTimelineFrame = mc.playbackOptions(query=True, maxTime=True)
    mc.intField('startFrameIF', edit=True, enable=True, value=minTimelineFrame)
    mc.intField('endFrameIF', edit=True, enable=True, value=maxTimelineFrame)

# Render Range button
def renderRange():
    minRenderFrame = mc.getAttr('defaultRenderGlobals.startFrame')
    maxRenderFrame = mc.getAttr('defaultRenderGlobals.endFrame')
    mc.intField('startFrameIF', edit=True, enable=True, value=minRenderFrame)
    mc.intField('endFrameIF', edit=True, enable=True, value=maxRenderFrame)

# Render Path dialog window
def renderPathDialog():
    dirName = mc.workspace( q=True, rootDirectory=True )
    openFileNameR = mc.fileDialog2(caption="Render Path", fileMode=1, startingDirectory=dirName, fileFilter='*.*')
    mc.textField('renderPathTF', edit=True, text=openFileNameR[0])

# Backburner Path dialog window
def backburnerPathDialog():
    dirName = mc.workspace( q=True, rootDirectory=True )
    openFileNameB = mc.fileDialog2(caption="Render Path", fileMode=1, startingDirectory=dirName, fileFilter='*.*')
    mc.textField('bburnerPathTF', edit=True, text=openFileNameB[0])

# Task List Name
def taskListName():
    taskList = mc.textField('jobNameTF', query=True, text=True)
    tempDir = tempfile.gettempdir()
    tempDir = tempDir.replace("\\", '/')
    tempDir += '/' + taskList + '.txt'
    return tempDir

# Create Task List
def createTaskList():
    filename = taskListName()
    taskListFile = open(filename, 'w')
    if (taskListFile == 0):
        mc.error('You dont have privilages')

    startFrame = mc.intField('startFrameIF', query=True, value=True)
    endFrame = mc.intField('endFrameIF', query=True, value=True)
    taskSize = mc.intField('taskSizeIF', query=True, value=True)

    if (taskSize == 0):
        mc.error('Task size should be greater than 0.')

    numberTasks = (float(endFrame) - float(startFrame)) / float(taskSize)
    if (numberTasks > int(numberTasks)):
        numberTasks = int(numberTasks) + 1

    startTaskFrame = startFrame
    lastTaskFrame = startFrame + taskSize - 1
    for task in range(int(numberTasks) + 1):
        if (lastTaskFrame >= endFrame):
            taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(endFrame) + "\t" + str(startTaskFrame) + "\t" + str(endFrame) + "\n")
            break
        taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(lastTaskFrame) + "\t" + str(startTaskFrame) + "\t" + str(lastTaskFrame) + "\n")
        startTaskFrame += taskSize
        lastTaskFrame += taskSize
    taskListFile.close()
    return filename

# Create Frames Task List
def createFramesTaskList():
    filename = taskListName()
    taskListFile = open(filename, 'w')
    if (taskListFile == 0):
        mc.error('You dont have privilages')

    frames = mc.textField('framesTF', query=True, text=True)
    taskSize = mc.intField('taskSizeIF', query=True, value=True)
    listB = frames.split(',')
    listA = []

    for each in listB:
        listA.append(each.replace(' ', ''))


    taskStartFrame = []
    taskEndFrame = []

    if (frames == ''):
        mc.error('Please complete Frames field.')

    if (taskSize == 0):
        mc.error('Task size should be greater than 0.')

    for task in range(len(listA)):
        if (listA[task].isdigit()):
            taskStartFrame.append(int(listA[task]))
            taskEndFrame.append(int(listA[task]))
        else:
            taskSeq = listA[task]
            taskSeq = taskSeq.split('-')
            if (len(taskSeq) == 0):
                result = re.sub("\d", "", taskSeq)
                mc.error('"' + result + '" is not an Integer.')
            else:
                seqFrames = []
                for seq in range(len(taskSeq)):
                    if (taskSeq[seq].isdigit()):
                        seqFrames.append(taskSeq[seq])
                    else:
                        result = re.sub("\d", "", taskSeq[seq])
                        mc.error('"' + result + '" is not an Integer.')
                if (int(seqFrames[1]) < int(seqFrames[0])):
                    mc.error('First frame is greater than second frame in sequence. ("' + seqFrames[0] + '" - "' + seqFrames[1] + '") ')
                taskStartFrame.append(int(seqFrames[0]))
                taskEndFrame.append(int(seqFrames[1]))

    for taskFrame in range(len(taskStartFrame)):
        if (taskStartFrame[taskFrame] == taskEndFrame[taskFrame]):
            taskListFile.write("frameRange " + str(taskStartFrame[taskFrame]) + "-" + str(taskEndFrame[taskFrame]) + "\t" + str(taskStartFrame[taskFrame]) + "\t" + str(taskEndFrame[taskFrame]) + "\n")
        else:
            numberTasks = (float(taskEndFrame[taskFrame]) - float(taskStartFrame[taskFrame])) / float(taskSize)
            if (numberTasks > int(numberTasks)):
                numberTasks = int(numberTasks) + 1
            startTaskFrame = taskStartFrame[taskFrame]
            lastTaskFrame = taskStartFrame[taskFrame] + taskSize - 1
            for task in range(int(numberTasks) + 1):
                if (lastTaskFrame >= taskEndFrame[taskFrame]):
                    taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(taskEndFrame[taskFrame]) + "\t" + str(startTaskFrame) + "\t" + str(taskEndFrame[taskFrame]) + "\n")
                    break
                taskListFile.write("frameRange " + str(startTaskFrame) + "-" + str(lastTaskFrame) + "\t" + str(startTaskFrame) + "\t" + str(lastTaskFrame) + "\n")
                startTaskFrame += taskSize
                lastTaskFrame += taskSize

    taskListFile.close()
    return filename

# Send Job
def sendJob(sendLayer=None):

    if (mc.radioButtonGrp('rangeRB', query=True, select=True) == 1):
        if (mc.checkBox('skipExistingFilesCB', query=True, value=True )):
            taskList = createSkipFramesTaskList(frameList=checkExistingFrames(checkLayer=sendLayer), layer=sendLayer)
        else:
            taskList = createTaskList()
    else:
        if (mc.checkBox('skipExistingFilesCB', query=True, value=True )):
            taskList = createSkipFramesTaskList(frameList=framesCheckExistingFrames(checkLayer=sendLayer), layer=sendLayer)
        else:
            taskList = createFramesTaskList()

    bburnerPathBB = errorMessageTF(property='bburnerPathTF', errorName='Backburner Path')
    jobNameBB = errorMessageTF(property='jobNameTF', errorName='Job Name')
    descriptionBB = mc.textField('descriptionTF', query=True, text=True )
    managerBB = errorMessageTF(property='managerNameTF', errorName='Manager Name')
    priorityBB = errorMessageIF(property='priorityIF', errorName='Priority')
    timeoutBB = errorMessageIF(property='timeoutIF', errorName='Timeout')
    renderPathBB = errorMessageTF(property='renderPathTF', errorName='Render Path')

    suspended = ''
    if (mc.checkBox('manualStartCB', query=True, value=True )):
        suspended = '-suspended '

    priority = priorityBB
    if (mc.checkBox('criticalCB', query=True, value=True )):
        priority = '0'

    rendererBB = ''
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 1 ):
        rendererBB = mc.getAttr("defaultRenderGlobals.currentRenderer")
        if (rendererBB == 'mayaHardware' ):rendererBB = 'hw'
        if (rendererBB == 'mayaSoftware' ):rendererBB = 'sw'
        if (rendererBB == 'mentalRay' ):rendererBB = 'mr'
        if (rendererBB == 'mayaVector' ):rendererBB = 'vr'

    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 2 ):rendererBB = 'mr'
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 3 ):rendererBB = 'sw'
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 4 ):rendererBB = 'hw'
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 5 ):rendererBB = 'vr'

    projectBB = mc.workspace( q=True, rootDirectory=True )

    verbosityBB = ''
    if ((mc.optionMenu('rendererOM', query=True, select=True)) == 2 ):
        verbosityBB = '-v ' + str(mc.optionMenu('verbosityOM', query=True, select=True) - 1)

    framePaddingBB = mc.intField('framePaddingIF', query=True, value=True )

    fileNameBB = mc.file(query=True, sceneName=True)
    if(fileNameBB == ''):
        mc.error('Save current file.')

    additionalOptionsBB = mc.textField('additionalOptionsTF', query=True, text=True )

    portBB = mc.intField('portIF', query=True, value=True )
    if (portBB == 0):
        portFlagBB = ''
    else:
        portFlagBB = ' -port ' + str(portBB)

    serverListBB = mc.textField('serverListTF', query=True, text=True )
    if (len(serverListBB)):
        serverListBB = ' -servers "' + serverListBB + '"'

    serverGroupBB = mc.textField('serverGroupTF', query=True, text=True )
    if (len(serverGroupBB)):
        serverGroupBB = ' -group "' + serverGroupBB + '"'

    serverCountBB = mc.intField('serverCountIF', query=True, value=True )
    if (serverCountBB == 0):
        serverCountFlagBB = ''
    else:
        serverCountFlagBB = ' -serverCount ' + serverCountBB

    renderFolderPath = mc.textField("renderFolder", query=True, text=True)

    renderLayerBB = ''
    layerJobName = sendLayer
    if (sendLayer != ''):
        renderLayerBB = (' -rl ' + sendLayer)
        layerJobName = ('_' + sendLayer)

    sendBB = ('"\\"\\"' + bburnerPathBB + '\\" -jobName \\"' + jobNameBB + layerJobName + '\\" -description \\"' + descriptionBB + '\\" -manager ')
    sendBB += (managerBB + portFlagBB + serverListBB + serverGroupBB + serverCountFlagBB +' ' + suspended + '-priority ')
    sendBB += (str(priority) + ' -taskList \\"' + taskList + '\\" -taskName 1 -timeout ' + str(timeoutBB))
    sendBB += (' \\"' + renderPathBB + '\\" -r ' + rendererBB + ' -s %tp2 -e %tp3 -proj \\"' + projectBB + '\\" -rd \\"' + renderFolderPath +'\\" ' + verbosityBB)
    sendBB += (renderLayerBB + ' -pad ' + str(framePaddingBB) + ' ' + additionalOptionsBB + ' \\"' + fileNameBB +'\\""')
    print sendBB
    return sendBB


#Close button
def closeBtn():
    mc.deleteUI("BburnWin")

# Submit button
def submitBtn():
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 1 ):
        send= sendJob(sendLayer='')
        print ('Backburner 1.0 by Mariano Antico.')
        print ('system (' + send + ')')
        printSend = mm.eval('system (' + send + ')')
        print printSend

    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 2 ):
        allLay = mc.ls(type='renderLayer')
        for layer in allLay:
            renderableLayer = mc.getAttr(layer + '.renderable')
            if (renderableLayer):
                send= sendJob(sendLayer=layer)
                print ('Backburner 1.2 by Mariano Antico.')
                print ('system (' + send + ')')
                printSend = mm.eval('system (' + send + ')')
                print printSend

    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 3 ):
        currentLay = mc.editRenderLayerGlobals(query=True, currentRenderLayer=True)
        send= sendJob(sendLayer=currentLay)
        print ('Backburner 1.2 by Mariano Antico.')
        print ('system (' + send + ')')
        printSend = mm.eval('system (' + send + ')')
        print printSend
    print 'Done!'

# Submit and Close
def submitCloseBtn():
    submitBtn()
    closeBtn()

# skip button disable task size
def skipBtn():
    if (mc.checkBox('skipExistingFilesCB', query=True, value=True )):
        mc.intField('taskSizeIF', edit=True, value=1, enable=False)
        mc.text('taskSizeTX', edit=True, enable=False)
    else:
        mc.intField('taskSizeIF', edit=True, enable=True)
        mc.text('taskSizeTX', edit=True, enable=True)

# Layer Task List Name
def taskListLayerName(Tasklayer=''):
    taskList = mc.textField('jobNameTF', query=True, text=True)
    tempDir = tempfile.gettempdir()
    tempDir = tempDir.replace("\\", '/')
    tempDir += '/' + taskList + '_' + Tasklayer + '.txt'
    return tempDir

# replace name from File Name Prefix
def replaceNamePrefix(fileName=None, replaceLayer=''):

    passes = listPasses(layerPass=replaceLayer)
    if passes:
        if not re.search('<RenderPass>', fileName):
            fileName = 'MasterBeauty/' + fileName

    cams = listRenderCameras(layerCam=replaceLayer)
    if len(cams) > 1:
        if not re.search('<Camera>', fileName):
            fileName = '<Camera>/' + fileName

    if not re.search('<RenderLayer>', fileName):
        fileName = replaceLayer + '/' + fileName

    directoryReplace = fileName.split('/')
    renderCams = []

    index = -1
    for directory in directoryReplace:
        index += 1
        if re.search('<Scene>', directory):
            sceneName = mc.file(query=True, shortName=True, sceneName=True)
            sceneName = sceneName.split(".")
            sceneNamePeriod = ''
            if len(sceneName) >= 1:
                for index in range(len(sceneName) - 1):
                    sceneNamePeriod += sceneName[index] + '.'
                sceneName = sceneNamePeriod
                sceneName = sceneName[:(len(sceneName)-1)]
            else :
                sceneName = sceneName.split(".")[0]
            if (sceneName == ''):
                sceneName = 'untitled'
            directoryReplace[index] = directoryReplace[index].replace('<Scene>',sceneName)
        if re.search('<RenderLayer>', directory):
            currentLay = replaceLayer
            if currentLay == 'defaultRenderLayer':
                currentLay = 'masterLayer'
            directoryReplace[index] = directoryReplace[index].replace('<RenderLayer>',currentLay)
        if re.search('<Camera>', directory):
            camRender = replaceCameras(layerCam=replaceLayer)
            if camRender:
                directoryReplace[index] = directoryReplace[index].replace('<Camera>',camRender)
            else :
                cameras = mc.ls(cameras=True)
                for cam in cameras:
                    renderableCam = mc.getAttr(cam + '.renderable')
                    if renderableCam:
                        mc.select(cam, replace=True)
                        camTransform = str(mc.pickWalk( direction='up' )[0])
                        renderCams.append(camTransform)
                directoryReplace[index] = directoryReplace[index].replace('<Camera>',renderCams[0])
        if re.search('<RenderPassFileGroup>', directory):
            directoryReplace[index] = directoryReplace[index].replace('<RenderPassFileGroup>','Beauties')
        if re.search('<RenderPass>', directory):
            directoryReplace[index] = directoryReplace[index].replace('<RenderPass>','MasterBeauty')
        if re.search('<RenderPassType>', directory):
            directoryReplace[index] = directoryReplace[index].replace('<RenderPassType>','BEAUTY')
        if re.search('<Extension>', directory):
            outFormat = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.outFormatControl')
            if outFormat == 2:
                outFormatExt = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.outFormatExt')
                directoryReplace[index] = directoryReplace[index].replace('<Extension>',outFormatExt)
            elif outFormat == 0:
                extension = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.imfPluginKey')
                directoryReplace[index] = directoryReplace[index].replace('<Extension>',extension)
            else :
                directoryReplace[index] = directoryReplace[index].replace('<Extension>','')
        if re.search('<Version>', directory):
            version = overrideCheckParameter(layerPrefix=replaceLayer, propPrefix='defaultRenderGlobals.renderVersion')
            directoryReplace[index] = directoryReplace[index].replace('<Version>',version)

    imageDir = ''
    for dir in range(len(directoryReplace)):
        if dir == (len(directoryReplace) - 1):
            imageDir += directoryReplace[dir]
            break
        imageDir += directoryReplace[dir] + '/'

    return imageDir

def replaceCameras(layerCam=''):
    valueExtOverride = ''
    renderCam = ''
    overrides = mc.listConnections(layerCam + '.adjs', destination=False, source=True, plugs=True)
    if overrides:
        for index in range(len(overrides)):
            if re.search('.renderable', overrides[index]):
                valueExtOverride = mc.getAttr(layerCam + '.adjs[' + str(index) + '].value')
                if valueExtOverride:
                    mc.select(overrides[index].split('.')[0], replace=True)
                    camTransform = str(mc.pickWalk( direction='up' )[0])
                    renderCam = camTransform
                    return renderCam
                    break
    return renderCam

def listRenderCameras(layerCam=''):
    mc.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
    valueExtOverride = ''
    renderCam = []
    overrides = mc.listConnections(layerCam + '.adjs', destination=False, source=True, plugs=True)
    if overrides:
        for index in range(len(overrides)):
            if re.search('.renderable', overrides[index]):
                valueExtOverride = mc.getAttr(layerCam + '.adjs[' + str(index) + '].value')
                if valueExtOverride:
                    mc.select(overrides[index].split('.')[0], replace=True)
                    camTransform = str(mc.pickWalk( direction='up' )[0])
                    renderCam.append(camTransform)
    return renderCam

def overrideCheckParameter(layerPrefix='', propPrefix=''):
    mc.editRenderLayerGlobals(currentRenderLayer='defaultRenderLayer')
    valueExtOverride = ''
    overrides = mc.listConnections(layerPrefix + '.adjs', destination=False, source=True, plugs=True)
    switch = 0
    if overrides:
        for index in range(len(overrides)):
            valueExtOverride = mc.getAttr(layerPrefix + '.adjs[' + str(index) + '].value')
            if re.search(propPrefix, overrides[index]):
                valueExtOverride = mc.getAttr(layerPrefix + '.adjs[' + str(index) + '].value')
                switch = 1
                #mc.editRenderLayerGlobals(currentRenderLayer=layerPrefix)
                break
    if not switch:
        valueExtOverride = mc.getAttr(propPrefix)
        #mc.editRenderLayerGlobals(currentRenderLayer=layerPrefix)
    return valueExtOverride

def listPasses(layerPass=''):
    passes = mc.ls(type='renderPass')
    hasPass = 0
    if passes:
        associatePass = mc.listConnections(layerPass + ".renderPass")
        if associatePass:
            hasPass = 1
    return hasPass

# Cheack Existing Frames
def checkExistingFrames(checkLayer=''):

    projectBB = mc.workspace( q=True, rootDirectory=True )

    imagesWorkSpace = mc.workspace( q=True, fileRule=True )
    imagesDir = ''
    count = 0
    for directory in imagesWorkSpace:
        count += 1
        if re.search('images', directory):
            imagesDir = imagesWorkSpace[count] + '/'
            break

    output = replaceNamePrefix(fileName = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imageFilePrefix'), replaceLayer=checkLayer)
    outputFile = output.split('/')[-1]

    outputDirSplit = output.split('/')
    outputDir = ''
    for dir in range(len(outputDirSplit) - 1):
        outputDir += outputDirSplit[dir] + '/'

    currentLay = checkLayer
    extension = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imfPluginKey')
    stratFrame = mc.intField('startFrameIF', query=True, value=True)
    endFrame = mc.intField('endFrameIF', query=True, value=True)

    outFormat = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatControl')
    animation = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.animation')
    putFrameBefore = mc.getAttr('defaultRenderGlobals.putFrameBeforeExt')
    periodInExt = mc.getAttr('defaultRenderGlobals.periodInExt')
    padding = mc.intField('framePaddingIF', query=True, value=True)
    outFormatExt = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatExt')
    frameList = []

    if (outFormat == 1 and animation == 0):
        # file format ('name (single)')
        outputFiles = outputFile
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 0):
        # file format ('name.ext (single)')
        outputFiles = outputFile + '.' + extension
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.ext')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.ext.%')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + extension + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 1 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.ext')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.ext')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))

    if (outFormat == 2 and animation == 0):
        # file format ('name.outFormatExt (single)')
        outputFiles = outputFile + '.' + outFormatExt
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.outFormatExt')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.outFormatExt.%')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + outFormatExt + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.outFormatExt')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.outFormatExt')
        for number in range(endFrame - stratFrame + 1):
            frameNum = format(int(number + stratFrame), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number + stratFrame))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number + stratFrame))

    return frameList

# Create Seq Task List and skip existing frames
def createSkipFramesTaskList(frameList=[], layer=''):
    if not frameList:
        mc.error(layer + ': All frames you wanto to render. Already exists. Disable Skip Existing Frames if you wanto to overwrite.')
    if frameList[0] == 'single':
        mc.error('You are trying to render a sequence, but you have set to render a Single Frame not an Animation.')
    filename = taskListLayerName(Tasklayer=layer)
    taskListFile = open(filename, 'w')
    if (taskListFile == 0):
        mc.error('You dont have privilages')

    startFrame = frameList[0]
    endFrame = frameList[-1]
    taskSize = 1

    taskFrame = startFrame
    for task in range(len(frameList)):
        taskFrame = frameList[task]
        taskListFile.write("frameRange " + str(taskFrame) + "-" + str(taskFrame) + "\t" + str(taskFrame) + "\t" + str(taskFrame) + "\n")
    taskListFile.close()
    return filename

# Create Frames List Skip Existing Files
def createListFramesSkipTaskList():
    frames = mc.textField('framesTF', query=True, text=True)
    taskSize = 1
    listB = frames.split(',')
    listA = []
    frameList = []

    for each in listB:
        listA.append(each.replace(' ', ''))

    taskStartFrame = []
    taskEndFrame = []

    if (frames == ''):
        mc.error('Please complete Frames field.')

    if (taskSize == 0):
        mc.error('Task size should be greater than 0.')

    for task in range(len(listA)):
        if (listA[task].isdigit()):
            taskStartFrame.append(int(listA[task]))
            taskEndFrame.append(int(listA[task]))
        else:
            taskSeq = listA[task]
            taskSeq = taskSeq.split('-')
            if (len(taskSeq) == 0):
                result = re.sub("\d", "", taskSeq)
                mc.error('"' + result + '" is not an Integer.')
            else:
                seqFrames = []
                for seq in range(len(taskSeq)):
                    if (taskSeq[seq].isdigit()):
                        seqFrames.append(taskSeq[seq])
                    else:
                        result = re.sub("\d", "", taskSeq[seq])
                        mc.error('"' + result + '" is not an Integer.')
                if (int(seqFrames[1]) < int(seqFrames[0])):
                    mc.error('First frame is greater than second frame in sequence. ("' + seqFrames[0] + '" - "' + seqFrames[1] + '") ')
                taskStartFrame.append(int(seqFrames[0]))
                taskEndFrame.append(int(seqFrames[1]))

    for taskFrame in range(len(taskStartFrame)):
        if (taskStartFrame[taskFrame] == taskEndFrame[taskFrame]):
            frameList.append(taskStartFrame[taskFrame])
        else:
            numberTasks = (float(taskEndFrame[taskFrame]) - float(taskStartFrame[taskFrame])) / float(taskSize)
            if (numberTasks > int(numberTasks)):
                numberTasks = int(numberTasks) + 1
            startTaskFrame = taskStartFrame[taskFrame]
            lastTaskFrame = taskStartFrame[taskFrame] + taskSize - 1
            for task in range(int(numberTasks) + 1):
                if (lastTaskFrame >= taskEndFrame[taskFrame]):
                    frameList.append(startTaskFrame)
                    break
                frameList.append(startTaskFrame)
                startTaskFrame += taskSize
                lastTaskFrame += taskSize

    return frameList

# Cheack Existing Frames for frame render mode
def framesCheckExistingFrames(checkLayer=''):
    projectBB = mc.workspace( q=True, rootDirectory=True )

    imagesWorkSpace = mc.workspace( q=True, fileRule=True )
    imagesDir = ''
    count = 0
    for directory in imagesWorkSpace:
        count += 1
        if re.search('images', directory):
            imagesDir = imagesWorkSpace[count] + '/'
            break

    output = replaceNamePrefix(fileName = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imageFilePrefix'), replaceLayer=checkLayer)
    outputFile = output.split('/')[-1]

    outputDirSplit = output.split('/')
    outputDir = ''
    for dir in range(len(outputDirSplit) - 1):
        outputDir += outputDirSplit[dir] + '/'

    currentLay = checkLayer
    extension = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.imfPluginKey')
    frames = createListFramesSkipTaskList()

    outFormat = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatControl')
    animation = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.animation')
    putFrameBefore = mc.getAttr('defaultRenderGlobals.putFrameBeforeExt')
    periodInExt = mc.getAttr('defaultRenderGlobals.periodInExt')
    padding = mc.intField('framePaddingIF', query=True, value=True)
    outFormatExt = overrideCheckParameter(layerPrefix=checkLayer, propPrefix='defaultRenderGlobals.outFormatExt')
    frameList = []

    if (outFormat == 1 and animation == 0):
        # file format ('name (single)')
        outputFiles = outputFile
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 0):
        # file format ('name.ext (single)')
        outputFiles = outputFile + '.' + extension
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.ext.%')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + extension + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 1 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 0 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  extension
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))

    if (outFormat == 2 and animation == 0):
        # file format ('name.ext (single)')
        outputFiles = outputFile + '.' + outFormatExt
        if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
            frameList.append('single')
        else:
            fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
            if fileSize < 129:
                frameList.append('single')
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 1):
        # file format ('name.%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 0 and periodInExt == 1):
        # file format ('name.ext.%')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '.' + outFormatExt + '.' + frameNum
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 0):
        # file format ('name%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))
    if (outFormat == 2 and animation == 1 and putFrameBefore == 1 and periodInExt == 2):
        # file format ('name_%.ext')
        for number in frames:
            frameNum = format(int(number), ('0' + str(padding) + 'd'))
            outputFiles = outputFile + '_' + frameNum + '.' +  outFormatExt
            if not os.path.exists(projectBB + imagesDir + outputDir + outputFiles):
                frameList.append(int(number))
            else :
                fileSize = os.path.getsize (projectBB + imagesDir + outputDir + outputFiles)
                if fileSize < 129:
                    frameList.append(int(number))

    return frameList

#switch Render Mode - Skip Existing Frames
def switchRenderMode():
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 1 ):
        mc.checkBox('skipExistingFilesCB', edit=True, value=False, enable=False)
        mc.intField('taskSizeIF', edit=True, enable=True)
        mc.text('taskSizeTX', edit=True, enable=True)
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 2 ):
        mc.checkBox('skipExistingFilesCB', edit=True, enable=True)
    if ((mc.radioButtonGrp('renderModeRB', query=True, select=True)) == 3 ):
        mc.checkBox('skipExistingFilesCB', edit=True, enable=True)
backBurner()
setRenderFolder()
