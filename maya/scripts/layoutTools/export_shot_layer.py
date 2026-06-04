import qtpy.QtWidgets as qt
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg
import mayaUsd.lib as mayaUsdLib #type: ignore
import maya.cmds as cmds
from pxr import Sdf, Usd, UsdUtils
import re




class ExportAsLayer(qt.QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Export data as Layer USD")
        self.resize(800, 400)


        mw = qt.QWidget()
        self.setCentralWidget(mw)

        container_main = qt.QVBoxLayout(mw)

        cc_lds = qt.QWidget()
        cc_lds.setFixedHeight(50)
        container_main.addWidget(cc_lds)

        
        ligne_data_shot = qt.QHBoxLayout(cc_lds)
        ligne_data_shot.setContentsMargins(0, 0, 0, 0)

        shot_e = qt.QLabel("shot to export: ")
        shot_e.setMaximumWidth(80)
        ligne_data_shot.addWidget(shot_e)

        self.all_shot_combo = qt.QComboBox()
        self.all_shot_combo.addItems(self._findAllShot())
        self.all_shot_combo.setCurrentText(self._curentShots())
        self.all_shot_combo.currentTextChanged.connect(self._refreshFramerange)
        self.all_shot_combo.setFixedWidth(200)
        ligne_data_shot.addWidget(self.all_shot_combo)

        self.start_time_shot = qt.QLabel("frame start: 1001")
        self.start_time_shot.setFixedWidth(150)
        ligne_data_shot.addWidget(self.start_time_shot)

        self.end_time_shot = qt.QLabel("frame end: 1002")
        self.end_time_shot.setFixedWidth(150)
        ligne_data_shot.addWidget(self.end_time_shot)

        ligne_data_shot.addStretch()



        separator(container_main)



        #-------------------------- coupé la fenêtre en deux morceau gauche USD est à droite Data Maya --------------------------
        split_windows = qt.QHBoxLayout()
        container_main.addLayout(split_windows)

        #--------------------- section USD ---------------------
        section_USD = qt.QVBoxLayout()
        split_windows.addLayout(section_USD)
        
        data_USD = qt.QLabel("Export USD Layer")
        data_USD.setStyleSheet("font-size: 20px;")
        data_USD.setAlignment(qtc.Qt.AlignCenter)
        data_USD.setFixedHeight(40)
        section_USD.addWidget(data_USD)

        separator(section_USD)

        self.all_proxyShape = qt.QComboBox()
        self.all_proxyShape.addItems(self._findUSDProxyShape())
        self.all_proxyShape.currentTextChanged.connect(self._buildTree)
        section_USD.addWidget(self.all_proxyShape)

        self.implicit = qt.QCheckBox("Flatten implicit all Layer")
        self.implicit.setChecked(True)
        self.implicit.toggled.connect(self._activeQTree)
        section_USD.addWidget(self.implicit)

        self.view_layer = qt.QTreeWidget()
        self.view_layer.setHeaderLabel("all USD Layer")
        self.view_layer.setDisabled(True)
        self.view_layer.setMaximumWidth(380)
        section_USD.addWidget(self.view_layer)

        section_USD.addStretch()

        export_USD = qt.QPushButton("export Layout")
        export_USD.clicked.connect(self._exportUSDLayer)
        section_USD.addWidget(export_USD)


        separator(split_windows, True)


        #------------------ section Data Maya ------------------
        section_DataMaya = qt.QVBoxLayout()
        split_windows.addLayout(section_DataMaya)

        data_m = qt.QLabel("Export Data Maya")
        data_m.setStyleSheet("font-size: 20px;")
        data_m.setAlignment(qtc.Qt.AlignCenter)
        data_m.setFixedHeight(40)
        section_DataMaya.addWidget(data_m)

        separator(section_DataMaya)

        select_geo = qt.QPushButton("show select data want you Export")
        select_geo.clicked.connect(self._selectAnimation)
        section_DataMaya.addWidget(select_geo)

        self.auto_detect = qt.QCheckBox("auto detect data want you Export")
        self.auto_detect.setChecked(True)
        section_DataMaya.addWidget(self.auto_detect)

        self.export_cam = qt.QCheckBox("Export Camera")
        section_DataMaya.addWidget(self.export_cam)

        section_DataMaya.addStretch()

        export_data = qt.QPushButton("export Animation")
        export_data.clicked.connect(self.exportDataMaya)
        section_DataMaya.addWidget(export_data)


        # execute
        self._refreshFramerange(self.all_shot_combo.currentText())
        self._buildTree(self.all_proxyShape.currentText())


    # ---------------- methode general ----------------
    def _findAllShot(self) -> list[str]:
        return cmds.sequenceManager(lsh=True) or []

    def _curentShots(self) -> str:
        return cmds.sequenceManager(q=True, cs=True)

    def _refreshFramerange(self, text: str) -> tuple[int, int]:
        start = str(int(cmds.shot(text, q=True, st=True)))
        end = str(int(cmds.shot(text, q=True, et=True)))

        self.start_time_shot.setText("frame start: "+start)
        self.end_time_shot.setText("frame end: "+end)



    # ---------------- section USD methode ----------------
    def _findUSDProxyShape(self) -> list[str]:
        return cmds.ls(type="mayaUsdProxyShape", long=True) or []
    
    def _buildTree(self, shape: str):
        if not shape:
            return
        prim = mayaUsdLib.GetPrim(shape)
        if not prim or not prim.IsValid():
            return
        
        self.view_layer.clear()

        session_layer = prim.GetStage().GetSessionLayer()
        session_item = qt.QTreeWidgetItem([session_layer.identifier])
        self.view_layer.addTopLevelItem(session_item)
        self._addSubLayers(session_layer, session_item)
        
        root_layer = prim.GetStage().GetRootLayer()
        root_item = qt.QTreeWidgetItem([root_layer.identifier])
        self.view_layer.addTopLevelItem(root_item)
        self._addSubLayers(root_layer, root_item)

        self.view_layer.expandAll()

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
    
    def _activeQTree(self, value: bool) -> None:
        self.view_layer.setDisabled(value)
        self.view_layer.clearSelection()


    def _layerAutoDetect(self) -> list[Sdf.Layer]:
        return []

    def _layerSelected(self) -> list[Sdf.Layer]:
        return [i.text(0) for i in self.view_layer.selectedItems()]

    def _exportUSDLayer(self) -> None:
        str_layers = []
        if self.implicit.isChecked():
            str_layers = self._layerAutoDetect()
        else:
            str_layers = self._layerSelected()

        if not str_layers:
            return

        stage = Usd.Stage.CreateInMemory()
        session_layer = stage.GetSessionLayer()
        for lay_str in str_layers:
            layer = Sdf.Layer.Find(lay_str)
            if layer:
                session_layer.subLayerPaths.append(layer.identifier)

        new_layer = UsdUtils.FlattenLayerStack(stage)
        new_layer.Export(r"D:\toto\Export_usd_test\test.usda")
        print("export USD")




    # ---------------- section data maya methode ----------------
    def dd(self):
        pass

    def _selectAnimation(self) -> list[str]:
        import maya.cmds as cmds

        nodes_find = set()
        for parent in ["assets|sets", "assets|characters", "assets|props", "assets|kits"]:
            if not cmds.objExists(parent):
                continue

            hierarchy_nodes = cmds.listRelatives(parent, allDescendents=True, s=False, f=True)
            if hierarchy_nodes is None:
                continue
            
            for node in hierarchy_nodes:
                if ":rig|" in node:
                    continue
                elif node.endswith(":geo"):
                    nodes_find.add(node)
        
        if not nodes_find:
            return self.PrintMSG('no geo to export, nice have: "assets|sets", "assets|characters", "assets|props", "assets|kits"')
        
        cmds.select(nodes_find)

        return nodes_find


    def exportDataMaya(self):
        print("export maya")





    
def separator( layout: qt.QVBoxLayout, vert=False):
    separator = qt.QFrame()
    separator.setFrameShape(qt.QFrame.HLine if not vert else qt.QFrame.VLine)
    separator.setFrameShadow(qt.QFrame.Sunken)
    separator.setStyleSheet("background-color: #555555;")
    separator.setFixedHeight(2) if not vert else separator.setFixedWidth(2)
    layout.addWidget(separator)