from importlib import reload
import qtpy.QtWidgets as qt
import qtpy.QtCore as qtc
from pathlib import Path
import sys
import os
import re



__ROOT__ = Path(__file__).parent
PYTHON_SCRIPT_MAYA = f"{__ROOT__}/mayaCode_updateImportRef.py"
MAYAPY = "C:/Program Files/Autodesk/Maya2025/bin/mayapy.exe"


from . import refUpdater
from . import UI_loadingScreen
reload(refUpdater)



class startWithRef(qt.QMainWindow):
    def __init__(self, Core, DCC, scenePath, ProjetPath, standalone, debug=False):
        super().__init__()
        self.ProjetPath = ProjetPath
        self.scenePath = scenePath
        self.standalone = standalone
        self.toUp_reference = []
        self.tables = []
        self.DCC = DCC
        self.Core = Core


        self.setWindowTitle("import  and update assets in the scene")
        self.resize(500, 800)
        windo = qt.QWidget(self)
        self.setCentralWidget(windo)
        layout = qt.QVBoxLayout(windo)
        

        path_layout = qt.QHBoxLayout()
        path_label = qt.QLabel("Chemin :")
        self.path_edit = qt.QLineEdit()
        self.path_edit.setEnabled(standalone)
        if self.scenePath:
            self.path_edit.setText(self.scenePath)
        self.QfindScene = qt.QPushButton("load scene")
        self.QfindScene.clicked.connect(self.findScene)
        self.QfindScene.setEnabled(standalone)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.QfindScene)
        layout.addLayout(path_layout)


        options = qt.QHBoxLayout()
        self.addRef = qt.QCheckBox("difference between Scene and Import")
        self.udpdateref = qt.QCheckBox("Update All Reference Scene")
        self.udpdateref.clicked.connect(self.activeCheckBox)
        self.consoleMode = qt.QCheckBox("Console mode")
        self.consoleMode.setEnabled(standalone)
        options.addWidget(self.addRef)
        options.addWidget(self.udpdateref)
        options.addWidget(self.consoleMode)
        layout.addLayout(options)


        self.tabs = qt.QTabWidget()
        self.createTab("Characters")
        self.createTab("Props")
        self.createTab("Sets")
        layout.addWidget(self.tabs)


        self.createReferenceTab("Update Reference")

        

        self.validate_button = qt.QPushButton("Valider")
        self.validate_button.clicked.connect(self.on_validate)
        layout.addWidget(self.validate_button)
    
    def createReferenceTab(self, titre):
        self.toUp_reference.clear()

        table = qt.QTableWidget()
        table.setObjectName(titre)
        self.tabs.addTab(table, titre)

        table.setColumnCount(5)
        table.setColumnWidth(0, 100)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 100)
        table.setColumnWidth(3, 100)
        table.setColumnWidth(4, 70)
        table.setHorizontalHeaderLabels(["name", "Reference", "Actual Version", "last Version", "update"])
        self.all_reference = []
        if not self.standalone:
            import maya.cmds as cmds
            reference_in_scene = self.findReferenceInScene()
            for referenceType in reference_in_scene:
                for asset_name in reference_in_scene[referenceType]:
                    for reference in reference_in_scene[referenceType][asset_name]:
                        file_path = cmds.referenceQuery(reference, f=True, wcn=True)
                        self.all_reference.append({"reference": reference, "path": file_path})
        
        else:
            self.all_reference = self.findReferenceInFile()
        
        if not self.all_reference:
            return

        table.setRowCount(len(self.all_reference))
        for row, data_ref in enumerate(self.all_reference):
            print(data_ref["reference"], data_ref["path"])
            asset_name = data_ref["reference"].split("_")[0]
            item = qt.QLabel(asset_name)
            table.setCellWidget(row, 0, item)


            QReference = qt.QLabel()
            QReference.setText(data_ref["reference"])
            table.setCellWidget(row, 1, QReference)


            QOld_version = qt.QLabel()
            table.setCellWidget(row, 2, QOld_version)


            QNew_version = qt.QLabel()
            table.setCellWidget(row, 3, QNew_version)

            QNew_version = qt.QLabel()
            table.setCellWidget(row, 3, QNew_version)

            QCheckBox = qt.QCheckBox()
            table.setCellWidget(row, 4, QCheckBox)


            #------------------------get all value for widget------------------------
            file_path = data_ref["path"]
            color = "rgb(64, 64, 0)"
            if file_path:
                old_version = file_path.split("/")[-2]
                new_version = sorted(os.listdir(Path(file_path).parent.parent))[-1]
                
                if old_version == new_version:
                    color = 'rgb(0, 64, 0)'
                else:
                    color = "rgb(64, 0, 0)"


            #----------------------------set the color and value----------------------------
            item.setStyleSheet(f"background-color: {color}")

            QReference.setStyleSheet(f"background-color: {color}")
            
            QOld_version.setText(old_version)
            QOld_version.setStyleSheet(f"background-color: {color}")
            
            QNew_version.setText(new_version)
            QNew_version.setStyleSheet(f"background-color: {color}")

            QCheckBox.setStyleSheet(f"background-color: {color}")
            QCheckBox.setEnabled(old_version != new_version)

            self.toUp_reference.append({"QCheckBox": QCheckBox, "reference": data_ref["reference"], "asset": asset_name, "old_version": old_version, "new_version": new_version})

    def activeCheckBox(self):
        result = self.udpdateref.isChecked()
        for ref_data in self.toUp_reference:
            QCheckBox : qt.QCheckBox = ref_data["QCheckBox"]

            if QCheckBox.isEnabled():
                QCheckBox.setChecked(result)



    def createTab(self, titre):
        table = qt.QTableWidget()
        table.setObjectName(titre)
        self.tables.append(table)

        table.setColumnCount(3)
        table.setColumnWidth(0, 200)
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 100)
        table.setHorizontalHeaderLabels([titre, "Nombre d'importations", "version"])
        items, path = self.findAllAssets(titre)
        table.setRowCount(len(items))
        
        for row, item_name in enumerate(items):
            item = qt.QTableWidgetItem(item_name)
            table.setItem(row, 0, item)


            spin = NoWheelSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(100)
            table.setCellWidget(row, 1, spin)


            Qversion = qt.QLabel()
            Qversion.setAlignment(qtc.Qt.AlignCenter)
            table.setCellWidget(row, 2, Qversion)


            if not os.path.exists(f"{path}/{item_name}/Export/Rigging"):
                item.setFlags(qtc.Qt.NoItemFlags)
                spin.setEnabled(False)
                Qversion.setText("no Rigging")
                continue
            
            version = sorted(os.listdir(f"{path}/{item_name}/Export/Rigging"))[-1]
            Qversion.setText(str(version))

        self.tabs.addTab(table, titre)

    def findAllAssets(self, assetType):
        path = self.ProjetPath + "/03_Production/Assets/" + assetType
        if not os.path.exists(path):
            print("error path not valide", path)
            return [], None
        
        return os.listdir(path), path

    def findScene(self):
        path = None
        if self.DCC == "Maya":
            path, _ = qt.QFileDialog.getOpenFileName(self, "Select your scene file", self.ProjetPath + "/03_Production/Shots", "Maya Files (*.ma);; Maya Files (*.mb);; all (*)")
        elif self.DCC == "Houdini":
            path, _ = qt.QFileDialog.getOpenFileName(self, "Select your scene file", self.ProjetPath + "/03_Production/Shots", "Houdini Files (*.hip);; Houdini Files (*.hipnc);; all (*)")
        
        if not path:
            return
        
        self.scenePath = path
        self.path_edit.setText(path)

    def on_validate(self):
        need_update = self.udpdateref.isChecked()
        path = self.path_edit.text()
        if not path:
            return
        
        # récupéré tout les element qu'on veux ajouter dans la scene
        dataRef = {}
        for table in self.tables:
            results = {}
            for row in range(table.rowCount()):
                item_name = table.item(row, 0).text()
                spinbox = table.cellWidget(row, 1)
                count = spinbox.value()
                if count != 0:
                    results[item_name] = count
            
            if not results:
                continue
            dataRef[table.objectName()] = results


        # récupéré tout les element qu'on veux mettre à jour dans la scene
        not_want_update = [ref_data["reference"] for ref_data in self.toUp_reference if not ref_data["QCheckBox"].isChecked()]
        if len(not_want_update) != len(self.all_reference):
            need_update =True

        if not dataRef and not need_update:
            return

        self.worker = refUpdater.instanceWorker( self.Core, self.DCC, self.scenePath, self.ProjetPath, self.addRef.isChecked(), need_update, not_want_update, dataRef, debug=self.consoleMode.isChecked())
        self.worker.runUpdate(self.standalone)
        if not self.consoleMode.isChecked() and self.standalone:
            self.Core.waiter = UI_loadingScreen.LoadingWindow("waite the script process...")
            self.Core.waiter.show()


        if not self.standalone:
            count = self.tabs.count()
            if count > 0:
                self.tabs.removeTab(count - 1)
                self.createReferenceTab("Update Reference")
                self.tabs.setCurrentIndex(count - 1)
    

    def findReferenceInScene(self):
        # petit fake pour que le script mayaCode_updateImport fonctionne correctement.
        environement = {"Projet": self.ProjetPath, "Scene": self.scenePath, "addition":False, "Update":False, "DEBUG":False, "standalone":False, "department":"Rigging"}

        if len(sys.argv) <= 1:
            sys.argv.append(str(environement))
        else:
            sys.argv[1] = str(environement)
        
        if len(sys.argv) <= 2:
            sys.argv.append(str({}))
        else:
            sys.argv[2] = str({})


        #importer et récupperer tout les references dans la scene 
        from . import mayaCode_updateImportRef as update
        reload(update)
        reference = update.findRefInScene()

        return reference
    
    def findReferenceInFile(self):
        #ouvre le fichier en type text pour lire ligne après ligne toute les data du fichier et recuppérer tout les référence de la scene maya
        with open(self.scenePath, "r") as f:
            data_file = f.read()
        
        all_reference = []
        lignes = re.split(r';\s*', data_file)
        lignes = [l for l in lignes if l.strip()]

        for ligne in lignes:
            if ligne.startswith("file -r -ns "):
                results = re.findall(r'"([^"]*)"', ligne)
                file_path = results[-1]
                refeenceRN = results[1]
                all_reference.append({"reference": refeenceRN, "path": file_path})

        return all_reference



class NoWheelSpinBox(qt.QSpinBox):
    def wheelEvent(self, event):
        event.ignore()