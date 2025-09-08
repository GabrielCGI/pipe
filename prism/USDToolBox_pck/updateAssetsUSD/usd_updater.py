
# standard deps
from enum import Enum
from datetime import datetime
from pathlib import Path
import subprocess
import logging
import socket
import shutil
import glob
import json
import sys
import os

# packages deps
from . import usd_parser
from .assetitem import AssetItem
from . import loggingsetup
from . import usd_check

# TODO DELETE DEBUG PACKAGE
DEBUG_MODE = False and socket.gethostname() == 'FOX-04'
if DEBUG_MODE:
    from . import debug

# logger setups using logconfig.json parameters
LOG_DIRECTORY = 'R:/logs/update_usd_logs'
LOG_CONFIG = os.path.join(os.path.dirname(__file__), "config/logconfig.json")

#---------------------------- pb ----------------------------
if not socket.gethostname() == 'ROLL4':
    is_log_setup = loggingsetup.setup_log(
        logName='update_usd',
        logConfigPath=LOG_CONFIG,
        logDirectory=LOG_DIRECTORY,
        with_time=False
    )
else:
    is_log_setup = False

#---------------------------- pb ----------------------------

if not is_log_setup:
    if not socket.gethostname() == 'ROLL4':
        with open(r"R:/logs/update_usd_logs/error_log.txt", 'w') as error_log:
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
    
    if not found:
        return False
    
    if pyside_path not in sys.path:
        sys.path.append(pyside_path)
    if path not in sys.path:
        sys.path.append(path)
    return True

# Import qt with qtpy of prism to match any version of qt found
# https://pypi.org/project/QtPy/
if import_qtpy():
    from qtpy import QtWidgets as Qt
    from qtpy import QtCore as Qtc
    from qtpy import QtGui as Qtg
else:
    logger.error(f'qtpy not found in C:/ILLOGIC_APP/Prism', file=sys.stderr)
    sys.exit(1)
    

#import USD libs
try:
    from pxr import Sdf, Usd
except:
    pass

#import for maya 
try:
    from maya import OpenMayaUI, cmds # type: ignore
    import mayaUsd # type: ignore
    from shiboken6 import wrapInstance
except:
    pass

#import for houdini 
try:
    import hou # type: ignore
except:
    pass

SCRIPT_DIRECTORY = Path(__file__).parent
EXPORT_PATHS_JSON = SCRIPT_DIRECTORY / "config/export_paths.json"

class AssetListWidget(Qt.QListWidget):
    
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layer: Sdf.Layer = None
        self.can_be_updated = True
        

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
        self.main_ui = ui
        
        
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
            lambda: self.main_ui.removeSelectedLayer(current_index)
        )
        menu.addAction(removeAction)
        return menu

    def contextMenuEvent(self, event: Qtg.QContextMenuEvent):
        contextmenu = Qt.QMenu(self)
        contextmenu = self.buildMenu(contextmenu)
        if hasattr(contextmenu, 'exec'):
            contextmenu.exec(event.globalPos())
        elif hasattr(contextmenu, 'exec_'):
            contextmenu.exec_(event.globalPos())

        
