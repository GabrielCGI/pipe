
from datetime import datetime
from pathlib import Path

import logging
import shutil
import glob
import json
import sys
import os
import re
    
import socket
# if socket.gethostname() == "RACOON-01":
#     import debug
#     debug.debug()
    # debug.debugpy.breakpoint()
    
# DEBUG ENV - TO DELETE LATER
try:    
    LOG_DIRECTORY = 'R:/logs/update_usd_logs'
    logger = logging.getLogger(__name__)
    # formatter setup
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    # log handler setup
    fileHandler = logging.FileHandler(
        os.path.join(LOG_DIRECTORY, f"log_update_usd.log"),
        mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    # set severity per handlers
    streamHandler.setLevel(logging.DEBUG)
    fileHandler.setLevel(logging.DEBUG)
    # logger setup
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
except Exception as e:
    with open(r"R:/logs/update_usd_logs/error_log.txt", 'w') as error_log:
        error_log.write('Error log:\n')
        error_log.write(str(e))

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
else:
    logger.error(f'qtpy not found in C:/ILLOGIC_APP/Prism', file=sys.stderr)
    sys.exit(1)
    

#import USD libs
try:
    from pxr import UsdUtils, Sdf, Ar
except:
    pass

#import for maya 
try:
    from maya import OpenMayaUI, cmds
    import mayaUsd
    from shiboken6 import wrapInstance
except:
    pass

#import for houdini 
try:
    import hou
except:
    pass


MAYA_LAYOUT_JSON = "R:/pipeline/pipe/prism/update_assets_USD/maya_layout.json"


class AssetItem:
    def __init__(self, original_path, updated_path, from_version, to_version):
        self.original_path = original_path
        self.updated_path = updated_path
        self.from_version = from_version
        self.to_version = to_version
        self.should_update = True
        

class mainInterface(Qt.QMainWindow):
    def __init__(self, openType=None, pathPrism=None, parent=None):
        super(mainInterface, self).__init__(parent)
        self.setWindowTitle("USD Payload Updater 1.0")
        self.resize(900, 800)
        self.listAssetsNeedUpdate = []
        self.checkboxWidgetPayload = []
        self.openType = openType
        self.pathFile = None
        self.pathPrism = pathPrism
        
        logger.info('Open USD updater in dev mode')

        #------------------------------------------------ Create interface ------------------------------------------------
        Mainwindow = Qt.QWidget()
        self.setCentralWidget(Mainwindow)
        mainLayout = Qt.QVBoxLayout(Mainwindow)

        #--------------------type Update  Worklayer  ou USDA file--------------------
        self.typeUpdate = Qt.QComboBox()
        if self.openType == 'maya':
            self.typeUpdate.addItems(["Update from USDA file", "Update Current Work Layer"])
        else:
            self.typeUpdate.addItems(["Update from USDA file"])
        if self.openType in ['maya']:
            self.typeUpdate.setCurrentIndex(1)
        else:
            self.typeUpdate.setCurrentIndex(0)
        self.typeUpdate.currentIndexChanged.connect(self.find_USD_File_To_Update)
        mainLayout.addWidget(self.typeUpdate)
        
        #--------------------choisir quelle layer d'USD choisir à modiffier--------------------
        file_layout = Qt.QHBoxLayout()

        self.USDFileNeedUpdate = Qt.QLineEdit()
        file_layout.addWidget(self.USDFileNeedUpdate)
        
        self.filePathBtn = Qt.QPushButton("Browse...")
        self.filePathBtn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.filePathBtn)
        mainLayout.addLayout(file_layout)

        #---------------------------list de tout ce qu'il faut update dans la stack USD---------------------------
        self.QlistUSDNeedUpdate = Qt.QListWidget()
        mainLayout.addWidget(self.QlistUSDNeedUpdate)

        #-----------------------------------------layout des boutton-----------------------------------------
        self.layoutButon = Qt.QHBoxLayout()
        mainLayout.addLayout(self.layoutButon)
        
        self.selAllBtm = Qt.QPushButton("Select All")
        self.selAllBtm.clicked.connect(lambda: self.set_all_checkboxes(True))
        self.layoutButon.addWidget(self.selAllBtm)

        self.deselAllBtm = Qt.QPushButton("Deselect All")
        self.deselAllBtm.clicked.connect(lambda: self.set_all_checkboxes(False))
        self.layoutButon.addWidget(self.deselAllBtm)

        self.runBtm = Qt.QPushButton("Update")
        self.runBtm.clicked.connect(self.run_update)
        self.layoutButon.addWidget(self.runBtm)

        #---------------------------box de log après le run du script---------------------------
        self.logBox = Qt.QTextEdit()
        self.logBox.setReadOnly(True)
        self.logBox.setFixedHeight(250)
        mainLayout.addWidget(self.logBox)

        self.find_USD_File_To_Update()


    def clearInterfaceData(self, pathfile=True):
        self.checkboxWidgetPayload.clear()
        self.listAssetsNeedUpdate.clear()
        self.QlistUSDNeedUpdate.clear()
        self.logBox.clear()
        self.USDFileNeedUpdate.clear()
        self.pathFile = None


    def set_log(self, text):
        self.logBox.append(text)
    
    
    def set_all_checkboxes(self, value):
        for cb in self.checkboxWidgetPayload:
            cb.setChecked(value)
    
    
    def browse_file(self):
        #trouver le path 
        if self.pathFile:
            chosePlaceSplit = self.pathFile.replace("\\", "/")
            chosePlaceSplit = chosePlaceSplit.split("/")[:-1]
            chosePlace = "/".join(chosePlaceSplit)
        else:
            chosePlace = "c:/"
        
        path, _ = Qt.QFileDialog.getOpenFileName(self, "Select USDA File", chosePlace, "USD Files (*.usda, *.usdc)") # possibiliter de détécter auto le path
        if path:
            self.clearInterfaceData()
            self.USDFileNeedUpdate.setText(path)
            self.pathFile = path
            self.load_USD()


    #----find layer on maya/houdini/prism----
    def find_USD_File_To_Update(self):
        self.clearInterfaceData()
        statute = self.typeUpdate.currentIndex()

        if not statute:
            try:
                self.pathFile = self.find_Lastest_layout_usda()
                logger.debug(f'Start parsing of {self.pathFile}')
                if self.pathFile:
                    self.USDFileNeedUpdate.setText(self.pathFile)
                    self.set_log(f"default file: {self.pathFile}")
                    self.load_USD()
            except Exception as e:
                self.set_log(f"⚠️ Error loading USDA file: {e}")
        else:
            if self.openType == "maya":
                self.load_maya_work_layer()
            elif self.openType == "houdini":
                self.load_houdini_work_layer()
            elif self.openType == "prism":
                self.set_log("⛔ Impossible défectuer cette option dans prism. Valable uniquement dans maya et houdini")


    def load_maya_layout_pattern(self):
        default_layouts = [
            "_layer_layout_layoutMaya",
            "_layer_lay_main",
            "_layer_mod_mayaLayout"
        ]
        
        try:
            with open(MAYA_LAYOUT_JSON, 'r+') as maya_layout:
                json_data = json.load(maya_layout)
            maya_layouts = json_data["maya_layouts"]
            return maya_layouts
        except Exception as e:
            logger.warning(e)
            return default_layouts
        

    #---trouve le dernier publish de la scene maya en question---
    def find_Lastest_layout_usda(self):
        if self.openType == "maya":
            logger.debug("-------------Fetching current Maya scene path...")
            scene_path = cmds.file(q=True, sceneName=True)
        elif self.openType == "houdini":
            scene_path = hou.hipFile.path()

        elif self.openType == "prism":
            logger.debug("--------------------------- file prism")
            return self.pathPrism.replace("\\", "/") # le passe que prism va donner 
        else:
            logger.warning(f"Error loading USDA file : pas de file scene donné")
            self.set_log(f"⚠️ Error loading USDA file : pas de file scene donné")
            return None
        
        logger.debug("Extracting project root, sequence, and shot...")
        parts = scene_path.split("/")
        if len(parts) < 6:
            logger.debug("Scene path is too short to extract project structure.")
            return None

        project_root = "/".join(parts[:4])  # I:/intermarche/03_Production/Shots
        seq = parts[4]
        shot = parts[5]

        logger.debug(f"Extracted project root: {project_root}")
        logger.debug(f"Extracted sequence: {seq}, shot: {shot}")

        logger.debug("Loading Maya layout pattern ...")
        layout_patterns = self.load_maya_layout_pattern()
        logger.debug(f"Patterns:\n{layout_patterns}")
        
        for layout_pattern in layout_patterns:
            layout_dir = os.path.join(project_root, seq, shot, "Export", layout_pattern)
            logger.debug(f"Checking layout directory: {layout_dir}")

            if not os.path.exists(layout_dir):
                logger.debug(f"Layout directory does not exist: {layout_dir}")
                continue

            version_dirs = [d for d in os.listdir(layout_dir) if re.fullmatch(r"v\d{3}", d)]
            logger.debug(f"Found version directories: {version_dirs}")

            if not version_dirs:
                logger.debug("No version directories found.")
                continue

            latest = max(version_dirs)
            logger.debug(f"Latest version directory: {latest}")

            target_dir = os.path.join(layout_dir, latest)
            expected_filename = f"{seq}-{shot}_{layout_pattern}_{latest}.usda"
            logger.debug(f"Expecting file: {expected_filename}")

            for f in os.listdir(target_dir):
                logger.debug(f"Checking file: {f}")
                if f.lower() == expected_filename.lower():
                    usda_path = os.path.join(target_dir, f)
                    logger.debug(f"Found matching USDA file: {usda_path}")
                    return usda_path
                logger.debug("--------------------------------------")
                logger.debug (f.lower().split("-")[-1])
                if f.lower() in expected_filename.lower():
                    usda_path = os.path.join(target_dir, f)
                    logger.debug(f"Found matching USDA file: {usda_path}")
                    return usda_path
        logger.warning("No matching USDA file found in any pattern.")
        return None


    # ----------------------------------script for maya ----------------------------------
    def load_maya_work_layer(self):
        stage = self.get_selected_stageMaya()
        if not stage:
            self.set_log("⛔ No valid USD stage selected in Maya.")
            return

        layer = stage.GetEditTarget().GetLayer()
        # content = layer.ExportToString()
        # self.parse_payloads(content)
        self.pathFile = ''
        self.parse_dependencies(layer)


    def get_selected_stageMaya(self):
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
    

    # ----------------------------------script for houdini ----------------------------------
    def load_houdini_work_layer(self):
        stage = self.get_selected_stageHoudini()
        if not stage:
            self.set_log("⛔ No valid USD stage selected in houdini.")
            return
        try:
            layer = stage.GetRootLayer()
            self.parse_dependencies(layer)
        except Exception as e:
            logger.warning(f'Did not get layer or dependencies: {e}')
            self.set_log(f'Did not get layer or dependencies: {e}')
            

    def get_selected_stageHoudini(self):
        nodes = hou.selectedNodes()
        if not nodes:
            hou.ui.displayMessage(
                text='Please select a node and refresh',
                severity=hou.severityType.Warning)
            return
        node: hou.LopNode = nodes[0]
        stage = node.stage()
        if not self.set_pathFile_houdini():
            return
        return stage


    def set_pathFile_houdini(self):
        scene_name = Path(hou.hipFile.name())
        entity_parts = scene_name.parts[:-4]
        if not entity_parts:
            return False
        entity_path = Path(*entity_parts)
        glob_pattern = entity_path / 'Export/USD/*'
        usd_versions = glob.glob(glob_pattern.as_posix())
        if not usd_versions:
            return False
        self.pathFile = os.path.join(usd_versions[-1], 'anon.usd')
        return True


    # ----------------------------------for all----------------------------------
    def resolve_path(self, assetPathProcessed: str) -> Path:
        asset_path = Path(assetPathProcessed)
        if asset_path.is_absolute():
            return asset_path
        else:
            relative_to_layer_path = self.dirname / asset_path
            if relative_to_layer_path.exists():
                return relative_to_layer_path
            try:
                resolver = Ar.GetResolver()
                resolved_path = resolver.Resolve(assetPathProcessed)
                resolved_path = resolved_path.GetPathString()
                if os.path.exists(resolved_path):
                    return Path(resolved_path)
                resolved_path = Path(resolved_path)
                parent_path = Path(*resolved_path.parts[:2])
                parent_resolved = resolver.Resolve(parent_path.as_posix())
                parent_resolved = parent_resolved.GetPathString()
                if os.path.exists(parent_resolved):
                    return Path(parent_resolved).parts[0] / Path(*resolved_path.parts[1:])
            except Exception as e:
                logger.warning(e)
            return relative_to_layer_path
        
    
    def parse_filter(self, assetPathProcessed):
        logger.debug(f'Parse {assetPathProcessed}')
        
        # resolve path from context or layer if needed
        resolved_path = self.resolve_path(assetPathProcessed)
        if len(resolved_path.parts) < 2:
            logger.debug(' - path is too short')
            return assetPathProcessed
        
        # create item
        relative_path = Path(*resolved_path.parts[1:])
        item = AssetItem(
            assetPathProcessed,
            relative_path.as_posix(),
            None,
            None
        )
        
        # check extension for USD files
        extension = resolved_path.suffix
        if not extension in ['.usdc', '.usda']:
            logger.debug(' - not an USD file')
            self.add_list_item_abs(item)
            return assetPathProcessed
        
        # parse alternate versions paths
        glob_pattern = (
            re
            .sub(r'v\d{2,9}', 'v*', resolved_path.as_posix())
            .replace(extension, '.usd*')
        )
        versions = glob.glob(glob_pattern)
        versions.sort()
        if not versions:
            self.set_log(f"❌ Did not found others versions: {assetPathProcessed}")
            logger.debug(' - did not found others versions')
            self.add_list_item_abs(item)
            return assetPathProcessed
        
        # parse versions digits
        version_pattern = r'.*?v(\d{2,9}).*?'
        latest_match = re.search(version_pattern, versions[-1])
        current_match = re.search(version_pattern, assetPathProcessed)
        if not current_match or not latest_match:
            self.set_log(f"❌ Skipped (invalid or unresolvable): {assetPathProcessed}")
            logger.debug(' - skipped (invalid or unresolvable)')
            self.add_list_item_abs(item)
            return assetPathProcessed
        
        # check if the current asset is the latest
        latest_version = int(latest_match.group(1))
        current_version = int(current_match.group(1))
        if latest_version == current_version:
            logger.debug(' - Already updated')
            self.set_log(f"🟰 Skipping up-to-date: {assetPathProcessed}")
            self.add_list_item_abs(item)
            return assetPathProcessed
            
        # update item to show latest and current version
        logger.debug(' - Can be updated')
        updatedPath = re.sub(
            r'v\d{2,9}', f'v{latest_match.group(1)}',
            relative_path.as_posix()
        )
        item.updated_path = updatedPath
        item.from_version = current_version
        item.to_version = latest_version
        self.add_list_item_once(item)
        return assetPathProcessed
    
    
    def apply_parse_filter(self, layer, depInfos):
        if layer.identifier == self.previousLayer:
            return depInfos
        path = layer.resolvedPath.GetPathString()
        if not path:
            return depInfos
        self.dirname = Path(path).parent
        self.previousLayer = layer.identifier
        UsdUtils.ModifyAssetPaths(layer, self.parse_filter)
        self.dirname = ''
        return depInfos


    def load_USD(self):
        layer = Sdf.Layer.FindOrOpen(self.pathFile)
        layer.Reload(True)
        if layer:
            self.parse_dependencies(layer)
    
    
    def recursive_parse_dependencies(self, layer):
        self.dirname = Path((self.pathFile)).parent
        UsdUtils.ModifyAssetPaths(layer, self.parse_filter)
        self.previousLayer = layer.identifier
        UsdUtils.ComputeAllDependencies(layer.identifier, self.apply_parse_filter)    
        self.dirname = ''
        
            
    def parse_dependencies(self, layer):
        self.ar_context = Ar.DefaultResolverContext(["I:/", "R:/"])
        with Ar.ResolverContextBinder(self.ar_context):
            self.dirname = Path((self.pathFile)).parent
            UsdUtils.ModifyAssetPaths(layer, self.parse_filter)
            self.previousLayer = layer.identifier
            self.dirname = ''


    def add_list_item_once(self, item):
        # add item to update list if new
        if (item not in self.listAssetsNeedUpdate):
            self.listAssetsNeedUpdate.append(item)
            self.add_list_item(item)
        
    
    def add_list_item_abs(self, item):
        # add item to update list if new and absolute
        if (item not in self.listAssetsNeedUpdate
            and os.path.isabs(item.original_path)):
            self.listAssetsNeedUpdate.append(item)
            self.add_list_item(item)
        

    def add_list_item(self, item):
        if not item.from_version:
            checkbox = Qt.QCheckBox(f"{item.original_path}\n➡ make relative")
        else:
            checkbox = Qt.QCheckBox(f"{item.original_path}\n➡ v{item.from_version:03d} → v{item.to_version:03d}")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(lambda state, i=item: setattr(i, 'should_update', state == Qtc.Qt.Checked))
        list_item = Qt.QListWidgetItem()
        self.QlistUSDNeedUpdate.addItem(list_item)
        self.QlistUSDNeedUpdate.setItemWidget(list_item, checkbox)
        list_item.setSizeHint(checkbox.sizeHint())
        self.checkboxWidgetPayload.append(checkbox)


    def update_filter(self, assetPathProcessed):
        asset_path = Path(assetPathProcessed)
        extension = asset_path.suffix

        # remove drive if the path has a drive to help ar resolver 
        if asset_path.is_absolute() and len(asset_path.parts) > 2:
            asset_path = Path(*asset_path.parts[1:]).as_posix()
        else:
            asset_path = assetPathProcessed
            
        if not extension in ['.usdc', '.usda']:
            return asset_path
        
        # check if the assetPathProcessed should be update
        for item in self.listAssetsNeedUpdate:
            if item.should_update and item.original_path == assetPathProcessed:
                self.set_log(f"✅ Updated: {item.original_path} → {item.updated_path}")
                self.changed = True
                return item.updated_path

        return asset_path
    
    
    def apply_update_filter(self, layer, depInfos):
        if layer.identifier == self.previousLayer:
            return depInfos
        path = layer.resolvedPath.GetPathString()
        if not path:
            return depInfos
        self.previousLayer = layer.identifier
        self.changed = False
        UsdUtils.ModifyAssetPaths(layer, self.update_filter)
        if self.changed:
            layer.Save()
            logger.debug("Update complete.")
            self.set_log("🎉 Update complete.")
        else:
            logger.debug("Nothing to update.")
            self.set_log("✅ Nothing to update.")
        self.changed = False
        return depInfos


    def update_layer(self, layer):
        logger.debug('Updating ...')
        self.changed = False
        UsdUtils.ModifyAssetPaths(layer, self.update_filter)
        if self.changed:
            layer.Save()
            logger.debug("Update complete.")
            self.set_log("🎉 Update complete.")
        else:
            logger.debug("Nothing to update.")
            self.set_log("✅ Nothing to update.")
        layer.Save()
        logger.debug('Update saved')
        self.changed = False


    def recursive_update(self, layer):
        self.changed = False
        UsdUtils.ModifyAssetPaths(layer, self.update_filter)
        changed = self.changed
        self.previousLayer = layer.identifier
        UsdUtils.ComputeAllDependencies(layer.identifier, self.apply_update_filter)
        if changed:
            layer.Save()
            self.set_log("🎉 Update complete.")
        else:
            self.set_log("✅ Nothing to update.")
        self.changed = False


    def run_update(self):
        statute = self.typeUpdate.currentIndex()
        self.QlistUSDNeedUpdate.clear()
        self.logBox.clear()

        if not statute:
            if not self.pathFile:
                self.set_log("⛔ No USDA file selected.")
                return
            
            layer = Sdf.Layer.FindOrOpen(self.pathFile)
            layer.Reload(True)
            
            # Generate timestamp string: YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = f"{self.pathFile}.{timestamp}.bak"
            
            shutil.copy2(self.pathFile, backup)
            self.set_log(f"🗂️ Backup created: {backup}")
        else:
            if self.openType == "maya":
                stage = self.get_selected_stageMaya()
            elif self.openType == "houdini":
                stage = self.get_selected_stageHoudini()
            else:
                self.set_log("⛔ Error impossible to get the stage")
                return
            
            if not stage:
                self.set_log("⛔ No valid USD stage.")
                return
            layer = stage.GetEditTarget().GetLayer()
            
        if layer:
            self.set_log(f"Asset items ready: {len(self.listAssetsNeedUpdate)}")
            self.update_layer(layer)
            layer.Reload(True)
            
            if not statute:
                self.load_USD()
            else:
                if self.openType == "maya":
                    self.load_maya_work_layer()
                elif self.openType == "houdini":
                    self.load_houdini_work_layer()
                elif self.openType == "prism":
                    self.set_log("⛔ Impossible défectuer cette option dans prism. Valable uniquement dans maya et houdini")
        else:
            self.set_log(f"Could not get USD layer")
            return    

    
    # ----------------------------------OLD----------------------------------
    def parse_payloads(self, content):
        pattern = r"@[^@]+\.usd[ac]@(?:<[^>]+>)?"  # Simplified: focus only on @...usd[ac]@
        matches = re.findall(pattern, content, re.IGNORECASE)
        seen = set()
        self.set_log(f"Found {len(matches)} payload(s)")
        
        for m in matches:
            clean_path = re.sub(r"<[^>]+>$", "", m)  # Remove optional target path
            m_norm = clean_path.lower()
            if m_norm in seen:
                continue
            seen.add(m_norm)
            item = self.find_latest_version_path(clean_path)
            if item:
                if item.from_version != item.to_version:
                    self.listAssetsNeedUpdate.append(item)
                    self.add_list_item(item)
                else:
                    self.set_log(f"🟰 Skipping up-to-date: {item.original_path}")
            else:
                self.set_log(f"❌ Skipped (invalid or unresolvable): {clean_path}")
                
                
    def find_latest_version_path(self, original_path):
        match = re.match(
            r"@(?P<base>.+?/Export/.+?/)v(?P<version>\d{3})/(?P<asset_name>.+)_.+?_(v\d{3}\.usd[ac])@",
            original_path,
            re.IGNORECASE
        )
        if not match:
            return None

        base_dir = match.group("base").replace("/", os.sep)
        current_version = int(match.group("version"))
        asset_name = match.group("asset_name")

        if not os.path.exists(base_dir):
            return None

        versions = [int(folder[1:]) for folder in os.listdir(base_dir)
                    if re.fullmatch(r"v\d{3}", folder)]
        if not versions:
            return None

        latest_version = max(versions)
        latest_str = f"v{latest_version:03d}"
        latest_folder = os.path.join(base_dir, latest_str)

        for fname in os.listdir(latest_folder):
            if re.fullmatch(f"{re.escape(asset_name)}_.+?_{latest_str}\\.usd[ac]", fname, re.IGNORECASE):
                latest_path = f"@{match.group('base')}/{latest_str}/{fname}@"
                return AssetItem(
                    original_path,
                    latest_path,
                    current_version,
                    latest_version
                )
        return None
    

def startUpdateAssetsUSD(openType, tmpfile =None):    
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
    
    my_window = mainInterface(openType, tmpfile, instance)
    my_window.show()
    if app_start:
        sys.exit(app.exec_())