from PrismUtils.Decorators import err_catcher_plugin as err_catcher
import qtpy.QtWidgets as qt
from pathlib import Path
from imp import reload
import importlib
import socket
import sys
import os

DEBUG = 0
MODULES_SEARCH_PATH = ["R:/pipeline/pipe/prism/referenceUpdater"]
for module_path in MODULES_SEARCH_PATH:
    if not module_path in sys.path:
        sys.path.append(module_path)

try:
    import refUpdater as refUp
except:
    pass

name = "Reference Updater"
classname = "ReferenceUpdater"

if socket.gethostname() == "FALCON-01" and DEBUG:
    import ctypes
    ctypes.windll.kernel32.AllocConsole()
    sys.stdout = open('CONOUT$', 'w')
    sys.stderr = open('CONOUT$', 'w')
    sys.stdin = open('CONIN$', 'r')

class ReferenceUpdater:
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
            reload(refUp)
            self.worker = refUp.instanceWorker(self, "Maya", path, self.core.projectPath)
            self.worker.runUpdate(True)
            self.waiter = refUp.LoadingWindow("waite the script process...")
            self.waiter.show()
        except:
            self.core.popup("module refUpdater not found")

    def updateReferenceWithUI(self, path):
        try:
            reload(refUp)
            self.waiter = None
            self.win = refUp.startWithRef(self, "Maya", path, self.core.projectPath)
            self.win.show()
        except Exception as e:
            print(e)
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
        