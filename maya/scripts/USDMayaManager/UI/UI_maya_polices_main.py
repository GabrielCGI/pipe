from importlib import reload
import qtpy.QtWidgets as qt
import qtpy.QtCore as qtc
import qtpy.QtGui as qtg



from ..core import maya_policies
reload(maya_policies)



class UIMainMaya(qt.QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("USD Manager")
        self.resize(720, 560)

        self.core = maya_policies.MayaPolices()
        self.COLOR_LAYER_UNMUTED = qtg.QColor("#ffffff")
        self.COLOR_LAYER_MUTED = qtg.QColor("#374563")
        self.FuncUnloadPayload = {"payloads Lights": self.core.unloadPayloadsLights}

        self.FuncMuteLayer = {"Mute Lighting": self.core.muteLayerLighting, "Mute Anim"  : self.core.muteLayerAnimation, 
                              "Mute Layout"  : self.core.muteLayerLayout,   "Mute Camera": self.core.muteLayerCameras, 
                              "Mute FX CFX"  : self.core.muteLayerFXCFX}



        main_widget = qt.QWidget(self)
        self.setCentralWidget(main_widget)


        main_layout = qt.QVBoxLayout(main_widget)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(2, 2, 2, 2)

        main_layout.addWidget(qt.QLabel("Paramètres"))

        proxy_row = qt.QHBoxLayout()
        self.proxy_combo = qt.QComboBox()
        self.proxy_combo.setMinimumWidth(300)
        self.proxy_combo.currentIndexChanged.connect(self.core.changeProxySelect)
        btn_refresh_proxy = qt.QPushButton("↺")
        btn_refresh_proxy.setFixedWidth(30)
        btn_refresh_proxy.setToolTip("Rafraîchir la liste des proxy shapes")
        btn_refresh_proxy.clicked.connect(self.updateProxyShape)
        proxy_row.addWidget(self.proxy_combo)
        proxy_row.addWidget(btn_refresh_proxy)
        main_layout.addLayout(proxy_row)


        main_layout.addWidget(qt.QLabel(""))


        self.tab_widget = qt.QTabWidget()
        main_layout.addWidget(self.tab_widget)
        self.tab_widget.tabBarClicked.connect(self.updateProxyShape)

        self._simpleOptionsTab()
        self._buildPayloadTab()
        self._muteLayersTab()

        self.updateProxyShape()

    def updateProxyShape(self) -> None:
        self.proxy_combo.blockSignals(True)
        self.proxy_combo.clear()
        shapes = self.core.getListProxyShape()
        if shapes:
            self.proxy_combo.addItems(shapes)
        else:
            self.proxy_combo.addItem("— Aucun proxy shape trouvé —")
        
        self.proxy_combo.blockSignals(False)
        self._updateInterface()
    
    def _updateInterface(self) -> None:
        shapes = self.core.getListProxyShape()
        if not shapes:
            self._stage = None
            self._proxy_shape = None
            self.payloads_tree.clear()
            self.layer_tree.clear()
            return

        self._proxy_shape = self.proxy_combo.currentText()
        self._refreshPayloadUI()
        self._refreshLayerUI()

    def _collectAllItemsTree(self, tree_parse: qt.QTreeWidget) -> list[qt.QTreeWidgetItem]:
        result = []
        def recurse(item: qt.QTreeWidgetItem):
            result.append(item)
            for i in range(item.childCount()):
                recurse(item.child(i))
        
        for i in range(tree_parse.topLevelItemCount()):
            recurse(tree_parse.topLevelItem(i))
        
        return result



    # ------------------ tab avec des settings pré definie pour se simplifier l'utilisation des data ------------------
    def _simpleOptionsTab(self) -> None:
        tab = qt.QWidget()
        layout = qt.QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        
        # ----------------------- system Load Payloads ----------------------------
        name_hide_section = qt.QLabel("Unload / load Payloads")
        layout.addWidget(name_hide_section)

        frame_hide = qt.QFrame(tab)
        frame_hide.setObjectName("cadreInfo")
        layout.addWidget(frame_hide)
        hide_layout = qt.QVBoxLayout(frame_hide)


        hide_light = qt.QCheckBox("Unload all light USD")
        hide_light.setObjectName("payloads Lights")
        hide_light.clicked.connect(lambda: self.checkUnloadPayloads(hide_light))
        hide_layout.addWidget(hide_light)

        # hide_env = qt.QCheckBox("Unload all Environments")
        # hide_env.setObjectName("payloads Environments")
        # hide_env.clicked.connect(lambda: self.checkUnloadPayloads(hide_env))
        # hide_layout.addWidget(hide_env)

        # hide_char = qt.QCheckBox("Unload all Characters")
        # hide_char.setObjectName("payloads Characters")
        # hide_char.clicked.connect(lambda: self.checkUnloadPayloads(hide_char))
        # hide_layout.addWidget(hide_char)

        # hide_props = qt.QCheckBox("Unload all Props")
        # hide_props.setObjectName("payloads Props")
        # hide_props.clicked.connect(lambda: self.checkUnloadPayloads(hide_props))
        # hide_layout.addWidget(hide_props)

        # hide_sets = qt.QCheckBox("Unload all Kits")
        # hide_sets.setObjectName("payloads Sets")
        # hide_sets.clicked.connect(lambda: self.checkUnloadPayloads(hide_sets))
        # hide_layout.addWidget(hide_sets)


        dd_env = CheckboxDropdown("Environments", [pay.GetPath().pathString for pay in self.core.traverseAllPayloadAtPath("/assets/environments", True)], self.core)
        hide_layout.addWidget(dd_env)
        
        dd_env = CheckboxDropdown("Characters", [pay.GetPath().pathString for pay in self.core.traverseAllPayloadAtPath("/assets/characters")], self.core)
        hide_layout.addWidget(dd_env)
        
        dd_env = CheckboxDropdown("Props", [pay.GetPath().pathString for pay in self.core.traverseAllPayloadAtPath("/assets/props")], self.core)
        hide_layout.addWidget(dd_env)
        
        dd_env = CheckboxDropdown("Kits", [pay.GetPath().pathString for pay in self.core.traverseAllPayloadAtPath("/assets/kits")], self.core)
        hide_layout.addWidget(dd_env)


        # ----------------------- system Mute Layer In Stake USD ----------------------------
        name_hide_section = qt.QLabel("Mute / UnMute Layer")
        layout.addWidget(name_hide_section)

        frame_mute = qt.QFrame(tab)
        frame_mute.setObjectName("cadreInfo")
        mute_layout = qt.QVBoxLayout(frame_mute)

        layout.addWidget(frame_mute)

        layer_lgt = qt.QCheckBox("Mute Layers Lighting")
        layer_lgt.setObjectName("Mute Lighting")
        layer_lgt.clicked.connect(lambda: self.checkMuteLayers(layer_lgt))
        mute_layout.addWidget(layer_lgt)

        layer_anim = qt.QCheckBox("Mute Layers Anim")
        layer_anim.setObjectName("Mute Anim")
        layer_anim.clicked.connect(lambda: self.checkMuteLayers(layer_anim))
        mute_layout.addWidget(layer_anim)

        layer_lay = qt.QCheckBox("Mute Layers Layout")
        layer_lay.setObjectName("Mute Layout")
        layer_lay.clicked.connect(lambda: self.checkMuteLayers(layer_lay))
        mute_layout.addWidget(layer_lay)

        layer_cam = qt.QCheckBox("Mute Layers Camera")
        layer_cam.setObjectName("Mute Camera")
        layer_cam.clicked.connect(lambda: self.checkMuteLayers(layer_cam))
        mute_layout.addWidget(layer_cam)

        layer_FXCFX = qt.QCheckBox("Mute Layers FX CFX")
        layer_FXCFX.setObjectName("Mute FX CFX")
        layer_FXCFX.clicked.connect(lambda: self.checkMuteLayers(layer_FXCFX))
        mute_layout.addWidget(layer_FXCFX)

        layout.addStretch()


        self.tab_widget.addTab(tab, "Simple Options")

    def checkUnloadPayloads(self, btn: qt.QCheckBox) -> None:
        self.FuncUnloadPayload[btn.objectName()](btn.isChecked())
    
    def checkMuteLayers(self, btn: qt.QCheckBox) -> None:
        self.FuncMuteLayer[btn.objectName()](btn.isChecked())




    # ------------------ tab avec toute les info des layer charger ou non ------------------
    def _muteLayersTab(self) -> None:
        tab = qt.QWidget()
        layout = qt.QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)


        # Liste des layers
        self.layer_tree = qt.QTreeWidget()
        self.layer_tree.setColumnCount(2)
        self.layer_tree.setHeaderLabels(["Layer", "État"])
        self.layer_tree.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)
        # self.layer_tree.header().setSectionResizeMode(0, qt.QHeaderView.Stretch)
        self.layer_tree.header().resizeSection(1, 110)
        layout.addWidget(self.layer_tree)


        # Statut layers
        self.lbl_layer_status = qt.QLabel("0 / 0 layer(s) muté(s)")
        layout.addWidget(self.lbl_layer_status)


        # Boutons
        btn_layout = qt.QHBoxLayout()
        layout.addLayout(btn_layout)

        btn_mute_sel = qt.QPushButton("mute Selection")
        btn_mute_sel.clicked.connect(self._muteItemSelected)
        btn_layout.addWidget(btn_mute_sel)

        btn_unmute_sel = qt.QPushButton("Unmute Selection")
        btn_unmute_sel.clicked.connect(self._unmuteItemSelected)
        btn_layout.addWidget(btn_unmute_sel)

        btn_layout.addStretch()

        btn_mute_all = qt.QPushButton("Tout muter")
        btn_mute_all.clicked.connect(self._muteAllItem)
        btn_layout.addWidget(btn_mute_all)

        btn_unmute_all = qt.QPushButton("Tout démuter")
        btn_unmute_all.clicked.connect(self._unmuteAllItem)
        btn_layout.addWidget(btn_unmute_all)

        btn_refresh_layers = qt.QPushButton("Rafraîchir")
        btn_refresh_layers.clicked.connect(self._refreshLayerUI)
        btn_layout.addWidget(btn_refresh_layers)


        self.tab_widget.addTab(tab, "Layers")

    def _refreshLayerUI(self) -> None:
        self.layer_tree.clear()
        if not self.core.stage:
            self._updateViewLayerMute()
            return

        root_layer = self.core.stage.GetRootLayer()
        if root_layer:
            root_item = self._addItemInTreeLayer(root_layer.identifier)
            self.layer_tree.addTopLevelItem(root_item)
            self._populateLayerTree(root_item, root_layer)

        self.layer_tree.expandAll()
        self._updateViewLayerMute()

    def _addItemInTreeLayer(self, layer_path: str) -> qt.QTreeWidgetItem:
        item = qt.QTreeWidgetItem()
        layer_path = layer_path.replace("\\", "/")
        name = layer_path.split("/")[-1]
        item.setText(0, name)
        item.setToolTip(0, layer_path)
        item.setData(0, qtc.Qt.UserRole, layer_path)
        
        if self.core.stage.IsLayerMuted(layer_path):
            item.setText(1, "◼ Muté")
            item.setForeground(0, qtg.QBrush(self.COLOR_LAYER_MUTED))
            item.setForeground(1, qtg.QBrush(self.COLOR_LAYER_MUTED))
        else:
            item.setText(1, "◻ Actif")
            item.setForeground(0, qtg.QBrush(self.COLOR_LAYER_UNMUTED))
            item.setForeground(1, qtg.QBrush(self.COLOR_LAYER_UNMUTED))
        
        return item
    
    def _populateLayerTree(self, parent_item: qt.QTreeWidgetItem, layer) -> None:
        for sub_path in layer.subLayerPaths:
            sub_layer = self.core.getSublayer(layer, sub_path)
            if not sub_layer:
                continue

            item = self._addItemInTreeLayer(sub_layer.identifier)
            parent_item.addChild(item)

            self._populateLayerTree(item, sub_layer)

    def _muteItemSelected(self) -> None:
        to_mute = [item.data(0, qtc.Qt.UserRole) for item in self.layer_tree.selectedItems()]
        self.core.muteLayers(to_mute)
        self._refreshLayerUI()

    def _unmuteItemSelected(self) -> None:
        to_mute = [item.data(0, qtc.Qt.UserRole) for item in self.layer_tree.selectedItems()]
        self.core.unmuteLayers(to_mute)
        self._refreshLayerUI()
    
    def _muteAllItem(self) -> None:
        all_item = self._collectAllItemsTree(self.layer_tree)
        to_mute = [item.data(0, qtc.Qt.UserRole) for item in all_item]
        self.core.muteLayers(to_mute)
        self._refreshLayerUI()

    def _unmuteAllItem(self) -> None:
        all_item = self._collectAllItemsTree(self.layer_tree)
        to_mute = [item.data(0, qtc.Qt.UserRole) for item in all_item]
        self.core.unmuteLayers(to_mute)
        self._refreshLayerUI()

    def _updateViewLayerMute(self) -> None:
        all_items = self._collectAllItemsTree(self.layer_tree)
        total = len(all_items)
        muted = sum(1 for it in all_items if "Muté" in it.text(1))
        self.lbl_layer_status.setText(f"{muted} / {total} layer(s) muté(s)")
    



    # ------------------ tab avec tout les data des chargement des payloads ------------------
    def _buildPayloadTab(self) -> None:
        tab = qt.QWidget()
        layout = qt.QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Filtre + expand/collapse
        filter_layout = qt.QHBoxLayout()
        self.filter_edit = qt.QLineEdit()
        self.filter_edit.setPlaceholderText("Filtrer par nom de prim…")
        self.filter_edit.textChanged.connect(self._applyFilter)
        btn_expand = qt.QPushButton("Tout déplier")
        btn_expand.setFixedWidth(100)
        btn_collapse = qt.QPushButton("Tout replier")
        btn_collapse.setFixedWidth(100)
        filter_layout.addWidget(qt.QLabel("Filtre :"))
        filter_layout.addWidget(self.filter_edit)
        filter_layout.addWidget(btn_expand)
        filter_layout.addWidget(btn_collapse)
        layout.addLayout(filter_layout)

        # Arbre
        self.payloads_tree = qt.QTreeWidget()
        self.payloads_tree.setColumnCount(2)
        self.payloads_tree.setHeaderLabels(["Layer", "État"])
        self.payloads_tree.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)
        self.payloads_tree.clicked.connect(self.selectPrim)
        # self.layer_tree.header().setSectionResizeMode(0, qt.QHeaderView.Stretch)
        self.payloads_tree.header().resizeSection(1, 110)
        layout.addWidget(self.payloads_tree)

        btn_expand.clicked.connect(self.payloads_tree.expandAll)
        btn_collapse.clicked.connect(self.payloads_tree.collapseAll)

        # Statut
        self.lbl_status = qt.QLabel("0 / 0 payload(s) chargé(s)")
        layout.addWidget(self.lbl_status)

        # Boutons
        btn_layout = qt.QHBoxLayout()

        self.btn_load_sel = qt.QPushButton("Charger la sélection")
        self.btn_load_sel.clicked.connect(self.loadItemSelect)

        self.btn_unload_sel = qt.QPushButton("Décharger la sélection")
        self.btn_unload_sel.clicked.connect(self.unloadItemSelect)

        self.btn_load_all = qt.QPushButton("Tout charger")
        self.btn_load_all.clicked.connect(self._loadAllItem)

        self.btn_unload_all = qt.QPushButton("Tout décharger")
        self.btn_unload_all.clicked.connect(self._unloadAllItem)

        self.btn_refresh = qt.QPushButton("Rafraîchir")
        self.btn_refresh.clicked.connect(self._refreshPayloadUI)

        btn_layout.addWidget(self.btn_load_sel)
        btn_layout.addWidget(self.btn_unload_sel)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_load_all)
        btn_layout.addWidget(self.btn_unload_all)
        btn_layout.addWidget(self.btn_refresh)
        layout.addLayout(btn_layout)

        self.tab_widget.addTab(tab, "Payloads")

    def _refreshPayloadUI(self) -> None:
        self.payloads_tree.clear()
        if not self.core.stage:
            self._updateViewPayloadsUnload()
            return

        node_map = {}

        def ensure_ancestors(path):
            path_str = str(path)
            if path_str in ('', '/') or path in node_map:
                return
            parent_path = path.GetParentPath()
            ensure_ancestors(parent_path)

            item = qt.QTreeWidgetItem()
            item.setText(0, path.name)
            item.setToolTip(0, path_str)
            node_map[path] = item

            if parent_path in node_map:
                node_map[parent_path].addChild(item)
            else:
                self.payloads_tree.addTopLevelItem(item)

        for prim in self.core.getPayloadPrims():
            path = prim.GetPath()
            ensure_ancestors(path.GetParentPath())

            item = PayloadItem(path, prim.IsLoaded())
            node_map[path] = item

            parent_path = path.GetParentPath()
            if parent_path in node_map:
                node_map[parent_path].addChild(item)
            else:
                self.payloads_tree.addTopLevelItem(item)

        self.payloads_tree.expandAll()
        self._applyFilter(self.filter_edit.text())
        self._updateViewPayloadsUnload()
    
    def _applyFilter(self, text: str) -> None:
        text = text.lower().strip()
        for i in range(self.payloads_tree.topLevelItemCount()):
            self._filterItem(self.payloads_tree.topLevelItem(i), text)
    
    def _filterItem(self, item: qt.QTreeWidgetItem, text: str) -> bool:
        self_matches = (not text) or (text in item.text(0).lower()) or (text in item.toolTip(0).lower())
        child_visible = False
        for i in range(item.childCount()):
            if self._filterItem(item.child(i), text):
                child_visible = True

        visible = self_matches or child_visible
        item.setHidden(not visible)
        # Déplier automatiquement si un descendant correspond
        if child_visible and text:
            item.setExpanded(True)
        
        return visible

    def _addItemInTreePayload(self, prim_path: str) -> qt.QTreeWidgetItem:
        item = qt.QTreeWidgetItem()
        item.setText(0, prim_path)
        item.setData(0, qtc.Qt.UserRole, prim_path)

        return item

    def unloadItemSelect(self) -> None:
        paths = [str(n.sdf_path) for n in self.payloads_tree.selectedItems() if isinstance(n, PayloadItem)]
        self.core.unloadPayloads(paths)
        self._refreshPayloadUI()

    def loadItemSelect(self) -> None:
        paths = [str(n.sdf_path) for n in self.payloads_tree.selectedItems() if isinstance(n, PayloadItem)]
        self.core.loadPayloads(paths)
        self._refreshPayloadUI()

    def _unloadAllItem(self) -> None:
        paths = [str(n.sdf_path) for n in self._collectAllItemsTree(self.payloads_tree) if isinstance(n, PayloadItem)]
        self.core.unloadPayloads(paths)
        self._refreshPayloadUI()

    def _loadAllItem(self) -> None:
        paths = [str(n.sdf_path) for n in self._collectAllItemsTree(self.payloads_tree) if isinstance(n, PayloadItem)]
        self.core.loadPayloads(paths)
        self._refreshPayloadUI()

    def _updateViewPayloadsUnload(self) -> None:
        all_nodes = [n for n in self._collectAllItemsTree(self.payloads_tree) if isinstance(n, PayloadItem)]
        loaded = sum(1 for n in all_nodes if n.is_loaded)
        self.lbl_status.setText(f"{loaded} / {len(all_nodes)} payload(s) chargé(s)")

    def selectPrim(self) -> None:
        paths = [str(n.sdf_path) for n in self.payloads_tree.selectedItems() if isinstance(n, PayloadItem)]
        self.core.selectPrim(paths)
        pass





