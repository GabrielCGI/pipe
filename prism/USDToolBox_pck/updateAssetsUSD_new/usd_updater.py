
# standard deps
from enum import Enum
from pathlib import Path
import subprocess
import logging
import socket
import glob
import json
import sys
import os

# packages deps
from . import usd_parser
from .assetitem import AssetItem
from . import loggingsetup
from . import usd_check

UD_MODULE_ROOT = os.path.dirname(__file__)
UD_ROOT = os.path.dirname(UD_MODULE_ROOT)

_ENV_ENABLE_DEBUG = bool(int(os.environ.get("UD_DEBUG", False)))
_ENV_LOG_DIR = os.environ.get("UD_LOG_DIR", False)
_ENV_QT_FROM_PRISM = bool(int(os.environ.get("UD_QT_FROM_PRISM", True)))

"""
Debug environnement specification
DEV_LIST hold list of machine name that are allowed to debug
DEBUG_MODE can be set manually and 
work only when debug module is present
"""
DEV_LIST = [
    'FOX-04'
]
_DEBUG_MODE = _ENV_ENABLE_DEBUG and socket.gethostname() in DEV_LIST
if _DEBUG_MODE: # pragma: no cover
    try:
        from . import debug
    except:
        _DEBUG_MODE = False

# Logger setups using logconfig.json parameters
LOG_CONFIG = os.path.join(UD_MODULE_ROOT, "config/logconfig.json")

_DEFAULT_LOG_DIR = os.path.join(UD_ROOT, "logs")
LOG_DIRECTORY = _ENV_LOG_DIR if _ENV_LOG_DIR else _DEFAULT_LOG_DIR
LOG_ERROR_FILE = os.path.join(LOG_DIRECTORY, "error_log.txt")

is_log_setup = loggingsetup.setup_log(
    logName='update_usd',
    logConfigPath=LOG_CONFIG,
    logDirectory=LOG_DIRECTORY,
    with_time=False
)
if not is_log_setup: # pragma: no cover
    with open(LOG_ERROR_FILE, 'w') as error_log:
        error_log.write(f'Could not setup log from {LOG_CONFIG}')

logger = logging.getLogger(__name__)
logger.info('Module loaded')


def import_qtpy():
    """
    Try to import qtpy from any prism install found in C:/ILLOGIC_APP/Prism.

    Returns:
        bool: True if the import path is found and False otherwise 
    """
    
    prism_qt_glob_pattern = "C:/ILLOGIC_APP/Prism/*/app/PythonLibs/*"

    found = False
    for path in glob.glob(prism_qt_glob_pattern):
        pyside_path = os.path.join(path, 'PySide')
        if os.path.exists(pyside_path):
            found = True
            break
    
    if not found: # pragma: no cover
        return False
    
    if pyside_path not in sys.path:
        sys.path.insert(0, pyside_path)
    if path not in sys.path:
        sys.path.insert(0, path)
    return True

# Import qt with qtpy of prism to match any version of qt found
# https://pypi.org/project/QtPy/
if _ENV_QT_FROM_PRISM: # pragma: no cover
    if not import_qtpy():
        logger.error(f'qtpy not found in C:/ILLOGIC_APP/Prism')
        sys.exit(1)
        
try: # pragma: no cover
    from qtpy import QtWidgets as Qt
    from qtpy import QtCore as Qtc
    from qtpy import QtGui as Qtg
except ImportError as e: # pragma: no cover
    logger.error(str(e))
    sys.exit(1)
    

#import USD libs
try: # pragma: no cover
    from pxr import Sdf, Usd
except ImportError as e: # pragma: no cover
    logger.error(str(e))
    sys.exit(1)

#import for maya 
try: # pragma: no cover
    from maya import OpenMayaUI, cmds # type: ignore
    import mayaUsd # type: ignore
    from shiboken6 import wrapInstance
except: # pragma: no cover
    pass

#import for houdini 
try:
    import hou # type: ignore
except:
    pass

EXPORT_PATHS_JSON = os.path.join(UD_MODULE_ROOT, "config/export_paths.json")
_PRODUCTION_IDENTIFIER = "03_Production"

class AssetListWidget(Qt.QListWidget):
    
    
    class LayerType(Enum):
        CONTAINER = "Container"
        DEPARTEMENT = "Departement"
        SUBLAYER = "Sublayer"
    
    
    def __init__(self, dependance=None, parent=None):
        super().__init__(parent)
        self.layer: Sdf.Layer = None
        self.layer_item = None
        self.can_be_updated = True
        self.isUpdate = False
        self.layer_type = self.LayerType.CONTAINER
        self.dependance = dependance


class LayerWidget(Qt.QWidget):


    class UpdateTextEnum(Enum):
        UPDATED = "<b style=\"color: green;\">(Updated)</b>"
        NOT_UPDATED = "<b style=\"color: red;\">(Not updated)</b>"
    
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.is_update = False

        self.mainLayout = Qt.QHBoxLayout()
        self.setLayout(self.mainLayout)
        
        self.label = Qt.QLabel(text)
        self.mainLayout.addWidget(self.label)
        self.mainLayout.addStretch()
        
        self.update_label = Qt.QLabel(self.UpdateTextEnum.UPDATED.value)
        self.mainLayout.addWidget(self.update_label)


    def sizeHint(self) -> Qtc.QSize:
        size = super().sizeHint()
        size += Qtc.QSize(0, 2)
        return size 


    def setUpdated(self, on: bool):
        self.is_update = on
        if self.is_update:
            self.update_label.setText(self.UpdateTextEnum.UPDATED.value)
        else:
            self.update_label.setText(self.UpdateTextEnum.NOT_UPDATED.value)


