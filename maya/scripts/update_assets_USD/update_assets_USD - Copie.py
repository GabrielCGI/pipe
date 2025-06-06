# Merged USDA Updater with Maya Work Layer Support

import os
import re
import shutil
import tempfile
from datetime import datetime
from PySide6 import QtWidgets, QtCore
from maya import OpenMayaUI, cmds
from shiboken6 import wrapInstance
from pxr import Usd
import mayaUsd

BASE_ASSET_PATH = "I:/ralphLauren_2412/03_Production/Assets/"

TMP_FILE_NAME = "USD_Maya_copy_paste_script_tmp.usda"

class AssetItem:
    def __init__(self, original_path, updated_path, from_version, to_version):
        self.original_path = original_path
        self.updated_path = updated_path
        self.from_version = from_version
        self.to_version = to_version
        self.should_update = True

def maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def find_latest_version_path(original_path):
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


class USDAUpdaterUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("USD Payload Updater")
        self.setMinimumSize(900, 800)
        self.asset_items = []
        self.checkbox_widgets = []
        self.usda_file = None
        self.mode = 'file'  # or 'maya'
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Mode selector
        self.mode_selector = QtWidgets.QComboBox()
        self.mode_selector.addItems(["Update from USDA file", "Update Maya Work Layer"])
        self.mode_selector.currentIndexChanged.connect(self.update_mode)
        layout.addWidget(self.mode_selector)

        # File selection
        self.file_path_edit = QtWidgets.QLineEdit()
        self.file_browse_btn = QtWidgets.QPushButton("Browse...")
        self.file_browse_btn.clicked.connect(self.browse_file)
        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.file_browse_btn)
        layout.addLayout(file_layout)

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)

        select_btns_layout = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton("Select All")
        self.deselect_all_btn = QtWidgets.QPushButton("Deselect All")
        self.select_all_btn.clicked.connect(lambda: self.set_all_checkboxes(True))
        self.deselect_all_btn.clicked.connect(lambda: self.set_all_checkboxes(False))
        select_btns_layout.addWidget(self.select_all_btn)
        select_btns_layout.addWidget(self.deselect_all_btn)
        layout.addLayout(select_btns_layout)

        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(250)
        layout.addWidget(self.log_box)

        self.run_button = QtWidgets.QPushButton("Run Update")
        self.run_button.clicked.connect(self.run_update)
        layout.addWidget(self.run_button)

        self.update_mode()

    def log(self, text):
        self.log_box.append(text)

    def update_mode(self):
        self.mode = 'maya' if self.mode_selector.currentIndex() == 1 else 'file'
        self.file_path_edit.setEnabled(self.mode == 'file')
        self.file_browse_btn.setEnabled(self.mode == 'file')
        self.list_widget.clear()
        self.asset_items.clear()
        self.checkbox_widgets.clear()
        if self.mode == 'file':
            try:
                default_file = self.find_latest_maya_layout_usda()
                self.log(f"default file: {default_file}")
                if default_file:
                    self.file_path_edit.setText(default_file)
                    self.load_usda(default_file)
            except Exception as e:
                self.log(f"⚠️ Error loading USDA file: {e}")
        else:
            self.load_maya_work_layer()

    def browse_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select USDA File", "C:/", "USDA Files (*.usda)")
        if path:
            self.file_path_edit.setText(path)
            self.load_usda(path)



    def find_latest_maya_layout_usda(self):
        print("Fetching current Maya scene path...")
        scene_path = cmds.file(q=True, sceneName=True)
        print(f"Scene path: {scene_path}")

        print("Attempting to extract sequence and shot from the scene path...")
        match = re.search(r"Shots[\\/](?P<seq>[A-Z0-9]+)[\\/](?P<shot>\d+)", scene_path, re.IGNORECASE)
        if not match:
            print("No match found for sequence and shot in the scene path.")
            return None

        seq = match.group("seq")
        shot = match.group("shot")
        print(f"Extracted sequence: {seq}, shot: {shot}")

        layout_dir = os.path.join("I:/ralphLauren_2412/03_Production/Shots", seq, shot, "Export", "_layer_layout_layoutMaya")
        print(f"Constructed layout directory path: {layout_dir}")

        if not os.path.exists(layout_dir):
            print(f"Layout directory does not exist: {layout_dir}")
            return None

        print("Listing version directories in layout directory...")
        version_dirs = [d for d in os.listdir(layout_dir) if re.fullmatch(r"v\d{3}", d)]
        print(f"Found version directories: {version_dirs}")

        if not version_dirs:
            print("No version directories found.")
            return None

        latest = max(version_dirs)
        print(f"Latest version directory: {latest}")

        target_dir = os.path.join(layout_dir, latest)
        print(f"Looking for USDA file in: {target_dir}")
        expected_filename = f"{seq}-{shot}__layer_layout_layoutMaya_{latest}.usda"
        print(f"Expecting file: {expected_filename}")
        for f in os.listdir(target_dir):
            print(f"Checking file: {f}")
            if f.lower() == expected_filename.lower():
                usda_path = os.path.join(target_dir, f)
                print(f"Found matching USDA file: {usda_path}")
                return usda_path

        print("No matching USDA file found.")
        return None


    def load_usda(self, filepath):
        self.usda_file = filepath
        self.asset_items.clear()
        self.checkbox_widgets.clear()
        self.list_widget.clear()
        self.log_box.clear()

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        self.parse_payloads(content)

    def load_maya_work_layer(self):
        self.asset_items.clear()
        self.checkbox_widgets.clear()
        self.list_widget.clear()
        self.log_box.clear()

        stage = self.get_selected_stage()
        if not stage:
            self.log("⛔ No valid USD stage selected in Maya.")
            return

        layer = stage.GetEditTarget().GetLayer()
        content = layer.ExportToString()
        self.parse_payloads(content)

    def get_selected_stage(self):
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

 
    def parse_payloads(self, content):
        escaped_base = re.escape(BASE_ASSET_PATH.replace('\\', '/'))
        pattern = r"@[^@]+\.usd[ac]@(?:<[^>]+>)?"  # Simplified: focus only on @...usd[ac]@
        matches = re.findall(pattern, content, re.IGNORECASE)
        seen = set()
        self.log(f"Found {len(matches)} payload(s)")
        for m in matches:
            clean_path = re.sub(r"<[^>]+>$", "", m)  # Remove optional target path
            m_norm = clean_path.lower()
            if m_norm in seen:
                continue
            seen.add(m_norm)
            item = find_latest_version_path(clean_path)
            if item:
                if item.from_version != item.to_version:
                    self.asset_items.append(item)
                    self.add_list_item(item)
                else:
                    self.log(f"🟰 Skipping up-to-date: {item.original_path}")
            else:
                self.log(f"❌ Skipped (invalid or unresolvable): {clean_path}")


    def add_list_item(self, item):
        checkbox = QtWidgets.QCheckBox(
            f"{item.original_path}\n➡ v{item.from_version:03d} → v{item.to_version:03d}"
        )
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(lambda state, i=item: setattr(i, 'should_update', state == QtCore.Qt.Checked))
        list_item = QtWidgets.QListWidgetItem()
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, checkbox)
        list_item.setSizeHint(checkbox.sizeHint())
        self.checkbox_widgets.append(checkbox)

    def set_all_checkboxes(self, value):
        for cb in self.checkbox_widgets:
            cb.setChecked(value)

    def run_update(self):
        if self.mode == 'file':
            if not self.usda_file:
                self.log("⛔ No USDA file selected.")
                return
            with open(self.usda_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate timestamp string: YYYYMMDD_HHMMSS
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = f"{self.usda_file}.{timestamp}.bak"
            
            shutil.copy2(self.usda_file, backup)
            self.log(f"🗂️ Backup created: {backup}")
        else:
            stage = self.get_selected_stage()
            if not stage:
                self.log("⛔ No valid USD stage.")
                return
            layer = stage.GetEditTarget().GetLayer()
            content = layer.ExportToString()

        self.log(f"Asset items ready: {len(self.asset_items)}")
        
        changed = False
        for item in self.asset_items:
            if item.should_update and item.original_path in content:
                content = content.replace(item.original_path, item.updated_path)
                self.log(f"✅ Updated: {item.original_path} → {item.updated_path}")
                changed = True

        if changed:
            if self.mode == 'file':
                with open(self.usda_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                layer.ImportFromString(content)
            self.log("🎉 Update complete.")
        else:
            self.log("✅ Nothing to update.")

        if self.mode == 'file':
            self.load_usda(self.usda_file)
        else:
            self.load_maya_work_layer()

def show_usda_updater_in_maya():
    global updater_window
    try:
        updater_window.close()
        updater_window.deleteLater()
    except:
        pass
    updater_window = USDAUpdaterUI(parent=maya_main_window())
    updater_window.show()
show_usda_updater_in_maya()