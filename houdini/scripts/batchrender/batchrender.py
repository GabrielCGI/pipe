import sys
import hou
import PrismInit

from . import farmsubmitter
import importlib
importlib.reload(farmsubmitter)
from PySide2 import QtCore
from PySide2 import QtWidgets

USD_PLUGIN = PrismInit.pcore.getPlugin('USD')
LOP_RENDER = USD_PLUGIN.api.lopRender

DEBUG_MODE = True
try:
    sys.path.append(r'R:\devmaxime\virtualvens\sanitycheck\Lib\site-packages')
    import debugpy
except:
    DEBUG_MODE = False

def debug():
    if not DEBUG_MODE:
        return
    
    hython = r"C:\Program Files\Side Effects Software\Houdini 20.5.548\bin\hython3.11.exe"
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        print("Already attached")
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()

    
class BatchSelector(QtWidgets.QDialog):
    
    def __init__(
            self,
            render_nodes: list[hou.LopNode],
            parent: QtWidgets.QWidget=None):
        
        super().__init__(parent)
        self.setWindowTitle('Batch Render')
        self.setMinimumSize(QtCore.QSize(400, 500))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.render_nodes = render_nodes
        self.render_nodes.sort(key=lambda x: x.name())
        
        self.setupUI()
        
        
    def setupUI(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        
        self.publish_button = QtWidgets.QPushButton(text='Execute')
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.publish_button)
        
        self.setLayout(self.main_layout)
        
        
    def submit(self):
        
        first_node = self.render_nodes[0]
        states = [
            LOP_RENDER.getStateFromNode({'node': node})
            for node in self.render_nodes
        ]
        kwargs = {'node': first_node}
        self.submitter = farmsubmitter.Farm_Submitter(
            LOP_RENDER,
            states,
            kwargs
        )
        
        res = self.submitter.exec()
        if res:
            self.accept()

def main():
    
    debug()
    
    render_nodes = list(
        hou.lopNodeTypeCategory()
        .nodeType('prism::LOP_Render::1.0')
        .instances()
    )
    
    if not render_nodes:
        hou.ui.displayMessage(
            text='Did not find any Prism LOP Render node',
            severity=hou.severityType.Warning
        )
    
    batch_selector = BatchSelector(render_nodes[:1], hou.qt.mainWindow())
    batch_selector.show()