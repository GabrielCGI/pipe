from importlib import reload
import qtpy.QtWidgets as qt
import traceback
import sys



# from  USDExport_anim import CustomExportAnim
from custom_export_UI import CustomExportUI
from custom_preExport import CustomPreExport



PRISM_SCRIPT_PATH = "R:/pipeline/pipe/prism"



class Prism_CustomStateManager_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        self.core.registerCallback("onStateStartup", self.onStateStartup, plugin=self, priority=40)
        self.core.registerCallback("onStateManagerOpen", self.EditStateManagerUI, plugin=self)
        self.core.registerCallback("preExport", self.preExport, plugin=self)
    #     self.core.registerCallback("onStateManagerOpen", self.createCustom_state_anim, plugin=self)

    # def createCustom_state_anim(self, origin):
    #     origin.loadState(CustomExportAnim) #pour creer ses propre state d'export


    # ---------------- modification de l'interface des states Export et D'USD export ----------------
    def onStateStartup(self, state):
        if self.core.appPlugin.pluginName != "Maya":
            return
        CustomExportUI(state)
    
    def preExport(self, **kwargs):
        if self.core.appPlugin.pluginName != "Maya":
            return
        CustomPreExport(kwargs)


    # ------------------------ modification de l'interface du state Manager -------------------------
    def EditStateManagerUI(self, origin) -> None:
        if self.core.appPlugin.pluginName != 'Maya':
            return
        
        self.origin = origin
        self.origin.gb_import.hide()

        box_edit_import = qt.QGroupBox(self.origin.splitter_2)
        self.origin.splitter_2.insertWidget(0, box_edit_import)
        lay = qt.QHBoxLayout(box_edit_import)

        qt_btn_ReferenceUpdater = qt.QPushButton("Reference Updater")
        qt_btn_ReferenceUpdater.clicked.connect(self.runReferenceUpdater)
        self.customSheet(qt_btn_ReferenceUpdater)
        lay.addWidget(qt_btn_ReferenceUpdater)

        qt_btn_showImport = qt.QPushButton("Show more")
        qt_btn_showImport.clicked.connect(self.showGroupBoxImport)
        qt_btn_showImport.setMaximumWidth(80)
        self.customSheet(qt_btn_showImport)
        lay.addWidget(qt_btn_showImport)
    
    def showGroupBoxImport(self) -> None:
        if self.origin.gb_import.isHidden():
            self.origin.gb_import.show()
        else:
            self.origin.gb_import.hide()
    
    def runReferenceUpdater(self) -> None:
        if not PRISM_SCRIPT_PATH in sys.path:
            sys.path.append(PRISM_SCRIPT_PATH)
        
        try:
            import referenceUpdater as refUp #type: ignore
            reload(refUp)
        except:
            traceback.print_exc()
            print("impossible de load refUpdater")
            return

        try:
            from maya import OpenMayaUI
            from shiboken6 import wrapInstance

            main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
            instance = wrapInstance(int(main_window_ptr), qt.QWidget)
            win = refUp.mainUI(self, "Maya", self.core.getCurrentFileName(), self.core.projectPath, False, False, instance)
            win.show()

        except Exception as e:
            print(e)
    
    def customSheet(self, bb) -> None:
        bb.setStyleSheet("""
        QPushButton {
            background-color: #303030; 
            border: 1px solid #D2D2D7; 
            border-radius: 5px;
            padding: 5px 8px;
        }
        QPushButton:hover {
            background-color: #505050;
        }

        QPushButton:pressed {
            background-color: #404040;
        }""")