import qtpy.QtWidgets as qt
from pathlib import Path
import random
import json
import os



DATA_PARSE = os.path.join(os.path.dirname(__file__), "configs", "configs_plugin.json")


class CustomExportUI():
    def __init__(self, state):
        if state.className != "Export" and state.className != "USD Export":
            return
        
        self.state = state
        self.visibilityWidget = True


        self.all_settings = qt.QPushButton("Show All Settings")
        self.all_settings.clicked.connect(self.setVisibilityWidget)
        self.state.verticalLayout.insertWidget(0, self.all_settings)
        self.customSheet(self.all_settings)


        # ------------------------------- ajouter le bouton select Auto dans l'interface prism ----------------------
        qt_lay_horizontal = qt.QHBoxLayout()
        self.state.b_add.setMaximumWidth(85)
        qt_lay_horizontal.addWidget(self.state.b_add)
        self.state.verticalLayout_3.addLayout(qt_lay_horizontal)

        qt_btn_autoSelect = qt.QPushButton("Select Auto")
        self.customSheet(qt_btn_autoSelect)
        qt_lay_horizontal.addWidget(qt_btn_autoSelect)
        

        # ------------------------------- effectuer des operations suivant le state ----------------------
        # self.layout_shot_plus_10 = qt.QHBoxLayout()
        # self.layout_shot_plus_10.setContentsMargins(10, 0, 10, 0)
        if self.state.className == "USD Export":
            if os.getlogin() not in self.getUserAcess("user_show_parameter") and "all" not in self.getUserAcess("user_show_parameter"):
                self.setVisibilityWidget()
            # layout = self.state.gb_settings.layout()
            # layout.insertLayout(2, self.layout_shot_plus_10)
            qt_btn_autoSelect.clicked.connect(lambda nul: self.findGoodMethodeUSD())

        elif self.state.className == "Export":
            # layout = self.state.gb_export.layout()
            # layout.insertLayout(5, self.layout_shot_plus_10)
            qt_btn_autoSelect.clicked.connect(lambda nul: self.findGoodMethode())


        # -------------------- ajouter le petit layout pour exporter les frame avec +10 et -10 --------------------
        

        # self.state.Illo_l_frame_plus_10 = qt.QLabel("Shot + 10")
        # self.layout_shot_plus_10.addWidget(self.state.Illo_l_frame_plus_10)
        # self.state.Illo_spin_frame_plus_10 = qt.QSpinBox()
        # self.state.Illo_spin_frame_plus_10.setRange(1, 9000)
        # self.state.Illo_spin_frame_plus_10.setValue(1)
        

        # self.layout_shot_plus_10.addWidget(self.state.Illo_spin_frame_plus_10)
        # self.showShotPlus10(self.state.cb_rangeType.currentIndex())
        # self.state.cb_rangeType.currentIndexChanged.connect(self.showShotPlus10)


    #------------------------ DEBUG ligne -----------------------
    # appliquer une couleur sur les different widget pour faciliter la modification de l'interface prism
    def setColor(self, layout: qt.QLayout) -> None:
        if isinstance(layout, qt.QGroupBox):
            layout = layout.layout()
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            
            if widget is not None:
                colorR = random.randrange(0, 255)
                colorG = random.randrange(0, 255)
                colorB = random.randrange(0, 255)
                widget.setStyleSheet(f"background-color: rgb({colorR}, {colorG}, {colorB})")
            elif item.layout() is not None:
                self.setColor(item.layout())
    
    def debugger(self) -> None:
        import sys
        sys.path.append("R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages/debug")
        import debug #type: ignore
        debug.debug()
        debug.debugpy.breakpoint()
    #------------------------ DEBUG ligne -----------------------



    # -------------------------------------------------- FOR USD EXPORT --------------------------------------------------
    def findGoodMethodeUSD(self) -> None:
        import maya.cmds as cmds
        save_mode = self.state.cb_saveMode.currentText()

        from_sceneFile = self.state.chb_depFromScene.isChecked()
        departement_select = self.state.cb_dep.currentText()
        product = self.state.getProductname()

        sublayer_checked = self.state.chb_sublayer.isChecked()
        sublayer = self.state.e_sublayer.text()

        cmds.select(clear=True)
        if save_mode == "Layer":
            if not from_sceneFile and sublayer_checked:
                if departement_select == "lay" and sublayer == "camera":
                    self.selectCamera()
                elif departement_select == "anm" and sublayer == "main":
                    self.selectAnimation()
                else:
                    self.PrintMSG("Unable to find what to select")
            
            elif not from_sceneFile and not sublayer_checked:
                if departement_select == "mod":
                    self.selectAssets()
                else:
                    self.PrintMSG("Unable to find what to select")
            else:
                self.PrintMSG("Unable to find what to select")
        


        elif save_mode == "Custom":
            if product == "toRig" or product == "Modeling":
                self.selectAssets()
            else:
                self.PrintMSG("Unable to find what to select")


        else:
            self.PrintMSG("Unable to find what to select")
    

        self.state.b_add.click()
    
    def setVisibilityWidget(self) -> None:
        if self.visibilityWidget:
            lost_layout = qt.QHBoxLayout() # créer un layout perdu dans l'univers rattaché à rien pour éviter que Prism force la visibilité des widgets dans l'interface
            self.state.groupBox_3.setParent(None) 
            lost_layout.addWidget(self.state.groupBox_3)
            lost_layout.addWidget(self.state.gb_previous)
            lost_layout.addWidget(self.state.gb_settings)
            self.all_settings.setText("Show all settings")
        else:
            self.state.groupBox_3.setParent(None) 
            self.state.verticalLayout_2.addWidget(self.state.groupBox_3)
            self.state.verticalLayout_2.addWidget(self.state.gb_settings)
            self.state.verticalLayout_2.addWidget(self.state.gb_previous)
            self.all_settings.setText("Hide all settings")
        
        
        self.visibilityWidget = not self.visibilityWidget
    # -------------------------------------------------- FOR USD EXPORT --------------------------------------------------

    # -------------------------------------------------- FOR EXPORT --------------------------------------------------
    def findGoodMethode(self) -> None:
        import maya.cmds as cmds
        product_name = self.state.getProductname()
        cmds.select(clear=True)

        if product_name == "cameraToAnim":
            self.selectCamera()
        if product_name == "Rigging":
            self.selectAssets()

        self.state.b_add.click()
    # -------------------------------------------------- FOR EXPORT --------------------------------------------------




    # -------------------------------------------------- common function -------------------------------------------------
    # -------------------------------------------------- common function -------------------------------------------------
    def selectCamera(self) -> None:
        import maya.cmds as cmds

        data = cmds.ls(dag=True, long=True)
        cleaned = []
        camera_found = None
        for item in data:
            cleaned.clear()
            for segment in item.split("|"):
                if ":" in segment:
                    # on garde ce qui est après le dernier ":"
                    cleaned.append(segment.split(":")[-1])
                elif segment:  # si pas de ":" mais chaîne non vide
                    cleaned.append(segment)

            if "|".join(cleaned) == 'cameras|camRig|camera|shotCam':
                camera_found = item
                break
            
        if not camera_found:
            return self.PrintMSG("camera not found, nice have:\n '(nameSpcae):cameras|nameSpace:camRig|nameSpace:camera|nameSpace:shotCam'")

        cmds.select(item)

    def selectAnimation(self) -> None:
        import maya.cmds as cmds

        nodes_find = set()
        for parent in ["assets|sets", "assets|characters", "assets|props"]:
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
            return self.PrintMSG('no geo to export, nice have: ["assets|sets", "assets|characters", "assets|props"')
        
        cmds.select(nodes_find)
    
    def selectAssets(self) -> None:
        import maya.cmds as cmds

        path_scene = self.state.core.getCurrentFileName()
        self.entity = self.state.core.getScenefileData(path_scene)
        asset_name = "|" + self.entity["asset"]
        if not cmds.objExists(asset_name):
            self.PrintMSG(f"the '|{asset_name}' group does not exist")
        
        cmds.select(asset_name)
    
    def hideWidget(self, layout: qt.QLayout)-> None:
        if isinstance(layout, qt.QGroupBox):
            layout.hide()
            layout = layout.layout()
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            
            if widget is not None:
                print("---", widget)
                widget.hide()
            elif item.layout() is not None:
                self.hideWidget(item.layout())
            else:
                print("pas trouver")

    def getUserAcess(self, key:str) -> list[str]:
        if not DATA_PARSE:
            return []
        
        json_data = None
        with open(DATA_PARSE, "r") as f:
            json_data:dict = json.loads(f.read())
        
        if not json_data:
            return []
        
        return json_data[key]

    def showWidget(self, layout: qt.QVBoxLayout) -> None:
        if isinstance(layout, qt.QGroupBox):
            layout = layout.layout()

        for i in range(layout.count()):
            item = layout.itemAt(i)
            widget = item.widget()
            
            if widget is not None:
                print("---", widget)
                widget.show()
            elif item.layout() is not None:
                self.showWidget(item.layout())

    def showShotPlus10(self, index: int):
        if index == 2:
            self.state.Illo_l_frame_plus_10.show()
            self.state.Illo_spin_frame_plus_10.show()
        else:
            self.state.Illo_l_frame_plus_10.hide()
            self.state.Illo_spin_frame_plus_10.hide()

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

    def PrintMSG(self, msg) -> None:
        import maya.cmds as cmds
        cmds.warning(msg)
        cmds.inViewMessage(amg=msg, pos = "midCenter", fade=True, bkc=0xcc0101)