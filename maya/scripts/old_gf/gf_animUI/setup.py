from gf_animUI import ui
from gf_animUI import ui_tools
import gf_animUI.object_sets as objSets

# animLauncherUI = ui.AnimLauncherDialog(ui.DockedAnimWindow)


def findUI(uiType):
    mayaMainWindow = ui.getMayaWindow()
    return mayaMainWindow.findChildren(uiType)


def onSceneChanged(*args, **kwargs):
    launcherWidgets = ui.AnimLauncherDialog.list()
    animWidgets = ui.AnimWindow.list()

    for w in launcherWidgets:
        w.loadMasterSets()

    for w in animWidgets:
        w.close()

__newSceneCallback = ui_tools.MSceneCallbackHandler('afterNew', onSceneChanged)
__newSceneCallback.install()

__openSceneCallback = ui_tools.MSceneCallbackHandler('afterOpen', onSceneChanged)
__openSceneCallback.install()