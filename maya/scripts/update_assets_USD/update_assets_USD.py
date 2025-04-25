import os
import re
import shutil
from PySide6 import QtWidgets, QtCore
from maya import OpenMayaUI, cmds
from shiboken6 import wrapInstance
print("yo2")
# ✅ Set this to your project-specific base asset path (slashes can be forward or back)
BASE_ASSET_PATH = "I:/ralphLauren_2412/03_Production/Assets/"

def maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class AssetItem:
    def __init__(self, original_path, updated_path, from_version, to_version):
        self.original_path = original_path
        self.updated_path = updated_path
        self.from_version = from_version
        self.to_version = to_version
        self.should_update = True

def find_latest_version_path(original_path):
    match = re.match(
        r"@(?P<base>.+/Export/USD)/v(?P<version>\d{3})/(?P<filename>(?P<asset>[^/_]+)_USD_v\d{3}\.(usd[ac]))@",
        original_path
    )
    if not match:
        return None

    base_dir = match.group("base").replace("/", os.sep)
    asset_name = match.group("asset")
    current_version = int(match.group("version"))

    if not os.path.exists(base_dir):
        return None

    versions = [int(folder[1:]) for folder in os.listdir(base_dir)
                if re.fullmatch(r"v\d{3}", folder)]

    if not versions:
        return None

    latest_version = max(versions)
    latest_str = f"v{latest_version:03d}"
    latest_folder = os.path.join(base_dir, latest_str)

    # Cherche le fichier correspondant au nom de l’asset, peu importe l’extension
    for fname in os.listdir(latest_folder):
        if re.fullmatch(f"{asset_name}_USD_{latest_str}\\.usd[ac]", fname, re.IGNORECASE):
            latest_path = f"@{match.group('base')}/{latest_str}/{fname}@"
            return AssetItem(
                original_path=original_path,
                updated_path=latest_path,
                from_version=current_version,
                to_version=latest_version
            )

    return None

class USDAUpdaterUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("USD Payload Updater")
        self.setMinimumSize(900, 800)
        self.asset_items = []
        self.usda_file = None
        self.checkbox_widgets = []
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # File selection
        file_layout = QtWidgets.QHBoxLayout()
        self.file_path_edit = QtWidgets.QLineEdit()
        self.file_browse_btn = QtWidgets.QPushButton("Browse...")
        self.file_browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.file_browse_btn)
        layout.addLayout(file_layout)

        # List + buttons
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

        # Log box
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(250)
        layout.addWidget(self.log_box)

        # Run button
        self.run_button = QtWidgets.QPushButton("Run Update")
        self.run_button.clicked.connect(self.run_update)
        layout.addWidget(self.run_button)
        # 🟢 Try to auto-load the latest mayaLayout.usda file
        try:
            default_usda = self.find_latest_maya_layout_usda()
            if default_usda:
                self.file_path_edit.setText(default_usda)
                self.load_usda(default_usda)
        except Exception as e:
            self.log(f"⚠️ Error finding default USDA file: {e}")
            
    def log(self, text):
        self.log_box.append(text)

    def browse_file(self):
        start_dir = os.path.dirname(self.find_latest_maya_layout_usda()) or "C:/"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select USDA File",
            start_dir,
            "USDA Files (*.usda)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self.load_usda(file_path)

    # 🔍 Finds the latest mayaLayout.usda file based on the current Maya scene
    def find_latest_maya_layout_usda(self):
        scene_path = cmds.file(q=True, sceneName=True)
        if not scene_path:
            print("⛔ No scene loaded.")
            return None

        match = re.search(r"Shots[\\/](?P<seq>[A-Z0-9]+)[\\/](?P<shot>\d+)", scene_path, re.IGNORECASE)
        if not match:
            print("⛔ Could not determine sequence and shot from path.")
            return None

        sequence = match.group("seq")
        shot = match.group("shot")
        shot_path = os.path.join("I:/ralphLauren_2412/03_Production/Shots", sequence, shot)
        layout_dir = os.path.join(shot_path, "Export", "_layer_layout_layoutMaya")
        print(layout_dir)

        if not os.path.exists(layout_dir):
            print(f"⛔ Layout directory not found: {layout_dir}")
            return None

        version_dirs = [d for d in os.listdir(layout_dir) if re.fullmatch(r"v\d{3}", d)]
        if not version_dirs:
            print("⛔ No version folders found.")
            return None

        latest_version = max(version_dirs)
        latest_path = os.path.join(layout_dir, latest_version)
        expected_name_pattern = rf"{sequence}-{shot}__layer_layout_layoutMaya_{latest_version}\.usda"

        for fname in os.listdir(latest_path):
            if re.fullmatch(expected_name_pattern, fname, re.IGNORECASE):
                full_path = os.path.join(latest_path, fname)
                print(f"✅ Found latest mayaLayout.usda: {full_path}")
                return full_path

        print("⛔ No matching USD file found in the latest version folder.")
        return None

    def load_usda(self, usda_file, clear_log=True):  # ← paramètre ajouté
        self.usda_file = usda_file
        self.asset_items.clear()
        self.checkbox_widgets.clear()
        self.list_widget.clear()

        if clear_log:
            self.log_box.clear()

        self.log(f"🔍 Parsing: {usda_file}")

        with open(usda_file, "r", encoding="utf-8") as f:
            content = f.read()

        escaped_path = re.escape(BASE_ASSET_PATH.replace("\\", "/"))
        pattern = rf"@{escaped_path}.+?/Export/USD/v\d{{3}}/[^@]+?_USD_v\d{{3}}\.usd[ac]@"
        matches = re.findall(pattern, content, re.IGNORECASE)

        self.log(f"Found {len(matches)} payload(s)")

        added = set()
        for match in matches:
            match_normalized = match.lower()
            if match_normalized in added:
                continue
            added.add(match_normalized)
            item = find_latest_version_path(match)
            if item and item.from_version != item.to_version:
                self.asset_items.append(item)
                self.add_list_item(item)
            else:
                self.log(f"🟰 Skipping (already latest or invalid): {match}")
    def add_list_item(self, item: AssetItem):
        checkbox = QtWidgets.QCheckBox(
            f"{item.original_path}\n➡ v{item.from_version:03d} → v{item.to_version:03d}"
        )
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(
            lambda state, i=item: setattr(i, 'should_update', state == QtCore.Qt.Checked)
        )

        list_item = QtWidgets.QListWidgetItem()
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, checkbox)
        list_item.setSizeHint(checkbox.sizeHint())

        self.checkbox_widgets.append(checkbox)

    def set_all_checkboxes(self, value: bool):
        for cb in self.checkbox_widgets:
            cb.setChecked(value)

    def run_update(self):
        print("yo5")
        if not self.usda_file:
            self.log("⛔ No USDA file selected.")
            return

        # Backup
        backup_path = self.usda_file + ".bak"
        shutil.copy2(self.usda_file, backup_path)
        self.log(f"🗂️ Backup created: {backup_path}")

        # Read and update
        with open(self.usda_file, "r", encoding="utf-8") as f:
            content = f.read()

        changes_made = False

        for item in self.asset_items:
            if item.should_update:
                if item.original_path in content:
                    content = content.replace(item.original_path, item.updated_path)
                    self.log(f"✅ Updated: {item.original_path} → {item.updated_path}")
                    changes_made = True
                else:
                    self.log(f"⚠️ Skipped (not found in file): {item.original_path}")

        if changes_made:
            with open(self.usda_file, "w", encoding="utf-8") as f:
                f.write(content)
            self.log("🎉 All selected payloads successfully updated.")
            
        else:
            self.log("✅ Nothing to update.")

        # Refresh UI
        # Refresh UI
        self.log("🔁 Refreshing asset list...")
        self.load_usda(self.usda_file, clear_log=False)  # ← flag passé à False


def show_usda_updater_in_maya():
    global updater_window
    try:
        updater_window.close()
        updater_window.deleteLater()
    except:
        pass

    updater_window = USDAUpdaterUI(parent=maya_main_window())
    updater_window.show()

# 👉 To launch, run this:
# show_usda_updater_in_maya()

