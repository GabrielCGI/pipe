from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from importlib import reload
import qtpy.QtWidgets as qt
import traceback
import sys
import os


file_path = os.path.dirname(__file__)
projet = file_path.split("\\")[1]

MODULES_SEARCH_PATH = f"i:/{projet}/.pipelines_deploy/maya/scripts"
if MODULES_SEARCH_PATH not in sys.path:
    sys.path.insert(0, MODULES_SEARCH_PATH)


name = "Plugin Reference Updater"
classname = "PluginReferenceUpdater"



class PluginReferenceUpdater:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"
        
        self.core.registerCallback("openPBFileContextMenu", self.sceneContextMenu, plugin=self)

    @err_catcher(name=__name__)
    def sceneContextMenu(self, origin, menu, path:  str):
        if path.endswith(".ma") or path.endswith(".mb"):
            self.add_actions(menu, path)

    def add_actions(self, menu, path):
        action = menu.addAction("Update/add reference UI")
        action.triggered.connect(lambda: self.updateReferenceWithUI(path))

    def updateReferenceWithUI(self, path):
        try:
            import anm_reference_updater
            reload(anm_reference_updater)
            self.waiter = None
            self.win = anm_reference_updater.mainUI(True, self.core, None, path)
            self.win.show()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self.core.popup("module refUpdater not found\n" + MODULES_SEARCH_PATH)
            self.core.popup(traceback.format_exc())