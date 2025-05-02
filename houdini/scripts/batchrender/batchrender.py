import os
import sys
import hou
import PrismInit
from PySide2 import QtCore
from PySide2 import QtWidgets

from . import farmsubmitter
import importlib
importlib.reload(farmsubmitter)

QSS_STYLESHEET_PATH = os.path.join(
    os.path.dirname(__file__),
    'ressources',
    'stylesheet.qss'
)

SHOT_IDENTIFIER = 'shots'
LAYER_IDENTIFIER = 'renderlayers'

USD_PLUGIN = PrismInit.pcore.getPlugin('USD')
LOP_RENDER = USD_PLUGIN.api.lopRender

DEBUG_MODE = False
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
    debugpy.breakpoint()

    
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
        
        self.initializeStyleSheet()
        self.setupUI()
        
        
    def initializeStyleSheet(self):
        """
        Initialize UI qss.
        """
        
        try:
            with open(QSS_STYLESHEET_PATH, "r") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            print(f"Could not load stylesheet:\n\t{e}")
  
  
    def parse_execution(self, id_exec, node):
        nb_contexts = node.parm(f'contextOptions_{id_exec}')
        
        if not nb_contexts:
            return
        
        exec_shot = None
        exec_layer = None
        for id_context in range(1, nb_contexts.eval()+1):
            name_context = node.parm(f'contextOptionsName_{id_exec}_{id_context}')
            value_context = node.parm(f'contextOptionsValue_{id_exec}_{id_context}')
            if not name_context or not value_context:
                return
            
            name = name_context.eval()
            value = value_context.eval()
            if name == SHOT_IDENTIFIER: 
                exec_shot = value
            elif name == LAYER_IDENTIFIER: 
                exec_layer = value
        
        if not exec_shot or not exec_layer:
            return
        
        return (exec_shot, exec_layer)          
            
            
    def create_render_tree(self):
        
        tree = QtWidgets.QTreeWidget()
        tree.setColumnCount(1)
        tree.setRootIsDecorated(False)
        tree.setHeaderHidden(True)
        
        items_list = []
        for node in self.render_nodes:
            nb_exec = node.parm('executions')
            # Si la Prism LOP Render node n'a pas d'executions
            # on l'ignore pour le moment
            if not nb_exec: 
                continue
            
            nb_exec = nb_exec.eval()
            if not nb_exec:
                continue
            
            item = QtWidgets.QTreeWidgetItem()
            item.setText(0, node.name())
            item.setCheckState(0, QtCore.Qt.CheckState.Checked)
            
            for id_exec in range(1, nb_exec+1):
                exec_res = self.parse_execution(id_exec, node)
                if not exec_res:
                    continue
                exec_shot, exec_layer = exec_res
                is_enable = node.parm(f'execution_enabled_{id_exec}')
                is_enable = is_enable and is_enable.eval()
                
                text = f'Execution: {id_exec} - Shot: {exec_shot} | Layer: {exec_layer}'
                exec_item = QtWidgets.QTreeWidgetItem()
                exec_item.setText(0, text)
                if is_enable:
                    exec_item.setCheckState(0, QtCore.Qt.CheckState.Checked)
                else:
                    exec_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                
                data = {
                    'execution': id_exec,
                    'shot': exec_shot,
                    'layer': exec_layer,
                    'node': node
                }
                exec_item.setData(0, QtCore.Qt.UserRole, data)                      
                item.addChild(exec_item)
            
            items_list.append(item)    
        tree.insertTopLevelItems(0, items_list)
        return tree
    
            
    def setupUI(self):
        self.main_layout = QtWidgets.QVBoxLayout()
        self.publish_button = QtWidgets.QPushButton(text='Execute')
        self.publish_button.clicked.connect(self.submit)
        
        self.tree = self.create_render_tree()

        self.main_layout.addWidget(self.tree, 90)
        self.main_layout.addWidget(self.publish_button, 10)
        
        self.setLayout(self.main_layout)
        
        
    def submit(self):
        
        states = []
        root = self.tree.invisibleRootItem()
        kwargs = None
        for id_shot in range(root.childCount()):
            shot = root.child(id_shot)
            
            if shot.checkState(0) != QtCore.Qt.CheckState.Checked:
                continue

            for id_layer in range(shot.childCount()):
                layer = shot.child(id_layer)
                data = layer.data(0, QtCore.Qt.UserRole)
                
                if layer.checkState(0) != QtCore.Qt.CheckState.Checked:
                    node = data['node']
                    node.parm(f'execution_enabled_{data["execution"]}').set(0)
                    continue
                
                states.append(LOP_RENDER.getStateFromNode(data))
                
                if kwargs is None:
                    kwargs = {'node': data['node']}
        
        # state = states[0]
        # sm = state.ui.stateManager
        # sm.getStateSettings()
        
        states = list(set(states))
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
    
    batch_selector = BatchSelector(render_nodes, hou.qt.mainWindow())
    batch_selector.show()