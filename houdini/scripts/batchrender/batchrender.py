import os
import hou
import json 
import sys

import PrismInit

from PySide2 import QtCore
from PySide2 import QtWidgets

from . import farmsubmitter
import importlib
importlib.reload(farmsubmitter)

SHOT_IDENTIFIER = 'shot'
LAYER_IDENTIFIER = 'layer'

TABLE_MAX_LENGTH = 2

USD_PLUGIN = PrismInit.pcore.getPlugin('USD')
LOP_RENDER = USD_PLUGIN.api.lopRender

UI_RESSOURCES_DIR = os.path.join(
    os.path.dirname(__file__),
    'ressources'
)
palettePath = os.path.join(UI_RESSOURCES_DIR, 'defaultPalette.json')
style_path = os.path.join(UI_RESSOURCES_DIR, 'stylesheet.qss')

with open(palettePath, "r") as file:
    palettedata = json.load(file)
with open(style_path, "r") as file:
    STYLE_CONTENT = file.read()
for key, value in palettedata.items():
    STYLE_CONTENT = STYLE_CONTENT.replace(key, value)




    
class BatchSelector(QtWidgets.QDialog):
    
    def __init__(
            self,
            render_nodes: list[hou.LopNode],
            parent: QtWidgets.QWidget=None):
        
        super().__init__(parent)
        self.setWindowTitle('Batch Render')
        self.setMinimumSize(QtCore.QSize(1000, 650))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.render_nodes = render_nodes
        self.render_nodes.sort(key=lambda x: x.name())
        
        self.initializeStyleSheet()
        self.setupUI()
        
        
    def initializeStyleSheet(self):
        """
        Initialize UI qss.
        """
  
        self.setStyleSheet(STYLE_CONTENT)
  
  
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
        tree.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        
        items_list = []
        self.render_nodes.sort(key=lambda node:node.name())
        for node in self.render_nodes:
            nb_exec = node.parm('executions')
            
            if not nb_exec: 
                continue
            
            nb_exec = nb_exec.eval()
            if not nb_exec:
                continue
            
            item = QtWidgets.QTreeWidgetItem()
            item.setCheckState(0, QtCore.Qt.CheckState.Checked)
            
            data = {'node': node}
            state = LOP_RENDER.getStateFromNode(data)
            data['executions'] = []
            data['state'] = state

            empty_shot = True
            for id_exec in range(1, nb_exec+1):
                exec_res = self.parse_execution(id_exec, node)
                if not exec_res:
                    continue
                empty_shot = False
        
                exec_shot, exec_layer = exec_res
                is_enable = node.parm(f'execution_enabled_{id_exec}')
                is_enable = is_enable and is_enable.eval()
                
                text = f'Shot: {exec_shot} - Layer: {exec_layer}'
                exec_item = QtWidgets.QTreeWidgetItem()
                exec_item.setText(0, text)
                if is_enable:
                    exec_item.setCheckState(0, QtCore.Qt.CheckState.Checked)
                else:
                    exec_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                
                data['executions'].append({
                    'shot': exec_shot,
                    'layer': exec_layer
                })
                
                exec_item.setData(0, QtCore.Qt.UserRole, id_exec)
                item.addChild(exec_item)
            
            if empty_shot:
                continue
            
            node_text = f"{node.name()}: {item.childCount()} executions"
            item.setData(0, QtCore.Qt.UserRole, data)
            item.setText(0, node_text)
            items_list.append(item)
        tree.insertTopLevelItems(0, items_list)
        tree.itemChanged.connect(self.on_item_changed)
        return tree


    def on_item_changed(self, item, column):
        # Check if the item changed is a layer or a shot
        if item.parent() is not None:
            data = item.parent().data(0, QtCore.Qt.UserRole)
            exec_id = item.data(0, QtCore.Qt.UserRole)
            
            parm_name = f'execution_enabled_{exec_id}'
            execution_enabled = data['node'].parm(parm_name)
            if item.checkState(0) == QtCore.Qt.Checked:
                execution_enabled.set(True)
            else:
                execution_enabled.set(False)

        if item.isSelected():
            if item.checkState(0) == QtCore.Qt.Checked:
                for selected_item in self.tree.selectedItems():
                    selected_item.setCheckState(0, QtCore.Qt.Checked)
                    
            else:
                for selected_item in self.tree.selectedItems():
                    selected_item.setCheckState(0, QtCore.Qt.Unchecked)
                
        description = self.get_description()
        self.tb_description.setHtml(description)            
            
    
    def get_description(self):

        description = (
            '<h4>Selected renders:</h4>'
            '<ul style="margin-left: -20px;">')
                
        root = self.tree.invisibleRootItem()
        for id_shot in range(root.childCount()):
            shot = root.child(id_shot)
            data = shot.data(0, QtCore.Qt.UserRole)
            node: hou.LopNode = data['node']

            if shot.checkState(0) != QtCore.Qt.CheckState.Checked:
                continue

            state = data['state']
            range_type = state.ui.cb_rangeType.currentText()
            frame_range = state.ui.getFrameRange(range_type)
            if len(frame_range) < 2:
                f1 = node.parm('f1')
                f2 = node.parm('f2')
                if f1 and f2:
                    frame_range = [f1.eval(), f2.eval()]
                else:
                    frame_range = [None, None]
                    
            if not frame_range[0] or not frame_range[1]:
                print('Did not found frame range')
                frame_range = [0, 0]
            shot_description = (
                f'<li><b>{node.name()}</b> : '
                f"({frame_range[0]} - {frame_range[1]})</li>"
                '<table style="'
                'border-collapse: collapse;'
                'border-spacing: 10px;'
                '">')

            layer_count = 0
            for id_exec in range(shot.childCount()):
                execution = shot.child(id_exec)
                execution_data = data['executions'][id_exec]

                if execution.checkState(0) == QtCore.Qt.CheckState.Checked:
                    exec_shot = execution_data['shot']
                    exec_layer = execution_data['layer']
                    
                    if (layer_count%TABLE_MAX_LENGTH == 0):
                        if layer_count != 0:
                            shot_description += "</tr>"
                            
                        shot_description += '<tr>'
                    shot_description += (
                        '<td style="'
                        'padding-left: 10px;'
                        'padding-right: 30px;'
                        f'border: 1px solid {palettedata["BLACK"]};'
                        # 'border-spacing: 30px;'
                        f'">{exec_shot} - <b>{exec_layer}</b></td>'
                    )
                    layer_count += 1

            if layer_count == 0:
                shot_description = ''

            description += f"{shot_description}</tr></table>"

        description += "</ul>"

        return description

    
    def refresh_execution_layout(self):
        
        root = self.tree.invisibleRootItem()
        
        for id_shot in range(root.childCount()):
            shot = root.child(id_shot)
            data = shot.data(0, QtCore.Qt.UserRole)
            node = data['node']
            
            for id_layer in range(shot.childCount()):
                layer = shot.child(id_layer)
                id_execution = layer.data(0, QtCore.Qt.UserRole)
                parm_name = f'execution_enabled_{id_execution}'
                enabled_parm = node.parm(parm_name)
                
                if enabled_parm and enabled_parm.eval():
                    layer.setCheckState(0, QtCore.Qt.Checked)
                else:
                    layer.setCheckState(0, QtCore.Qt.Unchecked)


    def setupUI(self):
        self.main_layout = QtWidgets.QHBoxLayout()
        
        # Execution layout
        self.execution_widget = QtWidgets.QGroupBox()
        execution_layout = QtWidgets.QVBoxLayout()
        
        self.tree = self.create_render_tree()
        execution_layout.addWidget(self.tree, 90)
        
        # Menu layout
        self.w_menu = QtWidgets.QWidget()
        lo_menu = QtWidgets.QHBoxLayout()
        
        refresh_button = QtWidgets.QPushButton(text='Refresh')
        refresh_button.clicked.connect(self.refresh_execution_layout)
        lo_menu.addWidget(refresh_button, 50)
        
        publish_button = QtWidgets.QPushButton(text='Execute')
        publish_button.clicked.connect(self.submit)
        lo_menu.addWidget(publish_button, 50)
        
        self.w_menu.setLayout(lo_menu)
        execution_layout.addWidget(self.w_menu, 10)
        
        self.execution_widget.setLayout(execution_layout)
        self.execution_widget.setObjectName('w_execution')
        self.execution_widget.setTitle("Executions")
        self.main_layout.addWidget(self.execution_widget, 50)
        
        # Description layout
        self.description_widget = QtWidgets.QGroupBox()
        description_layout = QtWidgets.QVBoxLayout()
        
        description = self.get_description()
        
        self.tb_description = QtWidgets.QTextBrowser()
        self.tb_description.setHtml(description)
        self.tb_description.setReadOnly(True)
        
        description_layout.addWidget(self.tb_description, 50)
                
        self.description_widget.setLayout(description_layout)
        self.description_widget.setObjectName('w_description')
        self.description_widget.setTitle('Description')
        self.main_layout.addWidget(self.description_widget, 50)
        
        self.setLayout(self.main_layout)
    
        
    def submit(self):
        
        states = []
        root = self.tree.invisibleRootItem()
        kwargs = None
        for id_shot in range(root.childCount()):
            shot = root.child(id_shot)
            data = shot.data(0, QtCore.Qt.UserRole)
            node = data['node']
            
            if shot.checkState(0) != QtCore.Qt.CheckState.Checked:
                continue
            
            has_no_execution = True
            
            for id_exec in range(shot.childCount()):
                execution = shot.child(id_exec)
                execution_data = execution.data(0, QtCore.Qt.UserRole)
                parm_name = ('execution_enabled_'
                                f'{execution_data}')
                execution_parm = node.parm(parm_name)
                
                if execution.checkState(0) != QtCore.Qt.CheckState.Checked:
                    execution_parm.set(0)
                    continue
                
                has_no_execution = False
                
            if has_no_execution:
                continue
                
            if kwargs is None:
                kwargs = {'node': node}
            
            states.append(data['state'])
        
        states = list(set(states))
        self.submitter = farmsubmitter.Farm_Submitter(
            LOP_RENDER,
            states,
            kwargs)
        
        res = self.submitter.exec()
        if res:
            self.accept()
        
            

def main():
    
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