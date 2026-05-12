import qtpy.QtWidgets as qt


import mayaUsd.lib as mayaUsdLib #type: ignore
from pathlib import Path
import maya.cmds as cmds
from pxr import Usd, Sdf
import PrismInit #type: ignore
import re
import os




class EditHierarchy(qt.QDialog):
    def __init__(self, parent = None):
        super(EditHierarchy, self).__init__(parent)
        self.resize(800, 500)
        self.setWindowTitle("USD Edit Hierarchy")
        self.core = PrismInit.pcore


        container_main = qt.QVBoxLayout(self)
        container_main.setContentsMargins(14, 12, 14, 12)
        container_main.setSpacing(10)

        # --- Title ---
        title = qt.QLabel("USD Edit Hierarchy")
        title.setObjectName("title")
        container_main.addWidget(title)

        sep = qt.QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(qt.QFrame.HLine)
        container_main.addWidget(sep)

        # --- Buttons ---
        btns = qt.QHBoxLayout()
        btns.setSpacing(8)

        edit_layer = qt.QPushButton("Edit Layer")
        edit_layer.setObjectName("btn_edit")
        edit_layer.pressed.connect(self.makeEditLayer)
        btns.addWidget(edit_layer)

        save_layer = qt.QPushButton("Save Layer")
        save_layer.setObjectName("btn_save")
        save_layer.pressed.connect(self.saveEditLayer)
        btns.addWidget(save_layer)

        reloadUI = qt.QPushButton("Reload Stack USD")
        reloadUI.setObjectName("btn_reload")
        reloadUI.pressed.connect(self.ReloadUI)
        btns.addWidget(reloadUI)

        btns.addStretch()
        container_main.addLayout(btns)

        # --- Edit banner ---
        self.edit_banner = qt.QLabel("⚠  Active edition mode - changes are in progress in the work layer. Save when you have finished.")
        self.edit_banner.setWordWrap(True)
        
        self.edit_banner.setVisible(False)
        container_main.addWidget(self.edit_banner)

        # --- Tree ---
        self.tree = qt.QTreeWidget()
        self.tree.setHeaderLabel("USD Layer Stack")
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        container_main.addWidget(self.tree)

        self.applyStyleSheet()
        self.ReloadUI()


    def buildTree(self, stage):
        root_layer = stage.GetRootLayer()
        root_item = qt.QTreeWidgetItem([root_layer.identifier])
        self.tree.addTopLevelItem(root_item)

        self._addSubLayers(root_layer, root_item)

        self.tree.expandAll()

    def _addSubLayers(self, layer, parent_item):
        for sub_path in layer.subLayerPaths:
            name_layer = Sdf.ComputeAssetPathRelativeToLayer(layer, sub_path)
            sub_layer = Sdf.Layer.Find(name_layer)
            if not sub_layer:
                continue

            item = qt.QTreeWidgetItem([sub_layer.identifier])
            parent_item.addChild(item)

            # récursion
            self._addSubLayers(sub_layer, item)

    def ReloadUI(self):
        self.layer_to_sreach = None
        self.work_layer = None
        self.layer_usd = None
        self.layer_path = None
        self.tree.clear()

        list_usd_shape = cmds.ls(sl=True, type="mayaUsdProxyShape", long=True) or []
        if not list_usd_shape:
            qt.QMessageBox.warning(self, "selection not good", "select a USDShape")
            return

        prim = mayaUsdLib.GetPrim(list_usd_shape[0])
        self.usd_Shape = list_usd_shape[0]
        self.stage = None
        if prim and prim.IsValid():
            self.stage: Usd.Stage = prim.GetStage()
        
        if self.stage:
            self.buildTree(self.stage)
    


    def makeEditLayer(self):
        if self.stage is None:
            return
        self.layer_to_sreach = self.tree.currentItem().text(0)

        all_layer = self.stage.GetLayerStack()

        for layer in all_layer:
            if layer.identifier.endswith(":work"):
                self.work_layer = layer

            elif self.layer_to_sreach == layer.identifier:
                self.layer_usd = layer
                self.layer_path = layer.identifier
        
        data_work = self.work_layer.ExportToString()
        if data_work != "#sdf 1.4.32\n\n":
            result = qt.QMessageBox.question(self, "Confirmation", "Layer work is not clear! Do you want to overwrite what is in the layer work?", qt.QMessageBox.Yes | qt.QMessageBox.No, qt.QMessageBox.No)
            if result == qt.QMessageBox.No:
                return

        print(self.layer_usd, "layer to copie")
        data_layer = self.layer_usd.ExportToString()
        lines = data_layer.splitlines()
        if lines and lines[0].startswith("#usda 1.0"):
            lines[0] = lines[0].replace( "#usda 1.0","#sdf 1.4.32")

        data_ready = "\n".join(lines)

        print(self.work_layer, "dans ce layer ")
        try:
            self.work_layer.ImportFromString(data_ready)
            self.edit_banner.setVisible(True)
            qt.QMessageBox.information(self, "nice", "Copy finish you can edit your hearchie")
        except Exception as e:
            qt.QMessageBox.warning(self, "pas nice", "Error when copying the layer\n" + str(e))
            

    def saveEditLayer(self):
        folder = str(Path(self.layer_path).parent.parent)
        version = sorted(os.listdir(folder))
        if not version:
            version = ["v000"]
        version = str(int(version[-1][1:]) + 1 ).zfill(3)

        new_path = re.sub(r"v(\d+)", "v" + version, self.layer_path)
        self.create_new_version(new_path, self.core)

        self.edit_banner.setVisible(False)
        print(self.work_layer, "layer to export")
        self.work_layer.Export(new_path)

        self.unloadUsdMemorie()



        if self.usd_Shape:
            parent_grp = cmds.listRelatives(self.usd_Shape, p=True) or []
            if parent_grp:
                cmds.delete(parent_grp)
        
        plugin_usd = self.core.getPlugin("USD").api

        path_scene = self.core.getCurrentFileName()
        entity = self.core.getScenefileData(path_scene)
        layer_USD_path = plugin_usd.getLatestEntityUsdPath(entity)
        self.test = plugin_usd.importUsd(layer_USD_path, False)

        new_layer = Sdf.Layer.Find(new_path)
        if new_layer:
            new_layer.Reload(force=True)
            qt.QMessageBox.information(self, "nice", "Publish et import de la stack réussie")

        del new_layer

    def unloadUsdMemorie(self):
        del self.work_layer
        del self.layer_usd
        del self.stage

        self.work_layer = None
        self.layer_usd = None
        self.stage = None


    def create_new_version(self, layer, core):
        project_path = Path(core.projectPath)
        project_offset = len(project_path.parts)
        usd_api = core.getPlugin("USD").api

        layer_path = Path(layer)
        path_scene = core.getCurrentFileName()
        entity = core.getScenefileData(path_scene)

        layer_directory = layer_path.parts[project_offset + 5]
        if layer_directory == "USD":
            _, new_version_path = usd_api.createEntityUsd(entity, allowAddLayers=False)
        else:
            layer_directory = layer_directory.split("_")
            departement = layer_directory[-2]
            sublayer = layer_directory[-1]
            if sublayer == "master":
                new_version_path = usd_api.createDepartmentLayerForEntity(
                    entity, departement
                )
            else:
                new_version_path = usd_api.createSublayerLayerForDepartment(
                    entity, departement, sublayer
                )
        return new_version_path
    

    def applyStyleSheet(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel#title {
                font-size: 15px;
                font-weight: bold;
                color: #c8a96e;
                padding: 6px 0px;
            }
            QFrame#separator {
                background-color: #444;
                max-height: 1px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 18px;
                font-size: 12px;
                font-weight: bold;
                min-width: 110px;
            }
            QPushButton#btn_edit {
                background-color: #3a6ea8;
                color: #ffffff;
                border: 1px solid #4a80c0;
            }
            QPushButton#btn_edit:hover {
                background-color: #4a80c0;
            }
            QPushButton#btn_edit:pressed {
                background-color: #2a5a90;
            }
            QPushButton#btn_save {
                background-color: #3a8a4a;
                color: #ffffff;
                border: 1px solid #4aa05a;
            }
            QPushButton#btn_save:hover {
                background-color: #4aa05a;
            }
            QPushButton#btn_save:pressed {
                background-color: #2a7038;
            }
            QPushButton#btn_reload {
                background-color: #555555;
                color: #dddddd;
                border: 1px solid #666666;
            }
            QPushButton#btn_reload:hover {
                background-color: #666666;
            }
            QPushButton#btn_reload:pressed {
                background-color: #444444;
            }
            QTreeWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                color: #d0d0d0;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 12px;
            }
            QTreeWidget::item:selected {
                background-color: #3a6ea8;
                color: #ffffff;
            }
            QTreeWidget::item:hover {
                background-color: #333a42;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #c8a96e;
                font-weight: bold;
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid #555;
            }
        """)
    
        self.edit_banner.setStyleSheet("""
            QLabel {
                background-color: #7a4a00;
                color: #ffcc55;
                border: 1px solid #ffaa00;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }
        """)