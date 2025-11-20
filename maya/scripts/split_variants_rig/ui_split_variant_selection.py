import maya.cmds as cmds
import json
import sys
import os




def import_qtpy():
    # permet de récupéré la dernière version de python dans le logiciel prism il prendra toutjours la bibliothèque qtpy de la dernière version de prism 
    prism_app = "C:/ILLOGIC_APP/Prism"
    if not os.path.exists(prism_app):
        return False

    versions = os.listdir(prism_app)
    versions.sort()
    version = versions[-2]
    Python_path = f"{prism_app}/{version}/app/PythonLibs/python3"
    pyside_path = Python_path + "/PySide"

    if not os.path.exists(pyside_path):
        return False
    
    if not Python_path in sys.path:
        sys.path.append(Python_path)
    
    if not pyside_path in sys.path:
        sys.path.append(pyside_path)
    
    return True
if import_qtpy():
    import qtpy.QtWidgets as qt
    import qtpy.QtCore as qtc



class UISelectExport(qt.QDialog):
    def __init__(self, prism, name_asset:str, data_in_scene: dict[str], outliner: qt.QWidget, name_variant: str, name_ctrl: str, parent = None):
        super(UISelectExport, self).__init__(parent)
        self.QtData_Widget: list[QvariantLineUI] = []
        self.data_in_scene = data_in_scene
        self.name_variant = name_variant
        self.name_asset = name_asset
        self.name_ctrl = name_ctrl
        self.data_to_Export = None
        self.saveData = False
        self.resulte = True
        self.bypass = False
        self.prism = prism

        self.setWindowTitle("Select and attribute each variants your rig for export")
        largeur = 1300
        self.resize(largeur, 600)



        #-------------------------------- start UI ------------------------------
        mainContainer = qt.QHBoxLayout(self)
        mainContainer.setContentsMargins(0, 0, 0, 0)
        
        spliter = qt.QSplitter()
        mainContainer.addWidget(spliter)


        #-----------------------------splitter parti gauche-----------------------------
        container_data = qt.QWidget(spliter)
        container_ligne = qt.QVBoxLayout(container_data)

        
        text_info = qt.QLabel("This tool allows you to create a custom export for each variant along with its rig. It will export the geometry and the rig variants, if any, in order to optimize the rig scenes. Then, it will reassemble the rigging products.\n\nExample: You have 3 variants A, B, and C. It will export 3 scenes: A.ma, B.ma, and C.ma, and reference them in the Rigging products.")
        text_info.setStyleSheet("font-size: 13px;")
        text_info.setWordWrap(True)
        container_ligne.addWidget(text_info)



        options = qt.QHBoxLayout()
        container_ligne.addLayout(options)

        self.BT_options_group = qt.QButtonGroup(self)
        self.BT_options_group.setExclusive(True)
        self.BT_options_group.buttonClicked.connect(self.selectOptions)


        radio1 = qt.QRadioButton("Load scene data")
        radio1.editable = False
        self.BT_options_group.addButton(radio1, id=1)
        options.addWidget(radio1)

        radio2 = qt.QRadioButton("Make Manual")
        radio2.editable = True
        self.BT_options_group.addButton(radio2, id=2)
        options.addWidget(radio2)
        radio2.setChecked(True) if not self.data_in_scene else radio1.setChecked(True)
        
        options.addStretch(1)
        
        self.exec_auto = qt.QPushButton("Auto detection")
        self.exec_auto.clicked.connect(self.detectionAutomatic)
        options.addWidget(self.exec_auto)
        
        options.addStretch(10)

        info_spin = qt.QLabel("nmb variant want split")
        options.addWidget(info_spin)
        
        self.nmb_variant_to_export = qt.QSpinBox()
        self.nmb_variant_to_export.setValue(1)
        self.nmb_variant_to_export.valueChanged.connect(self.changeValueSpinBox)
        options.addWidget(self.nmb_variant_to_export)



        self.list_QWidget_items = qt.QListWidget()
        container_ligne.addWidget(self.list_QWidget_items)
        self.createDataSet(self.data_in_scene)


        exec_button_layout = qt.QHBoxLayout()
        container_ligne.addLayout(exec_button_layout)

        exec_button_layout.addStretch()

        button_exec = qt.QPushButton("Execute script")
        button_exec.clicked.connect(self.executeScript)
        exec_button_layout.addWidget(button_exec)

        bypass_exec = qt.QPushButton("By pass")
        bypass_exec.clicked.connect(self.bypassScript)
        exec_button_layout.addWidget(bypass_exec)
        
        QButton_save_data = qt.QPushButton("Save Data")
        QButton_save_data.clicked.connect(self.saveDataInScene)
        exec_button_layout.addWidget(QButton_save_data)





        #-----------------------------splitter parti droit-----------------------------
        widget_outliner = qt.QWidget(spliter)
        self.container_outliner = qt.QVBoxLayout(widget_outliner)
        self.container_outliner.addWidget(outliner)



        spliter.setSizes([(largeur/10)*7, (largeur/10)*3])
        self.selectOptions(radio2 if not self.data_in_scene else radio1)


    #------------------------- UI -------------------------
    def createDataSet(self, data) -> None:
        if not data:
            self.list_QWidget_items.clear()
            self.QtData_Widget.clear()
            self.addQListWidgetItem()
            return

        self.nmb_variant_to_export.setValue(len(data))
        self.list_QWidget_items.clear()
        self.QtData_Widget.clear()
        for dagPath in data:
            self.QtData_Widget.append(QvariantLineUI(dagPath, data[dagPath]["geo"], data[dagPath]["rig"], self.list_QWidget_items))
            
    def changeValueSpinBox(self, value):
        if value > len(self.QtData_Widget):
            self.addQListWidgetItem()
        elif value < len(self.QtData_Widget):
            self.suppQListWidgetItem()
        else:
            print("pas normale sa")

    def suppQListWidgetItem(self) -> None:
        item = self.list_QWidget_items.currentItem()
        if item:
            index = self.list_QWidget_items.currentRow()
        else:
            index = self.list_QWidget_items.count() - 1
        
        if self.list_QWidget_items.count() > 0:
            self.list_QWidget_items.takeItem(index)
            self.QtData_Widget.pop(index)

    def addQListWidgetItem(self) -> None:
        self.QtData_Widget.append(QvariantLineUI("", None, None, self.list_QWidget_items))

    def selectOptions(self, button: qt.QRadioButton):
        if button.editable:
            self.list_QWidget_items.setDisabled(False)
            self.nmb_variant_to_export.setDisabled(False)
            self.exec_auto.setDisabled(False)
        else:
            self.list_QWidget_items.setDisabled(True)
            self.nmb_variant_to_export.setDisabled(True)
            self.exec_auto.setDisabled(True)

    def seeResult(self):
        print(self.QtData_Widget)

    def detectionAutomatic(self):
        if not self.list_QWidget_items.isEnabled():
            return
        
        rig = []
        if cmds.objExists(f'{self.name_asset}|rig'):
            rig.append(f'{self.name_asset}|rig')
        
        all_vairant = cmds.attributeQuery(self.name_variant, node=self.name_ctrl, listEnum=True)
        if all_vairant is None:
            return
        

        varaints = {}
        for variant in all_vairant[0].split(":"):
            if not cmds.objExists(variant):
                continue
            
            all_variant = cmds.ls(variant, long=True)
            clean_variant = []
            for pathVariant in all_variant:
                if "|rig|" in pathVariant:
                    continue

                clean_variant.append(pathVariant)
            
            varaints[variant] = {"rig": rig, "geo": clean_variant}

        self.createDataSet(varaints)
    
    def executeScript(self):
        self.converteData()
        self.saveData = True
        self.close()

    def bypassScript(self):
        self.bypass = True
        self.close()

    def converteData(self) -> dict[dict]:
        self.data_to_Export = {}
        for QWidget in self.QtData_Widget:
            if not QWidget.long_name or not QWidget.list_geo_save:
                continue
            
            self.data_to_Export[QWidget.long_name] = {"geo": QWidget.list_geo_save, "rig": QWidget.list_rig_save}

    def saveDataInScene(self):
        #save les datas dans la scene ouvert
        self.converteData()
        cmds.fileInfo("IllogicVariantRIG", json.dumps(self.data_to_Export))
        cmds.file(save=True)

    def closeEvent(self, event):
        if not self.saveData:
            self.data_to_Export = None
            self.QtData_Widget = None
            if not self.bypass:
                self.resulte = False
        
        return super().closeEvent(event)




