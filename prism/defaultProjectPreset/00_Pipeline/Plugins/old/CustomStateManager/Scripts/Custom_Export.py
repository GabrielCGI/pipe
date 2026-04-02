import qtpy.QtWidgets as qt



OLD_SETUP_USD = None
OLD_SETUP = None



class CustomExport():
    def __init__(self, state):
        self.state = state

        qt_lay_horizontal = qt.QHBoxLayout()
        qt_lay_horizontal.addWidget(self.state.b_add)
        self.state.verticalLayout_3.addLayout(qt_lay_horizontal)

        self.state.b_add.setMaximumWidth(85)

        qt_btn_autoSelect = qt.QPushButton("Select Auto")
        self.customSheet(qt_btn_autoSelect)
        qt_lay_horizontal.addWidget(qt_btn_autoSelect)

        if self.state.className == "USD Export":
            qt_btn_autoSelect.clicked.connect(lambda nul: self.findGoodMethodeUSD())
        elif self.state.className == "Export":
            qt_btn_autoSelect.clicked.connect(lambda nul: self.findGoodMethode())


    # -------------------------------------------------- FOR USD EXPORT --------------------------------------------------
    def findGoodMethodeUSD(self):
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
    # -------------------------------------------------- FOR USD EXPORT --------------------------------------------------

    # -------------------------------------------------- FOR EXPORT --------------------------------------------------
    def findGoodMethode(self):
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
    def selectCamera(self):
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

    def selectAnimation(self):
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
    
    def selectAssets(self):
        import maya.cmds as cmds

        path_scene = self.state.core.getCurrentFileName()
        self.entity = self.state.core.getScenefileData(path_scene)
        asset_name = "|" + self.entity["asset"]
        if not cmds.objExists(asset_name):
            self.PrintMSG(f"the '|{asset_name}' group does not exist")
        
        cmds.select(asset_name)
            

    def customSheet(self, bb):
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

    def PrintMSG(self, msg):
        import maya.cmds as cmds
        cmds.warning(msg)
        cmds.inViewMessage(amg=msg, pos = "midCenter", fade=True, bkc=0xcc0101)