import qtpy.QtWidgets as qt
import qtpy.QtCore as qtc
from importlib import reload
from pathlib import Path
import subprocess
import sys
import os



__ROOT__ = Path(__file__).parent
PYTHON_SCRIPT_MAYA = f"{__ROOT__}/mayaCode_updateImportRef.py"
MAYAPY = "C:/Program Files/Autodesk/Maya2025/bin/mayapy.exe"



class startWithRef(qt.QMainWindow):
    def __init__(self, Core, DCC, scenePath, ProjetPath, debug=False):
        super().__init__()
        self.ProjetPath = ProjetPath
        self.scenePath = scenePath
        self.tables = []
        self.DCC = DCC
        self.Core = Core


        self.setWindowTitle("import assets in the start of the scene")
        self.resize(500, 800)
        windo = qt.QWidget(self)
        self.setCentralWidget(windo)
        layout = qt.QVBoxLayout(windo)


        path_layout = qt.QHBoxLayout()
        path_label = qt.QLabel("Chemin :")
        self.path_edit = qt.QLineEdit()
        if self.scenePath:
            self.path_edit.setText(self.scenePath)
        self.QfindScene = qt.QPushButton("load scene")
        self.QfindScene.clicked.connect(self.findScene)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.QfindScene)
        layout.addLayout(path_layout)


        options = qt.QHBoxLayout()
        self.addRef = qt.QCheckBox("difference between Scene and Import")
        self.udpdateref = qt.QCheckBox("Update Reference Scene")
        self.consoleMode = qt.QCheckBox("Console mode")
        options.addWidget(self.addRef)
        options.addWidget(self.udpdateref)
        options.addWidget(self.consoleMode)
        layout.addLayout(options)


        self.tabs = qt.QTabWidget()
        self.createTab("Characters")
        self.createTab("Props")
        self.createTab("Sets")
        layout.addWidget(self.tabs)
        

        self.validate_button = qt.QPushButton("Valider")
        self.validate_button.clicked.connect(self.on_validate)
        layout.addWidget(self.validate_button)
    
    def createTab(self, titre):
        table = qt.QTableWidget()
        table.setObjectName(titre)
        self.tables.append(table)
        table.setColumnCount(3)
        table.setColumnWidth(0, 150)
        table.setColumnWidth(1, 200)
        table.setColumnWidth(1, 100)
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
            print("error path note valide", path)
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
        path = self.path_edit.text()
        if not path:
            return
        
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

        if not dataRef and not self.udpdateref.isChecked():
            return
        #environement = {"Projet": self.ProjetPath, "Scene": self.scenePath, "addition":self.addRef.isChecked(), "Update":self.udpdateref.isChecked()}
        self.worker = instanceWorker( self.Core, self.DCC, self.scenePath, self.ProjetPath, self.addRef.isChecked(), self.udpdateref.isChecked(), dataRef, debug=self.consoleMode.isChecked())
        self.worker.runUpdate(True)
        if not self.consoleMode.isChecked():
            self.Core.waiter = LoadingWindow("waite the script process...")
            self.Core.waiter.show()
    
    



class NoWheelSpinBox(qt.QSpinBox):
    def wheelEvent(self, event):
        event.ignore()



class LoadingWindow(qt.QWidget):
    def __init__(self, msg):
        super().__init__()
        self.setWindowTitle("Chargement...")
        self.setFixedSize(300, 100)
        self.setStyleSheet("background-color: #232323;")

        layout = qt.QVBoxLayout()
        self.text = qt.QLabel(msg)
        layout.addWidget(self.text)

        self.progress_bar = qt.QProgressBar(self)
        #self.progress_bar.setStyleSheet("")
        self.progress_bar.setRange(0, 0)  # 0,0 → mode indéterminé (boucle infinie)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)



class SubprocessWorker(qtc.QThread):
    finished = qtc.Signal(str)
    error = qtc.Signal(str)

    def __init__(self, command, debug):
        super().__init__()
        self.command = command
        self.debug = debug
        self.ignore_patterns = [
            "qt.svg",
            "Qt WebEngine",
            "# ", "Warning: ", "File read", "Error: "
        ] # Filtrage des lignes stderr

    def run(self):
        try:
            if self.debug:
                result = subprocess.run(self.command, text=True, creationflags=subprocess.CREATE_NEW_CONSOLE)#, stdout=subprocess.PIPE
                cleaned_stderr_lines = self.filtrageSTDERR(result.stdout)# Filtrage des lignes stderr
            else:
                result = subprocess.run(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                cleaned_stderr_lines = self.filtrageSTDERR(result.stdout)# Filtrage des lignes stderr

            self.finished.emit(cleaned_stderr_lines)
        except subprocess.CalledProcessError as e:
            self.error.emit(e.stderr or f"Error code {e.returncode}")
    
    # Filtrage des lignes stderr
    def should_ignore(self, line):
        for i in self.ignore_patterns:
            if line.startswith(i):
                return True
        
        return False
    
    def filtrageSTDERR(self, std):
        msg = ""
        for line in std.splitlines():
            if "ILLOGIC ERROR :"  in line:
                msg += line + "\n"
        
        return msg



class instanceWorker():
    def __init__(self, Core, DCC, scenePath, ProjetPath, addition = False, update = True,  dataRef:dict = {}, debug=False):
        self.ProjetPath = ProjetPath
        self.scenePath = scenePath
        self.addition = addition
        self.dataRef = dataRef
        self.update = update
        self.debug = debug
        self.Core = Core
        self.DCC = DCC

    
    def runUpdate(self, standalone: bool, forceDep:str = "Rigging"):
        environement = {"Projet": self.ProjetPath, "Scene": self.scenePath, "addition":self.addition, "Update":self.update, "DEBUG":self.debug, "standalone":standalone, "department":forceDep}

        
        arguments = None
        if self.DCC == "Maya":
            arguments = [MAYAPY, PYTHON_SCRIPT_MAYA, str(environement), str(self.dataRef)] #
        elif self.DCC == "Houdini":
            pass
        
        if not arguments:
            return False
        
        print("start worker...")
        if standalone:
            self.worker = SubprocessWorker(arguments, self.debug)
            self.worker.finished.connect(self.Core.handleResult)
            self.worker.error.connect(self.Core.handleError)
            self.worker.start()

        else:
            if len(sys.argv) <= 1:
                sys.argv.append(str(environement))
            else:
                sys.argv[1] = str(environement)
            
            if len(sys.argv) <= 2:
                sys.argv.append(str(self.dataRef))
            else:
                sys.argv[2] = str(self.dataRef)
            

            import mayaCode_updateImportRef as update
            reload(update)
            update.CoreStandalone()