class PrimItem(qt.QTreeWidgetItem):
    COLOR_NORMAL = qtg.QColor("#cccccc")
    def __init__(self, sdf_path):
        super().__init__()
        self.sdf_path = sdf_path
        self.setText(0, sdf_path.name or str(sdf_path))
        self.setForeground(0, qtg.QBrush(self.COLOR_NORMAL))
        self.setToolTip(0, str(sdf_path))

class PayloadItem(PrimItem):
    """Nœud portant un payload — affiche l'état chargé/déchargé."""

    COLOR_LOADED   = qtg.QColor("#4CAF50")
    COLOR_UNLOADED = qtg.QColor("#F44336")
    FONT_BOLD = None  # initialisé au premier usage

    def __init__(self, sdf_path, is_loaded):
        super().__init__(sdf_path)
        self.is_loaded = is_loaded
        self._apply_style()

    def _apply_style(self):
        # Nom en gras pour distinguer les payloads
        if PayloadItem.FONT_BOLD is None:
            font = self.font(0)
            font.setBold(True)
            PayloadItem.FONT_BOLD = font
        self.setFont(0, PayloadItem.FONT_BOLD)

        label = "● Chargé" if self.is_loaded else "○ Déchargé"
        color = self.COLOR_LOADED if self.is_loaded else self.COLOR_UNLOADED
        self.setText(1, label)
        self.setForeground(0, qtg.QBrush(color))
        self.setForeground(1, qtg.QBrush(color))

    def set_loaded(self, value):
        self.is_loaded = value
        self._apply_style()





