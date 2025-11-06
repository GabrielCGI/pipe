from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from importlib import reload
import qtpy.QtWidgets as qt
import traceback
import sys


MODULES_SEARCH_PATH = ["R:/pipeline/pipe/prism"]
for module_path in MODULES_SEARCH_PATH:
    if not module_path in sys.path:
        sys.path.insert(0, module_path)



name = "Plugin Reference Updater"
classname = "PluginReferenceUpdater"



class PluginReferenceUpdater:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"
        
        self.core.registerCallback("openPBFileContextMenu", self.sceneContextMenu, plugin=self)

    @err_catcher(name=__name__)
    def sceneContextMenu(self, origin, menu, path):
        print(path)
        self.add_actions(menu, path)

    def add_actions(self, menu, path):
        action = menu.addAction("Update Reference")
        action.triggered.connect(lambda: self.updateReference(path))

        action = menu.addAction("Update/add reference UI")
        action.triggered.connect(lambda: self.updateReferenceWithUI(path))
    
    def updateReference(self, path):
        try:
            import referenceUpdater as refUp
            reload(refUp)
            self.worker = refUp.instanceWorker(self, "Maya", path, self.core.projectPath)
            self.worker.runUpdate(True)
            self.waiter = refUp.loadingScreen("waite the script process...")
            self.waiter.show()
        except:
            self.core.popup("module refUpdater not found")

    def updateReferenceWithUI(self, path):
        try:
            import referenceUpdater as refUp
            reload(refUp)
            self.waiter = None
            self.win = refUp.mainUI(self, "Maya", path, self.core.projectPath, True)
            self.win.show()
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self.core.popup(f"module refUpdater not found")


    def handleError(self, msg):
        try:
            self.waiter.close()
        except:
            pass
        print(msg)
        self.core.popup(f"ERROR" + msg, severity="warning")

    def handleResult(self, msg):
        try:
            self.waiter.close()
        except:
            pass
        print(msg)
        if not msg:
            self.core.popup(f"tout c'est bien passer", severity="info")
        else:
            self.core.popup(f"Error" + msg, severity="error")