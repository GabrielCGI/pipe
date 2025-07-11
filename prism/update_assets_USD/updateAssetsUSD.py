try:
    from shiboken6 import wrapInstance
except:
    pass
try:
    from shiboken2 import wrapInstance
except:
    pass

from datetime import datetime
import glob
import shutil
import sys
import os
import re

#switch sur la version 2 de pyside si la 6 et pas installer
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






#import for maya 
try:
    from maya import OpenMayaUI, cmds
    from pxr import Usd
    import mayaUsd
except:
    pass


#import for houdini 
try:
    import hou
except:
    pass



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
        



        #------------------------------------------------ Create interface ------------------------------------------------
        Mainwindow = Qt.QWidget()
        self.setCentralWidget(Mainwindow)
        mainLayout = Qt.QVBoxLayout(Mainwindow)


        #--------------------type Update  Worklayer  ou USDA file--------------------
        self.typeUpdate = Qt.QComboBox()
        self.typeUpdate.addItems(["Update from USDA file", "Update Maya Work Layer"])
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

        self.runBtm = Qt.QPushButton("Run Update")
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
        #trouver le passe 
        if self.pathFile:
            chosePlaceSplit = self.pathFile.replace("\\", "/")
            chosePlaceSplit = chosePlaceSplit.split("/")[:-1]
            chosePlace = "/".join(chosePlaceSplit)
        else:
            chosePlace = "c:/"
        
        path, _ = Qt.QFileDialog.getOpenFileName(self, "Select USDA File", chosePlace, "USDA Files (*.usda)") # possibiliter de détécter auto le path
        if path:
            self.clearInterfaceData()
            self.USDFileNeedUpdate.setText(path)
            self.pathFile = path
            self.load_USDa()


    #----find layer on maya/houdini/prism----
    def find_USD_File_To_Update(self):
        self.clearInterfaceData()
        statute = self.typeUpdate.currentIndex()

        if not statute:
            try:
                self.pathFile = self.find_Lastest_layout_usda()
                if self.pathFile:
                    self.USDFileNeedUpdate.setText(self.pathFile)
                    self.set_log(f"default file: {self.pathFile}")
                    self.load_USDa()

            except Exception as e:
                self.set_log(f"⚠️ Error loading USDA file: {e}")

        else:
            if self.openType == "maya":
                self.load_maya_work_layer()
            elif self.openType == "houdini":
                self.load_houdini_work_layer()
            elif self.openType == "prism":
                self.set_log("⛔ impossible défectuer cette option dans prism.   valable uniquement dans maya et houdini")

    #---trouve le dernier publish de la scene maya en question---
    def find_Lastest_layout_usda(self):
        if self.openType == "maya":
            print("-------------Fetching current Maya scene path...")
            scene_path = cmds.file(q=True, sceneName=True)
        elif self.openType == "houdini":
            scene_path = hou.hipFile.path()

        elif self.openType == "prism":
            print("--------------------------- file prism")
            return self.pathPrism.replace("\\", "/") # le passe que prism va donner 
        else:
            self.set_log(f"⚠️ Error loading USDA file : pas de file scene donné")
            return None
        
        
        print("Extracting project root, sequence, and shot...")
        parts = scene_path.split("/")
        if len(parts) < 6:
            print("Scene path is too short to extract project structure.")
            return None

        project_root = "/".join(parts[:4])  # I:/intermarche/03_Production/Shots
        seq = parts[4]
        shot = parts[5]

        print(f"Extracted project root: {project_root}")
        print(f"Extracted sequence: {seq}, shot: {shot}")

        layout_patterns = ["_layer_layout_layoutMaya", "_layer_lay_main","_layer_mod_mayaLayout"]

        for layout_pattern in layout_patterns:
            layout_dir = os.path.join(project_root, seq, shot, "Export", layout_pattern)
            print(f"Checking layout directory: {layout_dir}")

            if not os.path.exists(layout_dir):
                print(f"Layout directory does not exist: {layout_dir}")
                continue

            version_dirs = [d for d in os.listdir(layout_dir) if re.fullmatch(r"v\d{3}", d)]
            print(f"Found version directories: {version_dirs}")

            if not version_dirs:
                print("No version directories found.")
                continue

            latest = max(version_dirs)
            print(f"Latest version directory: {latest}")

            target_dir = os.path.join(layout_dir, latest)
            expected_filename = f"{seq}-{shot}_{layout_pattern}_{latest}.usda"
            print(f"Expecting file: {expected_filename}")

            for f in os.listdir(target_dir):
                print(f"Checking file: {f}")
                if f.lower() == expected_filename.lower():
                    usda_path = os.path.join(target_dir, f)
                    print(f"Found matching USDA file: {usda_path}")
                    return usda_path
                print("--------------------------------------")
                print (f.lower().split("-")[-1])
                if f.lower() in expected_filename.lower():
                    usda_path = os.path.join(target_dir, f)
                    print(f"Found matching USDA file: {usda_path}")
                    return usda_path
        print("No matching USDA file found in any pattern.")
        return None



    # ----------------------------------script for maya ----------------------------------
    def load_maya_work_layer(self):
        stage = self.get_selected_stageMaya()
        if not stage:
            self.set_log("⛔ No valid USD stage selected in Maya.")
            return

        layer = stage.GetEditTarget().GetLayer()
        content = layer.ExportToString()
        self.parse_payloads(content)

    def get_selected_stageMaya(self):
        """
        Return the selected USD stage if it's a mayaUsdProxyShape,
        or fallback to the first mayaUsdProxyShape in the scene.
        """
        maya_stage_node = cmds.ls(selection=True, l=True)

        if maya_stage_node:
            selected_node = maya_stage_node[0]
            node_type = cmds.nodeType(selected_node)
            print(f"Selected node: {selected_node}, type: {node_type}")
            
            if node_type != "mayaUsdProxyShape":
                print("Selected node is not of type mayaUsdProxyShape. Searching for a valid one...")
                selected_node = None
            else:
                print("Selected node is a valid mayaUsdProxyShape.")
        else:
            print("No selection found.")
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
                print("No mayaUsdProxyShape found in the scene")
                return None
            selected_node = proxy_shapes[0]
            print(f"Using first mayaUsdProxyShape: {selected_node}")

        asset_stage = mayaUsd.ufe.getStage(selected_node)
        if asset_stage is None:
            cmds.confirmDialog(
                title='Invalid stage',
                message='Could not get stage from the selected node',
                button=['OK'],
                defaultButton='OK'
            )
            cmds.warning('Could not get stage from the selected node')
            print("Could not get stage from the selected node")
            return None

        print("Successfully retrieved stage.")
        return asset_stage
    


    # ----------------------------------script for houdini ----------------------------------
    def load_houdini_work_layer(self):
        stage = self.get_selected_stageHoudini()
        if not stage:
            self.set_log("⛔ No valid USD stage selected in houdini.")
            return

        layer = stage.GetEditTarget().GetLayer()
        content = layer.ExportToString()
        self.parse_payloads(content)

    def get_selected_stageHoudini(self):
        self.set_log("WIP--------------en coure de construction--------------WIP")


    # for all 
    def load_USDa(self):
        with open(self.pathFile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.parse_payloads(content)

    def convert_to_resolver_path(self):
        with open(self.pathFile, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match only payloads starting with drive letters (e.g., @I:/...)
        pattern = r"@[A-Z]:/[^@]+\.usd[ac]@(?:<[^>]+>)?"
        matches = re.findall(pattern, content, re.IGNORECASE)

        seen = set()
        self.set_log(f"🔍 Found {len(matches)} absolute-path payload(s) to fix.")

        for match in matches:
            if match in seen:
                continue
            seen.add(match)

            # Remove the drive letter and colon
            updated = re.sub(r'@[A-Z]:/', '@', match)

            if updated != match:
                self.set_log(f"🚚 Path fixed: {match} ➜ {updated}")
                content = re.sub(re.escape(match), updated, content)

        with open(self.pathFile, 'w', encoding='utf-8') as f:
            f.write(content)

        return content
    
    def parse_payloads(self, content):
        pattern = r"@[^@]+\.usd[ac]@(?:<[^>]+>)?"  # Simplified: focus only on @...usd[ac]@
        matches = re.findall(pattern, content, re.IGNORECASE)
        seen = set()
        self.set_log("debug")
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

    def add_list_item(self, item):
        checkbox = Qt.QCheckBox(f"{item.original_path}\n➡ v{item.from_version:03d} → v{item.to_version:03d}")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(lambda state, i=item: setattr(i, 'should_update', state == Qtc.Qt.Checked))
        list_item = Qt.QListWidgetItem()
        self.QlistUSDNeedUpdate.addItem(list_item)
        self.QlistUSDNeedUpdate.setItemWidget(list_item, checkbox)
        list_item.setSizeHint(checkbox.sizeHint())
        self.checkboxWidgetPayload.append(checkbox)


    def find_latest_version_path(self, original_path):
        raw_path = original_path.strip("@")
        is_relative = not os.path.isabs(raw_path) and not raw_path.startswith("/")
        resolver_roots = ["I:/", "R:/"]  # AR_PXR_DEFAULT_RESOLVER

        candidate_paths = []

        if is_relative:
            # Relative to USDA file
            if self.pathFile:
                rel_base = os.path.normpath(os.path.join(os.path.dirname(self.pathFile), raw_path))
                candidate_paths.append((rel_base, "relative"))

            # Logical path via resolver roots
            for root in resolver_roots:
                combined = os.path.normpath(os.path.join(root, raw_path))
                candidate_paths.append((combined, root))
        else:
            candidate_paths.append((os.path.normpath(raw_path), None))

        for resolved_path, source in candidate_paths:
            normalized_path = resolved_path.replace("\\", "/")
            match = re.match(
                r"(.+/Export/.+?/)(v\d{3})/([^/]+)_.+?_(v\d{3}\.usd[ac])$",
                normalized_path,
                re.IGNORECASE
            )
            if not match:
                continue

            base_dir = os.path.normpath(match.group(1))
            current_version = int(match.group(2)[1:])
            asset_name = match.group(3)

            if not os.path.exists(base_dir):
                continue

            versions = [int(f[1:]) for f in os.listdir(base_dir) if re.fullmatch(r"v\d{3}", f)]
            if not versions:
                continue

            latest_version = max(versions)
            latest_str = f"v{latest_version:03d}"
            latest_folder = os.path.join(base_dir, latest_str)

            for fname in os.listdir(latest_folder):
                if re.fullmatch(rf"{re.escape(asset_name)}_.+?_{latest_str}\.usd[ac]", fname, re.IGNORECASE):
                    updated_abs_path = os.path.join(base_dir, latest_str, fname)

                    # Compute updated_path safely (avoid backslashes in f-strings)
                    if source == "relative":
                        rel_path = os.path.relpath(updated_abs_path, os.path.dirname(self.pathFile))
                        rel_path = rel_path.replace("\\", "/")
                        updated_path = "@{}@".format(rel_path)
                    elif source in resolver_roots:
                        logical_part = os.path.relpath(updated_abs_path, source)
                        logical_part = logical_part.replace("\\", "/")
                        updated_path = "@{}@".format(logical_part)
                    else:
                        abs_path = updated_abs_path.replace("\\", "/")
                        updated_path = "@{}@".format(abs_path)

                    return AssetItem(
                        original_path=original_path,
                        updated_path=updated_path,
                        from_version=current_version,
                        to_version=latest_version
                    )

        return None



    def run_update(self):
        statute = self.typeUpdate.currentIndex()
        self.QlistUSDNeedUpdate.clear()
        self.logBox.clear()
        self.set_log("debug")



        if not statute:
            if not self.pathFile:
                self.set_log("⛔ No USDA file selected.")
                return
            with open(self.pathFile, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
            content = layer.ExportToString()

        self.set_log(f"Asset items ready: {len(self.listAssetsNeedUpdate)}")
        
        changed = False
        for item in self.listAssetsNeedUpdate:
            if item.should_update and item.original_path in content:
                content = content.replace(item.original_path, item.updated_path)
                self.set_log(f"✅ Updated: {item.original_path} → {item.updated_path}")
                changed = True

        if changed:
            if not statute:
                with open(self.pathFile, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                layer.ImportFromString(content)
            self.set_log("🎉 Update complete.")
        else:
            self.set_log("✅ Nothing to update.")

        if not statute:
            self.load_USDa()
        else:
            self.load_maya_work_layer()
        
        self.convert_to_resolver_path()


        
 

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