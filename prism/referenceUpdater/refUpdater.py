import qtpy.QtCore as qtc
from importlib import reload
from pathlib import Path
import subprocess
import sys



__ROOT__ = Path(__file__).parent
PYTHON_SCRIPT_MAYA = f"{__ROOT__}/mayaCode_updateImportRef.py"
MAYAPY = "C:/Program Files/Autodesk/Maya2025/bin/mayapy.exe"




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
    def __init__(self, Core, DCC, scenePath, ProjetPath, addition = False, update = True, notWantUpdate=[],  dataRef:dict = {}, debug=False):
        self.ProjetPath = ProjetPath
        self.notWantUpdate = notWantUpdate
        self.scenePath = scenePath
        self.addition = addition
        self.dataRef = dataRef
        self.update = update
        self.debug = debug
        self.Core = Core
        self.DCC = DCC

    
    def runUpdate(self, standalone: bool, forceDep:str = "Rigging"):
        environement = {"Projet": self.ProjetPath, "Scene": self.scenePath, "addition":self.addition, "Update":self.update, "notWantUpdate": self.notWantUpdate, "DEBUG":self.debug, "standalone":standalone, "department":forceDep}

        
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
            

            from . import mayaCode_updateImportRef as update
            reload(update)
            update.CoreStandalone()