class CheckboxDropdown(qt.QWidget):
    def __init__(self, title: str, items: list, core: maya_policies.MayaPolices):
        super().__init__()
        self._expanded = False
        self.core = core


        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)


        # --- Ligne header (flèche + titre) ---
        self._header = qt.QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(False)
        self._header.clicked.connect(self._toggle)
        self._title = title
        self._header.setStyleSheet("text-align: left;")
        layout.addWidget(self._header)


        # --- Container des checkboxes (caché par défaut) ---
        self._container = qt.QFrame()
        container_layout = qt.QVBoxLayout(self._container)
        container_layout.setContentsMargins(12, 6, 12, 6)
        container_layout.setSpacing(4)

        for item in items:
            ligne = qt.QHBoxLayout()
            container_layout.addLayout(ligne)

            prim = self.core.stage.GetPrimAtPath(item)
            cb = qt.QCheckBox(item.split("/")[-1])
            cb.setChecked(not prim.IsLoaded())
            cb.clicked.connect(lambda i= item, c=cb: self._LoadPayload(i))
            cb.setStyleSheet("color: #cccccc; padding: 2px 0;")
            ligne.addWidget(cb)

            ligne.addStretch()

            btn = qt.QPushButton("select")
            btn.clicked.connect(lambda i= item, c=cb: self._selectPrim(i))
            ligne.addWidget(btn)


        self._container.setVisible(False)
        layout.addWidget(self._container)
        
        self._update_header_text(title)

    def _update_header_text(self, title):
        arrow = "v" if self._expanded else ">"
        self._header.setText(f"  {arrow} Unload all {title} USD")

    def _toggle(self):
        self._expanded = not self._expanded
        self._container.setVisible(self._expanded)
        self._update_header_text(self._title)

    def _LoadPayload(self, item_path: str):
        prim = self.core.stage.GetPrimAtPath(item_path)
        if prim.IsLoaded():
            self.core.unloadPayloads([item_path])
        else:
            self.core.loadPayloads([item_path])
    
    def _selectPrim(self, prim_path):
        self.core.selectPrim([prim_path])