class MainInterface(Qt.QMainWindow):
    
    
    def __init__(
            self,
            openType=None,
            pathPrism=None,
            ar_context=None,
            check_update_only=False,
            parent=None):
        
        super(MainInterface, self).__init__(parent)
        self.setWindowTitle("USD Updater 1.0")
        self.resize(1200, 800)
        self.openType = openType
        self.pathPrism = pathPrism

        # layers informations
        self._pathFiles: list[str] = []
        self._layers: list[Sdf.Layer] = []
        self._assetsToUpdate: dict[list[AssetItem]] = {}
        
        # parser informations
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

        # -----------------mode Update Worklayer ou USDA file-----------------
        self.updateMode = Qt.QComboBox()
        if self.openType == 'maya':
            updateModeItem = [
                "Update from USDA file",
                "Update Current Work Layer"
            ]
        else:
            updateModeItem = [
                "Update from USDA file"
            ]
        self.updateMode.addItems(updateModeItem)
        
        if self.openType == 'maya':
            self.updateMode.setCurrentIndex(1)
        else:
            self.updateMode.setCurrentIndex(0)
            
        self.updateMode.currentIndexChanged.connect(
            self.find_USD_file_to_update
        )
        mainLayout.addWidget(self.updateMode)
        
        # -----------choisir quelle layer d'USD choisir à modiffier-----------
        file_layout = Qt.QHBoxLayout()

        self.USDFileNeedUpdate = Qt.QLineEdit()
        file_layout.addWidget(self.USDFileNeedUpdate)
        
        self.filePathBtn = Qt.QPushButton("Add Layer...")
        self.filePathBtn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.filePathBtn)
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
        
        self.selAllBtm = Qt.QPushButton("Select All")
        self.selAllBtm.clicked.connect(
            lambda: self.set_all_checkboxes(True)
        )
        self.layoutButon.addWidget(self.selAllBtm)

        self.deselAllBtm = Qt.QPushButton("Deselect All")
        self.deselAllBtm.clicked.connect(
            lambda: self.set_all_checkboxes(False)
        )
        self.layoutButon.addWidget(self.deselAllBtm)

        self.runBtm = Qt.QPushButton("Update")
        self.runBtm.clicked.connect(self.run_update)
        self.layoutButon.addWidget(self.runBtm)
        
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
        else:
            self.warningRecursion = Qt.QLabel(
                'Recursion only available for USD version higher '
                f'than 24.03 (current {major_version}.{minor_version})'
            )
            self.layoutAdvOptions.addWidget(self.warningRecursion, 50)
        
        if DEBUG_MODE:
            self.debugbutton = Qt.QPushButton("DEBUG")
            self.debugbutton.clicked.connect(self.debug)
            self.layoutAdvOptions.addWidget(self.debugbutton)
        
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


    def debug(self):
        if DEBUG_MODE:
            logger.debug('Enter debug mode')
            debug.debug()
            debug.debugpy.breakpoint()
            pass
        
        
    def setArContext(self, ar_context: list[str]):
        self._usd_parser.ar_context = ar_context


    def isUpdate(self):
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
            self.log(f"Could not open {directory_path} in explorer\n{e}")
            logger.error(f"Could not open {directory_path} in explorer\n{e}")
            

    def openExternal(self, index_layer: int):
        layer = self.getLayer(index_layer)
        file_path = Path(layer.realPath).as_posix()
        external_app = self.getExternalApp()
        command = [external_app, file_path]
        try:
            subprocess.run(command, check=True, capture_output=True)        
        except Exception as e:
            appname = os.path.splitext(os.path.basename(external_app))[0]
            self.log(f"Could not open {file_path} in {appname}\n{e}")
            logger.error(f"Could not open {file_path} in {appname}\n{e}")
            

    def removeSelectedLayer(self, index_layer: int):
        layer = self.getLayer(index_layer)
        if not layer:
            return
        try:
            self._layers.remove(layer)
        except Exception as e:
            logger.warning(e)
        try:
            del self._assetsToUpdate[layer.identifier]
        except Exception as e:
            logger.warning(e)
        self.layerList.takeItem(index_layer)
        self.QTabLayers.removeTab(index_layer)


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
            if not tab:
                continue
            if hasattr(tab, "layer"):
                if layer == tab.layer:
                    return index
        return None
    
            
    def setUpdatedLayer(self, layer: Sdf.Layer, on: bool):
            layer_index = self.getTabLayer(layer)
            if layer is None:
                return
            layer_item = self.layerList.item(layer_index)
            widget:LayerWidget = self.layerList.itemWidget(layer_item) 
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


    def log(self, text):
        # TODO Ameliorer pour prendre en compte les smileys
        # et log selon la severité
        self.logBox.append(text)
    
    
    def set_all_checkboxes(self, value: bool):
        current_tab_index = self.getTabLayer(self.getCurrentLayer())
        asset_list = self.QTabLayers.widget(current_tab_index)
        
        checkboxes = asset_list.findChildren(Qt.QCheckBox)
        for checkbox in checkboxes:
            checkbox.setChecked(value)
    
    
    def browse_file(self):
        #trouver le path 
        currentText = self.USDFileNeedUpdate.text()
        if currentText:
            choosePlace = os.path.dirname(currentText)
        else:
            choosePlace = "c:/"
        
        path, _ = Qt.QFileDialog.getOpenFileName(
            self,
            "Select USDA File",
            choosePlace,
            "USD Files (*.usd *.usda *.usdc)"
        ) # possibiliter de détécter auto le path
        
        if path:
            try:
                layer = Sdf.Layer.FindOrOpen(path)
                if layer in self._layers:
                    return
            except Exception:
                return
            self.USDFileNeedUpdate.setText(path)
            self.load_USD(path)


    def reload_dependencies(self):
        current_layer = self.getCurrentLayer()
        self.load_USD(current_layer.identifier)
        

    #----find layer on maya/houdini/prism----
    def find_USD_file_to_update(self):
        self.clearInterfaceData()
        current_mode = self.updateMode.currentIndex()

        if current_mode == 0:
            try:
                self._pathFiles = self.find_lastest_layout_usda()
                for path in self._pathFiles:
                    logger.debug(f'Start parsing of {path}')
                    if path:
                        self.USDFileNeedUpdate.setText(path)
                        self.log(f"default file: {path}")
                        self.load_USD(path)
            except Exception as e:
                logger.warning(f"Error loading USDA file: {e}")
                self.log(f"⚠️ Error loading USDA file: {e}")
        elif current_mode == 1:
            if self.openType == "maya":
                self.load_maya_work_layer()
            elif self.openType == "prism":
                logger.error(
                    "Impossible d'effectuer cette opération dans prism."
                    " Valable uniquement dans maya et houdini")
                self.log(
                    "⛔ Impossible d'effectuer cette opération dans prism."
                    " Valable uniquement dans maya et houdini")
        else:
            logger.error("Invalid update mode (How ???)")
            self.log("Invalid update mode (How ???)")
            return


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
        except Exception as e:
            logger.warning(e)
            return {"layout": default_layouts}
    
    
    def get_path_from_houdini_node(self):
        nodes = hou.selectedNodes()
        if not nodes:
            self.log("No node selected, could not parse usd export path")
            return ''
        node: hou.LopNode = nodes[0]
        if node.type().name() == 'prism::LOP_Import::1.0':
            try:
                source_parm: hou.Parm = node.parm('filepath')
                source_path = source_parm.eval()
                return source_path
            except Exception as e:
                logger.warning(
                    'Could not find file path in'
                    f' parm of node {node.name()}'
                )
        stage: Usd.Stage = node.stage()
        try:
            prism_metadata = stage.GetPrimAtPath('/prism_metadata')
            source_attribute = prism_metadata.GetAttribute('prism_sources')
            source_path = source_attribute.Get()[0]
            return source_path
        except Exception as e:
            self.log(
                "Warning : Could not found usd"
                f" export from node {node.name()}"
            )
            logger.warning(e)
            return ''
        

    #---trouve le dernier publish de la scene maya en question---
    def find_lastest_layout_usda(self) -> list[str]:
        exports_path = []
        if self.openType == "maya":
            logger.debug("---------Fetching current Maya scene path---------")
            scene_path = cmds.file(q=True, sceneName=True)
        elif self.openType == "houdini":
            logger.debug("---------Fetching current Maya scene path---------")
            scene_path = self.get_path_from_houdini_node()
            if not scene_path:
                if os.path.exists(str(self.pathPrism)):
                    scene_path = self.pathPrism
                else:
                    logger.debug(
                        'Did not found path from'
                        ' node fallback to scenepath'
                    )
                    return []
        elif self.openType == "prism":
            logger.debug("---------------Get file from Prism---------------")
            # le chemin que prism va donner 
            scene_path = self.pathPrism
            exports_path.append(scene_path)
        else:
            logger.warning(
                f"Error loading USDA file : pas de file scene donné"
            )
            self.log(
                f"⚠️ Error loading USDA file : pas de file scene donné"
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
        project_root = Path(*scene_path.parts[:4])
        sequence = scene_path.parts[4]
        shot = scene_path.parts[5]

        logger.debug(f"Extracted project root: {project_root}")
        logger.debug(f"Extracted sequence: {sequence}, shot: {shot}")

        export_directory = project_root / sequence / shot / "Export"
        exports_patterns = self.load_exports_names()
        
        for key in exports_patterns:
            logger.debug("Start parsing {key} exports")
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
                    exports_path.append(latest)
                    break
        return exports_path

    # ----------------------------script for Maya----------------------------
    def load_maya_work_layer(self):
        stage = self.get_selected_stageMaya()
        if not stage:
            self.log("⛔ No valid USD stage selected in Maya.")
            return

        layer = stage.GetEditTarget().GetLayer()
        content = layer.ExportToString()
        self._usd_parser.parse_payloads(content)


    def get_selected_stageMaya(self) -> Usd.Stage:
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
    def load_USD(self, usd_path):
        try:
            layer = Sdf.Layer.FindOrOpen(usd_path)
        except Exception as e:
            logger.warning(f"Error loading layer from file: {e}")
            self.log(f"⚠️ Error loading layer from file: {e}")
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
            asset_list.can_be_updated = not self._enable_recursion
            if layer in self._layers:
                tab = self.getTabLayer(layer)
                if tab is None:
                    logger.error(
                        "Could not find an already existing"
                        f" tab for {layer.identifier}"
                    )
                    self.log(
                        "Could not find an already existing"
                        f" tab for {layer.identifier}"
                    )
                    return
                
                asset_list.layer = layer
                currentTab = self.QTabLayers.currentIndex()
                self.QTabLayers.removeTab(tab)
                self.QTabLayers.insertTab(tab, asset_list, f"Layer {tab+1}")
                self.QTabLayers.setCurrentIndex(currentTab)
            else:
                self._layers.append(layer)
                self.add_layer_tab(layer, asset_list)
            is_updated = not len(self._assetsToUpdate[layer.identifier])
            self.setUpdatedLayer(layer, is_updated)

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
        
            
    def add_layer_tab(self, layer: Sdf.Layer, asset_list: AssetListWidget): 
        
        asset_list.layer = layer
        
        tab_number = self.QTabLayers.count()+1
        self.QTabLayers.addTab(asset_list, f"Layer {tab_number}")
        
        layer_path = Path(layer.realPath)
        if len(layer_path.parts) < 3:
            layer_text = layer_path.parts[-1]
        else:
            layer_text = (
                f"<b>{layer_path.parts[-3]}</b>"
                f"<br> - {layer_path.parts[-1]}"
            )
        layer_widget = LayerWidget(layer_text)
        layer_item = Qt.QListWidgetItem()
        self.layerList.addItem(layer_item)
        self.layerList.setItemWidget(layer_item, layer_widget)
        layer_item.setSizeHint(layer_widget.sizeHint())
        

    def run_update(self):
        
        self.logBox.clear()

        current_layer = self.getCurrentLayer()
        
        current_tab: AssetListWidget = self.QTabLayers.currentWidget()
        if not current_tab.can_be_updated:
            self.log("⛔ Cannot update recursive found dependencies")
            return
        
        # for layer in self._layers:
        # Generate timestamp string: YYYYMMDD_HHMMSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"{current_layer.realPath}.{timestamp}.bak"
        
        shutil.copy2(current_layer.realPath, backup)
        self.log(f"🗂️ Backup created: {backup}")
        
        assets_to_update = self._assetsToUpdate[current_layer.identifier]
        self.log(
            f"Asset items ready: {len(assets_to_update)}"
        )
        self._usd_parser.set_assets_to_update(assets_to_update)
        self._usd_parser.update_layer(current_layer)
        current_layer.Reload(True)
            
        current_mode = self.updateMode.currentIndex()
        if current_mode == 0:
            if self.openType == 'houdini':
                usd_check.checkEveryNodes()
            self.load_USD(current_layer.identifier)
        elif current_mode == 1:
            if self.openType == "maya":
                self.load_maya_work_layer()
            elif self.openType == "prism":
                self.log(
                    "⛔ Impossible défectuer cette option dans prism. "
                    "Valable uniquement dans maya et houdini"
                )
        else:
            logger.error("Invalid update mode (How ???)")
            self.log("Invalid update mode (How ???)")
            return


def startUpdateAssetsUSD(openType, tmpfile=None, ar_context=None):    
    instance = None
    if not Qt.QApplication.instance():
        app_start = True 
        app = Qt.QApplication(sys.argv)
    else:
        app_start = False
        if openType == "maya":
            main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
            instance = wrapInstance(int(main_window_ptr), Qt.QWidget)

        elif openType == "houdini":
            instance = hou.qt.mainWindow()
        
        else:
            instance = None
        app = Qt.QApplication.instance()
    
    my_window = MainInterface(
        openType=openType,
        pathPrism=tmpfile,
        ar_context=ar_context,
        parent=instance
    )
    my_window.show()
    if app_start:
        sys.exit(app.exec_())