class QvariantLineUI(qt.QListWidgetItem):
    def __init__(self, long_name: str, list_geo_save:list[str], list_rig_save: list[str], QlistQWidget: qt.QListWidget):
        super(QvariantLineUI, self).__init__(QlistQWidget)
        self.list_geo_save = list_geo_save
        self.list_rig_save = list_rig_save
        self.nameVariant = long_name.split("|")[-1] if long_name else "Variant No Def"
        self.long_name = None

        container = qt.QWidget()
        layouH = qt.QHBoxLayout(container)
        layouH.setContentsMargins(10, 5, 10, 5)

        self.QNameVariant = qt.QLabel(self.nameVariant)
        layouH.addWidget(self.QNameVariant)

        button_selected_geo = qt.QPushButton("Save Selected Geo")
        button_selected_geo.clicked.connect(self.saveDataGeo)
        layouH.addWidget(button_selected_geo)

        label_fleche = qt.QLabel(" -----> ")
        layouH.addWidget(label_fleche)



        layouV_geo = qt.QVBoxLayout()
        layouH.addLayout(layouV_geo)

        geometry_Label = qt.QLabel("Geometry to export")
        layouV_geo.addWidget(geometry_Label)

        self.all_string_geo = qt.QTextEdit()
        if list_geo_save: self.saveDataGeo(self.list_geo_save)
        self.all_string_geo.setMaximumHeight(50)
        self.all_string_geo.setMinimumWidth(10)
        layouV_geo.addWidget(self.all_string_geo)



        button_selected_rig = qt.QPushButton("Save Selected Rig")
        button_selected_rig.clicked.connect(self.saveDataRig)
        layouH.addWidget(button_selected_rig)

        label_fleche = qt.QLabel(" -----> ")
        layouH.addWidget(label_fleche)



        layouV_rig = qt.QVBoxLayout()
        layouH.addLayout(layouV_rig)

        rig_label = qt.QLabel("Rig to export")
        layouV_rig.addWidget(rig_label)

        self.all_string_rig = qt.QTextEdit()
        if list_rig_save: self.saveDataRig(self.list_rig_save)
        self.all_string_rig.setMaximumHeight(50)
        self.all_string_rig.setMinimumSize(0, 0)
        layouV_rig.addWidget(self.all_string_rig)


        self.setSizeHint(container.sizeHint())
        QlistQWidget.setItemWidget(self, container)

    def saveDataGeo(self, data=None):
        if not data:
            data = cmds.ls(sl=True, long=True)
            self.list_geo_save = data
        
        if data:
            goodName = []
            for i in data:
                goodName.append(i.split("|")[-1])
        
            self.all_string_geo.setText(str(goodName))


            self.QNameVariant.setText(goodName[0])
            self.nameVariant = goodName[0]
            self.long_name = data[0]
    
    def saveDataRig(self, data=None):
        if not data:
            data = cmds.ls(sl=True, long=True)
            self.list_rig_save = data
        
        if data:
            goodName = []
            for i in data:
                goodName.append(i.split("|")[-1])
            
            self.all_string_rig.setText(str(goodName))
    