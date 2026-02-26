import qtpy.QtCore as qtc
import subprocess
import traceback
import os



from ..Core.RU_signal import signal



PYTHON_SCRIPT_MAYA = os.path.join(os.path.dirname(__file__), "RU_startStandalone.py")
MAYAPY = "C:/Program Files/Autodesk/Maya2025/bin/mayapy.exe"




class Worker(qtc.QThread):
    finished = qtc.Signal(str)

    def __init__(self, sceneFile:str, data_to_send: dict, debug_mode=False):
        super().__init__()
        self.debug_mode = debug_mode
        self.sceneFile = sceneFile
        self.data = data_to_send

    def run(self):
        try:
            command = [MAYAPY, PYTHON_SCRIPT_MAYA, self.sceneFile, str(self.data)]
            if self.debug_mode:
                result = subprocess.Popen(command, text=True, creationflags=subprocess.CREATE_NEW_CONSOLE)#, stdout=subprocess.PIPE
            else:
                result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            for line in result.stdout:
                line = line.strip()
                if line.startswith("SIGNAL:"):
                    data = line[7:]
                    signal.emits(data)
            
            result.wait()
            self.finished.emit("stop")

        except Exception as e:
            signal.emits(e)
            pass