class LayerList(Qt.QListWidget):
    
    
    def __init__(self, ui, parent=None):
        super().__init__(parent)
        self.main_ui: MainInterface = ui
        
        
    def buildMenu(self, menu: Qt.QMenu) -> Qt.QMenu:
        selected_indexes = self.selectedIndexes()
        if not selected_indexes:
            return
        current_index = selected_indexes[0].row()
        
        openexplorerAction = menu.addAction("Open in Explorer")
        openexplorerAction.triggered.connect(
            lambda: self.main_ui.openInExplorer(current_index)
        )
        
        openexternalAction = menu.addAction("Open in External Editor")
        openexternalAction.triggered.connect(
            lambda: self.main_ui.openExternal(current_index)
        )
                
        removeAction = menu.addAction("Remove layer")
        removeAction.triggered.connect(
            lambda: self.main_ui.removeLayerAtIndex(current_index)
        )
        menu.addAction(removeAction)
        return menu

    def contextMenuEvent(self, event: Qtg.QContextMenuEvent):
        self.contextmenu = Qt.QMenu(self)
        self.contextmenu = self.buildMenu(self.contextmenu)
        if hasattr(self.contextmenu, 'exec'):
            self.contextmenu.exec(event.globalPos())
        elif hasattr(self.contextmenu, 'exec_'):
            self.contextmenu.exec_(event.globalPos())

        
