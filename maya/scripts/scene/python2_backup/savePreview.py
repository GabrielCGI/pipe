import maya.cmds as cmds
import maya.mel as mel
import maya.app.general.createImageFormats as createImageFormats
import os


def savePreview():
    #Get the current scene path
    scenePath = cmds.file(q=True, sceneName=True)
    #Get the parent directory
    pardir =  os.path.dirname(scenePath)
    #Get the scene name
    fullSceneName = os.path.basename(scenePath)
    #Split scene name and extension
    sceneName, extension = os.path.splitext(fullSceneName)
    #Create preview name
    previewName = sceneName + ".jpg"
    #Create preview path
    previewPath = os.path.join(pardir,previewName)

    #Start render and save
    mel.eval('renderWindowRender redoPreviousRender renderView')
    editor = 'renderView'
    formatManager = createImageFormats.ImageFormats()
    formatManager.pushRenderGlobalsForDesc("JPEG")
    cmds.renderWindowEditor(editor, e=True, writeImage=previewPath, com=True)
    formatManager.popRenderGlobals()