class MainInterface(Qt.QMainWindow):
    
    
    class SeverityFlag(Enum):
        WARNING = "⚠️"
        ERROR = "⛔"
    
    
    def __init__(
            self,
            openType=None,
            pathPrism=None,
            pcore=None,
            ar_context=None,
            check_update_only=False,
            parent=None):
        
        super(MainInterface, self).__init__(parent)
        self.setWindowTitle("USD Updater 1.0")
        self.resize(1200, 800)
        self.openType = openType
        self.pathPrism = pathPrism
        self.pcore = pcore

        # layers informations
        self._pathFiles: list[str] = []
        self._hiddenDependencies: list[str] = []
        self._layers: list[Sdf.Layer] = []
        self._assetsToUpdate: dict[list[AssetItem]] = {}
        
        # opentype specific informations
        if self.openType == 'houdini':
            self._houdini_nodes = []
        
        # parser informations
        self.update_mode = usd_parser.USDParser.UpdateMode.NEW_VERSION
        self.check_update_only = check_update_only
        self._enable_recursion = False
        self._usd_parser = usd_parser.USDParser(self.log)
        if ar_context is not None:
            self.setArContext(ar_context) 
        
        logger.info('Open USD updater in dev mode')
        logger.info(f'Started from "{__file__}"')

        # --------------------------Create interface--------------------------
        Mainwindow = Qt.QWidget()
        self.setCentralWidget(Mainwindow)
        mainLayout = Qt.QVBoxLayout(Mainwindow)

        # -----------------mode Update Worklayer ou USD file-----------------
        self.targetMode = Qt.QComboBox()
        if self.openType == 'maya': # pragma: no cover
            targetModeItem = [
                "Update from USD file",
                "Update Current Work Layer"
            ]
        else:
            targetModeItem = [
                "Update from USD file"
            ]
        self.targetMode.addItems(targetModeItem)
        
        if self.openType == 'maya': # pragma: no cover
            self.targetMode.setCurrentIndex(1)
        else:
            self.targetMode.setCurrentIndex(0)
            
        self.targetMode.currentIndexChanged.connect(
            self.find_USD_file_to_update
        )
        mainLayout.addWidget(self.targetMode)
        
        # -----------choisir quelle layer d'USD choisir à modiffier-----------
        file_layout = Qt.QHBoxLayout()

        self.USDFileNeedUpdate = Qt.QLineEdit()
        file_layout.addWidget(self.USDFileNeedUpdate)
        
        self.filePathBtn = Qt.QPushButton("Add Layer...")
        self.filePathBtn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.filePathBtn)
    
        if self.openType == "houdini": # pragma: no cover
            self.reloadButton = Qt.QPushButton("Reload From Nodes")
            self.reloadButton.clicked.connect(self.find_USD_file_to_update)
            file_layout.addWidget(self.reloadButton)
        
        mainLayout.addLayout(file_layout)
        
        # ---------list de tout ce qu'il faut update dans la stack US---------
                
        layerLayout = Qt.QHBoxLayout()
        mainLayout.addLayout(layerLayout)
        
        self.layerList = LayerList(self)
        layerLayout.addWidget(self.layerList, 33)
        
        self.QTabLayers = Qt.QTabWidget()
        # set stylesheet to prevent prism pipeline overriding it
        self.QTabLayers.setStyleSheet("QTabWidget::tab-bar {alignment: left;}")
        self.QTabLayers.tabBar().hide()
        
        self.layerList.itemSelectionChanged.connect(
            self.onSelectedLayerChanged
        )
        
        layerLayout.addWidget(self.QTabLayers, 67)

        # -------------------------layout des boutton-------------------------
        self.layoutButon = Qt.QHBoxLayout()
        mainLayout.addLayout(self.layoutButon)
        
        self.selAllButton = Qt.QPushButton("Select All")
        self.selAllButton.clicked.connect(
            lambda: self.set_all_checkboxes(True)
        )
        self.layoutButon.addWidget(self.selAllButton)

        self.deselAllButton = Qt.QPushButton("Deselect All")
        self.deselAllButton.clicked.connect(
            lambda: self.set_all_checkboxes(False)
        )
        self.layoutButon.addWidget(self.deselAllButton)

        self.runButton = Qt.QPushButton("Update")
        self.runButton.clicked.connect(
            lambda:
                self.run_update(
                    self.QTabLayers.widget(self.QTabLayers.currentIndex())
                )
        )
        self.layoutButon.addWidget(self.runButton)
        
        self.updateAllButton = Qt.QPushButton("Update All")
        self.updateAllButton.clicked.connect(self.update_all)
        self.layoutButon.addWidget(self.updateAllButton)
            
        # --------------------layout des options avancees--------------------
        
        # Enable recursion mode only if Usd Version allow it (24.03)
        # commit: https://github.com/PixarAnimationStudios/OpenUSD/commit/830fe92f96e730b2deae70e9e476770ea8265bbb
        _, major_version, minor_version = Usd.GetVersion()
        
        self.layoutAdvOptions = Qt.QHBoxLayout()
        mainLayout.addLayout(self.layoutAdvOptions)
        
        if major_version >= 24:
            self.checkboxRecursion = Qt.QCheckBox('Enable Recursion')
            self.checkboxRecursion.setChecked(False)
            self.checkboxRecursion.stateChanged.connect(
                self.onChangedRecursive
            )
            self.layoutAdvOptions.addWidget(self.checkboxRecursion, 50)
        else: # pragma: no cover
            self.warningRecursion = Qt.QLabel(
                'Recursion only available for USD version higher '
                f'than 24.03 (current {major_version}.{minor_version})'
            )
            self.layoutAdvOptions.addWidget(self.warningRecursion, 50)
        
        if _DEBUG_MODE:
            self.debugbutton = Qt.QPushButton("DEBUG")
            self.debugbutton.clicked.connect(self.debug)
            self.layoutAdvOptions.addWidget(self.debugbutton)
        
        saveModeLayout = Qt.QVBoxLayout()

        self.saveModeNew = Qt.QRadioButton(text='Create New Version')
        self.saveModeNew.setChecked(True)
        self.saveModeNew.toggled.connect(self.setSaveMode)
        saveModeLayout.addWidget(self.saveModeNew)

        self.saveModeOverwrite = Qt.QRadioButton(text='Overwrite Version')
        self.saveModeOverwrite.toggled.connect(self.setSaveMode)
        saveModeLayout.addWidget(self.saveModeOverwrite)
        
        self.layoutAdvOptions.addLayout(saveModeLayout, 50)
        
        self.parseButton = Qt.QPushButton('Parse Dependencies')
        self.parseButton.clicked.connect(
                self.reload_dependencies
        )
        self.layoutAdvOptions.addWidget(self.parseButton, 50)

        # -----------------box de log après le run du script-----------------
        self.logBox = Qt.QTextEdit()
        self.logBox.setReadOnly(True)
        self.logBox.setFixedHeight(250)
        mainLayout.addWidget(self.logBox)

        self.find_USD_file_to_update()


    def debug(self): # pragma: no cover
        if _DEBUG_MODE:
            logger.debug('Enable debug mode')
            debug_log_path = os.path.join(LOG_DIRECTORY, 'debug.log')
            debug.debug(log_file=debug_log_path)
            debug.debugpy.breakpoint()
            pass
        
        
    def setArContext(self, ar_context: list[str]):
        self._usd_parser.ar_context = ar_context


    def isUpdate(self): # pragma: no cover
        return self._usd_parser.isUpdate()


    def getLayer(self, index: int) -> Sdf.Layer | None:
        tab: AssetListWidget = self.QTabLayers.widget(index)
        if not tab:
            return
        return tab.layer
    
    
    def getExternalApp(self):
        vscode_path = "C:/Program Files/Microsoft VS Code/Code.exe"
        if os.path.exists(vscode_path):
            return vscode_path 
        return "notepad"
    
    
    def openInExplorer(self, index_layer: int):
        layer = self.getLayer(index_layer)
        directory_path = Path(layer.realPath).parent.as_uri()
        command = ['explorer.exe', directory_path]
        try:
            subprocess.run(command, capture_output=True)
        except Exception as e:
            self.log(
                f"Could not open {directory_path} in explorer\n{e}",
                severity=logging.ERROR
            )
            

    def openExternal(self, index_layer: int):
        layer = self.getLayer(index_layer)
        file_path = Path(layer.realPath).as_posix()
        external_app = self.getExternalApp()
        command = [external_app, file_path]
        try:
            subprocess.run(command, check=True, capture_output=True)        
        except Exception as e:
            appname = os.path.splitext(os.path.basename(external_app))[0]
            self.log(
                f"Could not open {file_path} in {appname}\n{e}",
                severity=logging.ERROR
            )            


    def removeLayerAtIndex(self, index_layer: int):
        layer = self.getLayer(index_layer)
        if index_layer is None:
            return
        try:
            self._layers.remove(layer)
        except ValueError as e:
            logger.warning(e)
        try:
            del self._assetsToUpdate[layer.identifier]
        except KeyError as e:
            logger.warning(e)
        asset_list: AssetListWidget = self.QTabLayers.widget(index_layer)
        index = self.layerList.indexFromItem(asset_list.layer_item)
        self.layerList.takeItem(index.row())
        self.QTabLayers.removeTab(index_layer)


    def removeSelectedLayer(self, layer: Sdf.Layer):
        index_layer = self.getTabLayer(layer)
        self.removeLayerAtIndex(index_layer)


    def onSelectedLayerChanged(self):
        selectedItem = self.layerList.selectedItems()
        if selectedItem:
            current_index = self.layerList.indexFromItem(selectedItem[0])
            self.QTabLayers.setCurrentIndex(
                current_index.row()
            )
    

    def getCurrentLayer(self) -> Sdf.Layer:
        current_widget: AssetListWidget = self.QTabLayers.currentWidget()
        layer = current_widget.layer
        return layer
    
    
    def getTabLayer(self, layer: Sdf.Layer) -> int | None:
        for index in range(self.QTabLayers.count()):
            tab: AssetListWidget = self.QTabLayers.widget(index)
            if hasattr(tab, "layer"):
                if layer == tab.layer:
                    return index
        return None
    
            
    def setUpdatedLayer(self, layer: Sdf.Layer, on: bool):
            layer_index = self.getTabLayer(layer)
            if layer is None:
                return
            asset_list: AssetListWidget = self.QTabLayers.widget(layer_index)
            widget:LayerWidget = self.layerList.itemWidget(
                asset_list.layer_item)
            widget.setUpdated(on)


    def onChangedRecursive(self):
        self._enable_recursion = self.checkboxRecursion.isChecked()
        

    def clearInterfaceData(self):
        self._pathFiles.clear()
        self._layers.clear()
        self._assetsToUpdate.clear()
        
        self.layerList.clear()
        self.QTabLayers.clear()
        self.logBox.clear()
        self.USDFileNeedUpdate.clear()


    def log(self, text, severity=logging.INFO):
        if severity == logging.WARNING:
            self.logBox.append(f"{self.SeverityFlag.WARNING.value} {text}")
        elif severity == logging.ERROR:
            self.logBox.append(f"{self.SeverityFlag.ERROR.value} {text}")
        else:
            self.logBox.append(text)
        logger.log(severity, text)
    
    
    def set_all_checkboxes(self, value: bool):
        current_tab_index = self.getTabLayer(self.getCurrentLayer())
        asset_list = self.QTabLayers.widget(current_tab_index)
        
        checkboxes = asset_list.findChildren(Qt.QCheckBox)
        for checkbox in checkboxes:
            checkbox.setChecked(value)
    
    
    def setSaveMode(self):
        if self.saveModeNew.isChecked():
            self.update_mode = usd_parser.USDParser.UpdateMode.NEW_VERSION
        else:
            self.update_mode = usd_parser.USDParser.UpdateMode.OVERWRITE
    
    
    def browse_file(self):
        #trouver le path 
        currentText = self.USDFileNeedUpdate.text()
        if currentText:
            choosePlace = os.path.dirname(currentText)
        else:
            choosePlace = "c:/"
        
        path, _ = Qt.QFileDialog.getOpenFileName(
            self,
            "Select USD File",
            choosePlace,
            "USD Files (*.usd *.usda *.usdc)"
        )
        self.default_parse(path)


    def reload_dependencies(self):
        current_layer = self.getCurrentLayer()
        self.load_USD(current_layer.identifier)
        

    #----find layer on maya/houdini/prism----
    def default_parse(self, pathfile: str):
        try:
            self._pathFiles = self.find_lastest_layout_usd(pathfile)
            self._hiddenDependencies = self.getHiddenDependencies(
                self._pathFiles
            )
            for path in self._pathFiles:
                logger.debug(f'Start parsing of {path}')
                if path:
                    self.log(f"Default file: {path}")
                    self.load_USD(path)
            for path in self._hiddenDependencies:
                if path:
                    self.load_USD(path, True)
        except Exception as e: # pragma: no cover
            self.log(
                f"Error loading USD file: {e}",
                severity=logging.WARNING
            )
    
    
    def ask_latest(self, pathfile: str):
        versions = self.check_latest_container(pathfile)
        if versions is None:
            return pathfile
        current_version, last_version = versions
        if last_version != current_version:
            last_path = usd_parser.VERSION_PATTERN_COMPILED.sub(last_version, pathfile)
            ask_latest = Qt.QMessageBox(parent=self)
            ask_latest.setText(
                "A newer USD container is available :\n - "
                f"{current_version} => {last_version}\n"
            )
            ask_latest.setInformativeText(
                "Would you like to update your layer from the latest version ?",
            )
            ask_latest.setStandardButtons(
                Qt.QMessageBox.StandardButton.Apply
                | Qt.QMessageBox.StandardButton.Cancel
            )
            ask_latest.setDefaultButton(
                Qt.QMessageBox.StandardButton.Cancel
            )
            ask_latest.setWindowTitle("USD Container Warning")
            ask_latest.setWindowModality(Qtc.Qt.WindowModality.WindowModal)
            should_update = ask_latest.exec_()
            if should_update == Qt.QMessageBox.StandardButton.Apply:
                return last_path
        return pathfile
    
    
    def check_latest_container(self, pathfile: str):
        expanded_path = os.path.expandvars(pathfile)
        last_version = self._usd_parser.get_last_version(expanded_path)
        if last_version is None:
            return
        layer_type = self.getLayerType(expanded_path)
        if layer_type != AssetListWidget.LayerType.CONTAINER:
            return
        current_version = usd_parser.VERSION_PATTERN_COMPILED.search(pathfile).group(0)
        return current_version, last_version
    
    
    def find_USD_file_to_update(self):
        self.clearInterfaceData()
        current_mode = self.targetMode.currentIndex()

        if current_mode == 0:
            if self.openType == "houdini": # pragma: no cover
                usd_paths = self.get_path_from_houdini_node()
                for path in usd_paths:
                    self.default_parse(path)
            else:
                self.default_parse(self.pathPrism)
        elif current_mode == 1: # pragma: no cover
            if self.openType == "maya":
                self.load_maya_work_layer()
            elif self.openType == "prism":
                self.log(
                    "Impossible d'effectuer cette opération dans prism."
                    " Valable uniquement dans maya et houdini",
                    severity=logging.ERROR
                )
        else: # pragma: no cover
            self.log(
                "Invalid update mode (How ???)",
                severity=logging.ERROR
            )


    def getLayerType(self, layer_path: str) -> AssetListWidget.LayerType:
        layer_path_p = Path(layer_path)
        try:
            production_index = layer_path_p.parts.index(_PRODUCTION_IDENTIFIER)
        except ValueError:
            return AssetListWidget.LayerType.CONTAINER
        layer_directory = layer_path_p.parts[production_index+5]
        if layer_directory == 'USD':
            return AssetListWidget.LayerType.CONTAINER
        layer_directory = layer_directory.split('_')
        sublayer = layer_directory[-1]
        if sublayer == 'master':
            return AssetListWidget.LayerType.DEPARTEMENT
        else:
            return AssetListWidget.LayerType.SUBLAYER
        

    def getParentLayer(self, layer_path: str) -> str:
        layer_path_p = Path(layer_path)
        try:
            production_index = layer_path_p.parts.index(_PRODUCTION_IDENTIFIER)
        except ValueError:
            return None
        layer_directory = layer_path_p.parts[production_index+5]
        if layer_directory == 'USD':
            return None
        else:
            layer_directory = layer_directory.split('_')
            departement = layer_directory[-2]
            sublayer = layer_directory[-1]
            if sublayer == 'master':
                layer_directory = 'USD'
            else:
                layer_directory = f'_layer_{departement}_master'
            parts = list(layer_path_p.parts)
            parts[production_index+5] = layer_directory
            layer_pattern = Path(*parts[:production_index+6])
            latest = None
            for layers_version in os.scandir(layer_pattern.as_posix()):
                if not layers_version.is_dir():
                    continue
                for f in os.scandir(layers_version.path):
                    name = f.name
                    if not name.endswith(usd_parser.USD_EXTS):
                        continue
                    if latest is None or name > latest[0]:
                        latest = (name, f.path)
            if latest is None:
                return None
            return Path(latest[1]).as_posix()


    def load_exports_names(self):
        default_layouts = [
            "_layer_layout_layoutMaya",
            "_layer_lay_main",
            "_layer_mod_mayaLayout"
        ]
        try:
            with open(EXPORT_PATHS_JSON, 'r+') as maya_layout:
                json_data = json.load(maya_layout)
            return json_data
        except Exception as e: # pragma: no cover
            logger.warning(e)
            return {"layout": default_layouts}
    
    
    def get_path_from_houdini_node(self): # pragma: no cover
        nodes: list[hou.LopNode] = hou.selectedNodes()
        if not nodes:
            self.log("No node selected, could not parse usd export path")
            return []
        self._houdini_nodes = nodes
        usd_paths = []
        for node in nodes:
            if node.type().name() == 'prism::LOP_Import::1.0':
                try:
                    source_parm: hou.Parm = node.parm('filepath')
                    source_path = source_parm.unexpandedString()
                    pathfile = self.ask_latest(source_path)
                    source_parm.set(pathfile)
                    usd_paths.append(source_parm.eval())
                except Exception as e:
                    logger.warning(
                        'Could not find file path in'
                        f' parm of node {node.name()}'
                    )
            else:
                if not hasattr(node, "stage"):
                    continue
                stage: Usd.Stage = node.stage()
                try:
                    prism_metadata = stage.GetPrimAtPath('/prism_metadata')
                    source_attribute = prism_metadata.GetAttribute('prism_sources')
                    source_path = source_attribute.Get()[0]
                    usd_paths.append(source_path)
                except Exception as e:
                    self.log(
                        f"Could not found usd export from node {node.name()}",
                        severity=logging.WARNING
                    )
        return usd_paths        


    def update_houdini_node_paths(self):
        """
        Update selected Houdini nodes path
        if a newer version is available.
        """
        nodes = self._houdini_nodes
        for node in nodes:
            if node.type().name() == 'prism::LOP_Import::1.0':
                try:
                    source_parm: hou.Parm = node.parm('filepath')
                    source_path = source_parm.eval()
                    raw_path = source_parm.unexpandedString()
                    last_version = self._usd_parser.get_last_version(source_path)
                    if last_version is None:
                        continue
                    last_path = usd_parser.VERSION_PATTERN_COMPILED.sub(
                        last_version,
                        raw_path
                    )
                    if os.path.exists(os.path.expandvars(last_path)):
                        source_parm.set(last_path)
                except Exception as e:
                    logger.warning(
                        'Could not find file path in'
                        f' parm of node {node.name()}'
                    )


    #---trouve le dernier publish de la scene maya en question---
    def find_lastest_layout_usd(self, filepath: str) -> list[str]:
        exports_path = []
        if self.openType == "maya": # pragma: no cover
            logger.debug("---------Fetching current Maya scene path---------")
            scene_path = cmds.file(q=True, sceneName=True)
        elif self.openType == "houdini": # pragma: no cover
            logger.debug("---------Fetching current Maya scene path---------")
            scene_path = filepath
            if not scene_path:
                if os.path.exists(str(filepath)):
                    scene_path = filepath
                else:
                    logger.debug(
                        'Did not found path from'
                        ' node fallback to scenepath'
                    )
                    return []
            exports_path.append(Path(scene_path).as_posix())
        elif self.openType == "prism":
            logger.debug("---------------Get file from Prism---------------")
            # le chemin que prism va donner 
            if not filepath:
                return []
            scene_path = filepath
            exports_path.append(Path(scene_path).as_posix())
        else:
            self.log(
                f"Error loading USD file : pas de file scene donné",
                severity=logging.WARNING
            )
            return []
        
        logger.debug("Extracting project root, sequence, and shot...")
        scene_path = Path(scene_path)
        if len(scene_path.parts) < 6:
            logger.debug(
                "Scene path is too short to extract project structure."
            )
            return []

        # I:/Production/03_Production/Shots
        try:
            production_index = scene_path.parts.index(_PRODUCTION_IDENTIFIER)
        except ValueError:
            self.log(
                f"File not in prism project:\n - \"{scene_path.as_posix()}\"",
                severity=logging.WARNING
            )
            return exports_path
        project_root = Path(*scene_path.parts[:production_index+2])
        sequence = scene_path.parts[production_index+2]
        shot = scene_path.parts[production_index+3]

        logger.debug(f"Extracted project root: {project_root}")
        logger.debug(f"Extracted sequence: {sequence}, shot: {shot}")

        export_directory = project_root / sequence / shot / "Export"
        exports_patterns = self.load_exports_names()
        
        for key in exports_patterns:
            logger.debug(f"Start parsing {key} exports")
            export_names = exports_patterns[key]
            for export_name in export_names:
                logger.debug(f" - export name = {export_name}")
                usd_name = f"{sequence}-{shot}_{export_name}_v*.usd*"
                glob_pattern = (
                    export_directory/export_name/"v*"/usd_name
                ).as_posix()
                logger.debug(f"Glob with '{glob_pattern}'")
                glob_versions = glob.glob(glob_pattern)
                versions = []
                for version in glob_versions:
                    if not '.bak' in version:
                        versions.append(version)
                if not versions:
                    continue
                versions.sort()
                latest = versions[-1]
                if os.path.exists(latest):
                    logger.debug(f"Found {latest}")
                    exports_path.append(Path(latest).as_posix())
                    break
        return exports_path
    
    
    def getHiddenDependencies(self, exports_path):
        hidden_depencencies = []
        for path in exports_path:
            parent = self.getParentLayer(path)
            if parent is not None:
                if (not parent in exports_path
                    and not parent in hidden_depencencies):
                    hidden_depencencies.append(parent) 
                grand_parent = self.getParentLayer(parent)
                if (grand_parent is not None
                    and not grand_parent in exports_path
                    and not grand_parent in hidden_depencencies):
                    hidden_depencencies.append(grand_parent)
        return hidden_depencencies


    # ----------------------------script for Maya----------------------------
    def load_maya_work_layer(self): # pragma: no cover
        stage = self.get_selected_stageMaya()
        if not stage:
            self.log(
                "No valid USD stage selected in Maya.",
                severity=logging.ERROR
            )
            return

        layer = stage.GetEditTarget().GetLayer()
        content = layer.ExportToString()
        self._usd_parser.parse_payloads(content)


    def get_selected_stageMaya(self) -> Usd.Stage: # pragma: no cover
        """
        Return the selected USD stage if it's a mayaUsdProxyShape,
        or fallback to the first mayaUsdProxyShape in the scene.
        """
        maya_stage_node = cmds.ls(selection=True, l=True)

        if maya_stage_node:
            selected_node = maya_stage_node[0]
            node_type = cmds.nodeType(selected_node)
            logger.debug(f"Selected node: {selected_node}, type: {node_type}")
            
            if node_type != "mayaUsdProxyShape":
                logger.debug("Selected node is not of type mayaUsdProxyShape."
                             " Searching for a valid one...")
                selected_node = None
            else:
                logger.debug("Selected node is a valid mayaUsdProxyShape.")
        else:
            logger.debug("No selection found.")
            selected_node = None

        if not selected_node:
            proxy_shapes = cmds.ls(type="mayaUsdProxyShape", l=True)
            if not proxy_shapes:
                cmds.confirmDialog(
                    title='No stage found',
                    message='No mayaUsdProxyShape found in the scene',
                    button=['OK'],
                    defaultButton='OK'
                )
                cmds.warning('No mayaUsdProxyShape found in the scene')
                logger.warning("No mayaUsdProxyShape found in the scene")
                return None
            selected_node = proxy_shapes[0]
            logger.debug(f"Using first mayaUsdProxyShape: {selected_node}")

        asset_stage = mayaUsd.ufe.getStage(selected_node)
        if asset_stage is None:
            cmds.confirmDialog(
                title='Invalid stage',
                message='Could not get stage from the selected node',
                button=['OK'],
                defaultButton='OK'
            )
            cmds.warning('Could not get stage from the selected node')
            logger.warning("Could not get stage from the selected node")
            return None

        logger.debug("Successfully retrieved stage.")
        return asset_stage
    

    # --------------------------------for all--------------------------------
    def load_USD(self, usd_path: str, hidden=False):
        try:
            layer: Sdf.Layer = Sdf.Layer.FindOrOpen(usd_path)
        except Exception as e:
            self.log(
                f"Error loading layer from file: {e}",
                severity=logging.WARNING
            )
            return
        if layer:
            layer.Reload(True)
            self._usd_parser.parse(
                layer=layer,
                enable_recursion=self._enable_recursion,
                check_mode=self.check_update_only
            )
            assets_to_update = self._usd_parser.get_assets_to_update()
            
            self._assetsToUpdate[layer.identifier] = assets_to_update
            
            asset_list = self.build_item_list(assets_to_update)
            asset_list.layer_type = self.getLayerType(usd_path)
            dependance = self.getParentLayer(usd_path)
            asset_list.dependance = dependance
            asset_list.can_be_updated = not self._enable_recursion
            if layer in self._layers:
                tab = self.getTabLayer(layer)
                if tab is None:
                    self.log(
                        "Could not find an already existing"
                        f" tab for {layer.identifier}",
                        severity=logging.ERROR
                    )
                    return
                
                tab_widget: AssetListWidget = self.QTabLayers.widget(tab)
                asset_list.layer = layer
                asset_list.layer_item = tab_widget.layer_item
                currentTab = self.QTabLayers.currentIndex()
                self.QTabLayers.removeTab(tab)
                self.QTabLayers.insertTab(tab, asset_list, f"Layer {tab+1}")
                self.QTabLayers.setCurrentIndex(currentTab)
            else:
                self._layers.append(layer)
                self.add_layer_tab(layer, asset_list, hidden)
            is_updated = not len(self._assetsToUpdate[layer.identifier])
            self.setUpdatedLayer(layer, is_updated)
            asset_list.isUpdate = is_updated
            return layer
            

    def add_item_list(self, listwidget:AssetListWidget, item: AssetItem):
        
        item_widget = Qt.QWidget()
        item_hbox = Qt.QHBoxLayout()
        item_hbox.setContentsMargins(0, 0, 0, 0)
        item_widget.setLayout(item_hbox)
        
        if item.from_version and item.to_version:
            text = (
                f"<em>{item.original_path}</em><br>"
                "➡ <b><span style='color: red;'>"
                f"v{item.from_version:03d}</span></b> "
                "→ <b><span style='color: green;'>"
                f"v{item.to_version:03d}</span></b>"
            )
        else:
            text = f"{item.original_path}\n➡ make relative"
        item_label = Qt.QLabel(text)
            
        checkbox = Qt.QCheckBox()
        checkbox.setObjectName('item_checkbox')
        if item.can_be_updated:
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(
                lambda state, i=item: 
                    setattr(i, 'should_be_updated', state == Qtc.Qt.Checked)
            )
        else:
            item.should_be_updated = False
            checkbox.setChecked(False)
            checkbox.setCheckable(False)
            
        item_hbox.addWidget(checkbox, 1)
        item_hbox.addWidget(item_label, 99)

        list_item = Qt.QListWidgetItem()
        listwidget.addItem(list_item)
        listwidget.setItemWidget(list_item, item_widget)
        list_item.setSizeHint(item_widget.sizeHint())
        

    def add_item_text(self, listwidget:AssetListWidget, text):
        layer_item = Qt.QListWidgetItem()
        label = Qt.QLabel(text=text)
        label.setContentsMargins(10, 0, 5, 0)
        listwidget.addItem(layer_item)
        listwidget.setItemWidget(layer_item, label)
        layer_item.setSizeHint(label.sizeHint() + Qtc.QSize(0, 5))
     
     
    def onItemClicked(self, item: Qt.QListWidgetItem):
        try:
            listwidget = item.listWidget()
            item_widget = listwidget.itemWidget(item)
            if item_widget.metaObject().className() == 'QWidget':
                checkbox: Qt.QCheckBox = item_widget.findChild(
                    Qt.QCheckBox,
                    'item_checkbox'
                )
                if checkbox.isCheckable():
                    checkbox.setChecked(not checkbox.isChecked())
        except Exception as e:
            logger.warning(e)
            return    


    def build_item_list(self, assetsToUpdate: list[AssetItem]):
        
        asset_list = AssetListWidget()
        # add callback on click to check/uncheck items
        asset_list.itemClicked.connect(self.onItemClicked)
        
        for i, item in enumerate(assetsToUpdate):            
            # add layer header if current reference is in a new layer
            if i == 0:
                previous_layer = assetsToUpdate[0].layer_path
                self.add_item_text(
                    asset_list,
                    f"Current layer : <b>{previous_layer}</b>"
                )
            elif item.layer_path != previous_layer:
                previous_layer = item.layer_path
                self.add_item_text(
                    asset_list,
                    f"Current layer : <b>{previous_layer}</b>"
                )
            # add item to tree
            self.add_item_list(asset_list, item)
                    
        return asset_list
        
            
    def add_layer_tab(
            self,
            layer: Sdf.Layer,
            asset_list: AssetListWidget,
            hidden: bool=False): 
        
        asset_list.layer = layer
        tab_number = self.QTabLayers.count()+1
        self.QTabLayers.addTab(asset_list, f"Layer {tab_number}")
        layer_path = Path(layer.identifier)
        if len(layer_path.parts) < 3:
            layer_text = layer_path.parts[-1]
        else:
            layer_text = (
                f"<b>{layer_path.parts[-3]}</b>"
                f"<br> - {layer_path.parts[-1]}"
            )   
        layer_widget = LayerWidget(layer_text)
        layer_item = Qt.QListWidgetItem()
        asset_list.layer_item = layer_item
        self.layerList.addItem(layer_item)
        layer_item.setHidden(hidden)
        self.layerList.setItemWidget(layer_item, layer_widget)
        layer_item.setSizeHint(layer_widget.sizeHint())

    
    def update_all(self):
        self.logBox.clear()
        
        tabs = [self.QTabLayers.widget(tab_idx) 
                for tab_idx in range(self.QTabLayers.count())]
        for tab in tabs:
            self.run_update(
                tab,
                clear_log=False,
                check_nodes=False
            )
            
        current_mode = self.targetMode.currentIndex()
        if current_mode == 0:
            if self.openType == 'houdini':
                self.update_houdini_node_paths()
                usd_check.checkEveryNodes()
            
    
    def run_update(self, tab, clear_log=True, check_nodes=True, clean_tabs=True):
        if clear_log:
            self.logBox.clear()
            
        if not isinstance(tab, AssetListWidget):
            self.log("Invalid tab type", severity=logging.ERROR)
            return
            
        current_layer: Sdf.Layer = tab.layer
        layer_identifier = current_layer.identifier
        assets_to_update = self._assetsToUpdate[layer_identifier]
        
        if not tab.can_be_updated:
            self.log(
                "Cannot update recursive found dependencies",
                severity=logging.WARNING
            )
            return
        if tab.isUpdate or not (assets_to_update):
            self.log(f"Already updated: {layer_identifier}")
            return
        
        self._usd_parser.set_assets_to_update(assets_to_update)
        new_layer = self._usd_parser.update_layer(
            current_layer,
            self.update_mode,
            self.pcore)
        layer_widget = self.layerList.itemWidget(tab.layer_item)
        is_hidden = layer_widget.isHidden()
        
        if self.update_mode == usd_parser.USDParser.UpdateMode.NEW_VERSION:
            if new_layer is None:
                self.log(
                    "Could not increment version "
                    f"for : {layer_identifier}",
                    severity=logging.ERROR
                )
                return
            else:
                layer_identifier = new_layer
            dep = tab.dependance
            child_identifier = layer_identifier
            while dep is not None:
                # recursively refresh each old dep in UI
                current_deps_identifier = dep
                new_deps_identifier = self.getParentLayer(child_identifier)
                dep_layer = self.load_USD(current_deps_identifier)
                dep_index = self.getTabLayer(dep_layer)
                dep_tab: AssetListWidget = self.QTabLayers.widget(dep_index)
                dep = dep_tab.dependance
                self.removeSelectedLayer(dep_layer)
                self.load_USD(new_deps_identifier)
            if clean_tabs:
                self.removeSelectedLayer(current_layer)
            
        current_mode = self.targetMode.currentIndex()
        if current_mode == 0:
            if check_nodes and self.openType == 'houdini': # pragma: no cover
                self.update_houdini_node_paths()
                usd_check.checkEveryNodes()
            self.load_USD(layer_identifier, is_hidden)
        elif current_mode == 1: # pragma: no cover
            if self.openType == "maya":
                self.load_maya_work_layer()
            else:
                self.log(
                    "Impossible défectuer cette option dans prism. "
                    "Valable uniquement dans Maya",
                    severity=logging.ERROR
                )
        else: # pragma: no cover
            self.log("Invalid update mode (How ???)", severity=logging.ERROR)
            return


def startUpdateAssetsUSD(
        openType,
        tmpfile=None,
        prism_core=None,
        ar_context=None):    
    instance = None
    if not Qt.QApplication.instance(): # pragma: no cover
        app_start = True 
        app = Qt.QApplication(sys.argv)
    else:
        app_start = False
        if openType == "maya": # pragma: no cover
            main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
            instance = wrapInstance(int(main_window_ptr), Qt.QWidget)

        elif openType == "houdini": # pragma: no cover
            instance = hou.qt.mainWindow()
        
        else:
            instance = None
        app = Qt.QApplication.instance()
    
    my_window = MainInterface(
        openType=openType,
        pathPrism=tmpfile,
        pcore=prism_core,
        ar_context=ar_context,
        parent=instance
    )
    my_window.show()
    if app_start:
        sys.exit(app.exec_())