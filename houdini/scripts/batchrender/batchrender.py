import os
import hou
import json 
from functools import partial
from .qt import QtCore, QtWidgets, QtGui

import PrismInit

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


class ShotItem(QtWidgets.QWidget):
    
    def __init__(self, text, item: QtWidgets.QTreeWidgetItem, batch_selector, parent=None):
        super().__init__(parent)
        self.batch_selector = batch_selector
        self.item = item
        self.setObjectName("w_shotitem")

        lo_item = QtWidgets.QHBoxLayout()
        lo_item.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lo_item)
        
        self.cbb_state = QtWidgets.QCheckBox()
        # cbb_state.stateChanged.connect(self.on_state_changed)
        self.cbb_state.setCheckState(QtCore.Qt.CheckState.Checked)
        lo_item.addWidget(self.cbb_state)
        
        btn_check_all = QtWidgets.QPushButton("Check All")
        btn_check_all.clicked.connect(
            lambda: self.set_check_all(True)
        )
        lo_item.addWidget(btn_check_all)
        
        btn_uncheck_all = QtWidgets.QPushButton("Uncheck All")
        btn_uncheck_all.clicked.connect(
            lambda: self.set_check_all(False)
        )
        lo_item.addWidget(btn_uncheck_all)
        
        lo_item.addStretch()
        
        lb_shot = QtWidgets.QLabel(text)
        lo_item.addWidget(lb_shot)


    def set_check_state(self, state: QtCore.Qt.CheckState):
        self.cbb_state.setCheckState(state)


    def is_checked(self):
        return self.cbb_state.isChecked()


    def set_check_all(self, on: bool):
        if on:
            check_state = QtCore.Qt.CheckState.Checked
        else:
            check_state = QtCore.Qt.CheckState.Unchecked
        self.set_check_state(check_state)
        for id_exec in range(self.item.childCount()):
            execution = self.item.child(id_exec)
            execution.setCheckState(0, check_state)
            self.batch_selector.refresh_execution_item(execution)

    
class BatchSelector(QtWidgets.QDialog):
    
    def __init__(
            self,
            render_nodes: list[hou.LopNode],
            parent: QtWidgets.QWidget=None):
        
        super().__init__(parent)
        self.setWindowTitle('Batch Render')
        self.setMinimumSize(QtCore.QSize(1100, 650))
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.render_nodes = render_nodes
        self.render_nodes.sort(key=lambda x: x.name())
        
        self.initialize_style_sheet()
        self.setup_UI()
        
    
    # ======== UI Setup ========
        
    def initialize_style_sheet(self):
        """
        Initialize UI qss.
        """

        self.setStyleSheet(STYLE_CONTENT)


    def setup_UI(self):
        self.main_layout = QtWidgets.QHBoxLayout()
        
        # Execution layout
        self.execution_widget = QtWidgets.QGroupBox()
        execution_layout = QtWidgets.QVBoxLayout()
        
        self.tree = self.create_render_tree()
        execution_layout.addWidget(self.tree, 90)
        
        # Menu layout
        self.w_menu = QtWidgets.QWidget()
        lo_menu = QtWidgets.QVBoxLayout()

        lo_selection = QtWidgets.QHBoxLayout()
        lo_menu.addLayout(lo_selection)

        select_all_button = QtWidgets.QPushButton(text='Check All')
        select_all_button.clicked.connect(
            lambda: self.set_check_all(True)
        )
        lo_selection.addWidget(select_all_button)

        deselect_all_button = QtWidgets.QPushButton(text='Uncheck All')
        deselect_all_button.clicked.connect(
            lambda: self.set_check_all(False)
        )
        lo_selection.addWidget(deselect_all_button)
        
        lo_submit = QtWidgets.QHBoxLayout() 
        lo_menu .addLayout(lo_submit)

        refresh_button = QtWidgets.QPushButton(text='Refresh')
        refresh_button.clicked.connect(self.refresh_execution_layout)
        lo_submit.addWidget(refresh_button, 50)
        
        publish_button = QtWidgets.QPushButton(text='Submit')
        publish_button.clicked.connect(self.submit)
        lo_submit.addWidget(publish_button, 50)
        
        self.w_menu.setLayout(lo_menu)
        execution_layout.addWidget(self.w_menu, 10)
        
        self.execution_widget.setLayout(execution_layout)
        self.execution_widget.setObjectName('w_execution')
        self.execution_widget.setTitle("Executions")
        self.main_layout.addWidget(self.execution_widget, 50)
        
        # Description layout
        # self.description_widget = QtWidgets.QGroupBox()
        # description_layout = QtWidgets.QVBoxLayout()
        
        # description = self.get_description()
        
        # self.tb_description = QtWidgets.QTextBrowser()
        # self.tb_description.setHtml(description)
        # self.tb_description.setReadOnly(True)
        
        # description_layout.addWidget(self.tb_description, 50)
                
        # self.description_widget.setLayout(description_layout)
        # self.description_widget.setObjectName('w_description')
        # self.description_widget.setTitle('Description')
        # self.main_layout.addWidget(self.description_widget, 50)
        
        self.setLayout(self.main_layout)
      
    
    # def get_description(self):

    #     description = (
    #         '<h4>Selected renders:</h4>'
    #         '<ul style="'
    #         'margin-left: -20px;'
    #         '">'
    #     )
                
    #     root = self.tree.invisibleRootItem()
    #     for id_shot in range(root.childCount()):
    #         shot = root.child(id_shot)
    #         shot_widget: ShotItem = self.tree.itemWidget(shot, 0)
    #         data = shot.data(0, QtCore.Qt.UserRole)
    #         node: hou.LopNode = data['node']

    #         if shot.is_checked():
    #             continue

    #         state = data['state']
    #         range_type = state.ui.cb_rangeType.currentText()
    #         frame_range = state.ui.getFrameRange(range_type)
    #         if len(frame_range) < 2:
    #             f1 = node.parm('f1')
    #             f2 = node.parm('f2')
    #             if f1 and f2:
    #                 frame_range = [f1.eval(), f2.eval()]
    #             else:
    #                 frame_range = [None, None]
                    
    #         if not frame_range[0] or not frame_range[1]:
    #             print('Did not found frame range')
    #             frame_range = [0, 0]
            
    #         node_executions = data['executions']
    #         if not node_executions:
    #             continue
    #         shot_name = node_executions[0]
    #         shot_description = (
    #             f'<li><b>{shot_name["shot"]}</b> : '
    #             f"({frame_range[0]} - {frame_range[1]})</li>"
    #             '<table width="100%" '
    #             'style="'
    #             'table-layout: fixed;'
    #             'border-collapse: collapse;'
    #             'border-spacing: 10px;'
    #             '">'
    #         )

    #         layer_count = 0
    #         for id_exec in range(shot.childCount()):
    #             execution = shot.child(id_exec)
    #             execution_data = node_executions[id_exec]

    #             if execution.checkState(0) == QtCore.Qt.CheckState.Checked:
    #                 exec_layer = execution_data['layer']
                    
    #                 if (layer_count%TABLE_MAX_LENGTH == 0):
    #                     if layer_count != 0:
    #                         shot_description += "</tr>"
    #                     shot_description += '<tr>'
    #                 shot_description += (
    #                     '<td '
    #                     'style="'
    #                     'padding-left: 10px;'
    #                     'padding-right: 30px;'
    #                     f'border: 1px solid {palettedata["BLACK"]};">'
    #                     f'<b>{exec_layer}</b></td>'
    #                 )
    #                 layer_count += 1

    #         if layer_count == 0:
    #             shot_description = ''

    #         description += f"{shot_description}</tr></table>"

    #     description += "</ul>"

    #     return description

      
    def refresh_description(self):
        return
        description = self.get_description()
        self.tb_description.setHtml(description)
         
  
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
                    layer.setCheckState(0, QtCore.Qt.CheckState.Checked)
                else:
                    layer.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        self.refresh_description()
        

    def set_check_all(self, on: bool):
        if on:
            check_state = QtCore.Qt.CheckState.Checked
        else:
            check_state = QtCore.Qt.CheckState.Unchecked
        root = self.tree.invisibleRootItem()
        for id_shot in range(root.childCount()):
            shot = root.child(id_shot)
            shot_widget: ShotItem = self.tree.itemWidget(shot, 0)
            shot_widget.set_check_state(check_state)
            for id_exec in range(shot.childCount()):
                execution = shot.child(id_exec)    
                execution.setCheckState(0, check_state)
                self.refresh_execution_item(execution)
        self.refresh_description()


    def refresh_execution_item(self, item: QtWidgets.QTreeWidgetItem):
        if item.parent() is not None:
            data = item.parent().data(0, QtCore.Qt.UserRole)
            exec_id = item.data(0, QtCore.Qt.UserRole)
            parm_name = f'execution_enabled_{exec_id}'
            execution_enabled = data['node'].parm(parm_name)
            if item.checkState(0) == QtCore.Qt.CheckState.Checked:
                execution_enabled.set(True)
            else:
                execution_enabled.set(False)

    
    def on_item_clicked(self, item: QtWidgets.QTreeWidgetItem, column: int):
        # Check if the item changed is a layer or a shot
        self.tree.setUpdatesEnabled(False)
        if item.parent() is not None:
            if column != 0:
                return
            if item.checkState(0) == QtCore.Qt.CheckState.Checked:
                check_state = QtCore.Qt.CheckState.Unchecked
            else:
                check_state = QtCore.Qt.CheckState.Checked
            item.setCheckState(0, check_state)
            self.refresh_execution_item(item)
            self.refresh_description()
        self.tree.setUpdatesEnabled(True)
        

    # ======== Batch Render ========
          
    def create_render_tree(self):
        
        tree = QtWidgets.QTreeWidget()
        tree.setColumnCount(1)
        tree.setRootIsDecorated(True)
        tree.setHeaderHidden(True)
        # tree.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.MultiSelection)
        tree.setSelectionMode(QtWidgets.QTreeWidget.SelectionMode.NoSelection)
        tree.itemClicked.connect(self.on_item_clicked)
        tree.itemChanged.connect(self.refresh_description)
        
        items_list = []
        self.render_nodes.sort(key=lambda node:node.name(), reverse=True)
        for node in self.render_nodes:
            nb_exec = node.parm('executions')
            # check if shot has executions
            if not nb_exec: 
                continue
            nb_exec = nb_exec.eval()
            if not nb_exec:
                continue
            
            item = QtWidgets.QTreeWidgetItem()
            
            # store shot data in item
            data = {
                'node': node,
                'executions': [],
            }
            data['state'] = LOP_RENDER.getStateFromNode(data) 
            
            empty_shot = True
            no_shot_enable = True
            for id_exec in range(1, nb_exec+1):
                # try to parse execution shot and layer
                exec_res = self.parse_execution(id_exec, node)
                if not exec_res:
                    continue
                empty_shot = False

                # update execution data
                exec_shot, exec_layer = exec_res
                data['executions'].append({
                    'shot': exec_shot,
                    'layer': exec_layer
                })
                is_enable = node.parm(f'execution_enabled_{id_exec}')
                is_enable = is_enable and is_enable.eval()
                
                exec_item = QtWidgets.QTreeWidgetItem()
                if is_enable:
                    no_shot_enable = False
                    exec_item.setCheckState(0, QtCore.Qt.CheckState.Checked)
                else:
                    exec_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                
                # store data et widget in item
                exec_item.setText(0, exec_layer)
                exec_item.setData(0, QtCore.Qt.UserRole, id_exec)
                exec_item.setFlags(exec_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.addChild(exec_item)
            
            # ignore shot without executions
            if empty_shot:
                continue
            
            # create item widget
            node_text = f"{exec_shot}: {item.childCount()} executions"
            
            item.setData(0, QtCore.Qt.UserRole, data)
            item_widget = ShotItem(node_text, item, self)
            if no_shot_enable:
                item_widget.set_check_state(QtCore.Qt.CheckState.Unchecked)
            items_list.append((item, item_widget))
        for item, widget in items_list:
            tree.insertTopLevelItem(0, item)
            tree.setItemWidget(item, 0, widget)
        return tree


    def submit(self):
        
        states = []
        root = self.tree.invisibleRootItem()
        kwargs = None
        for id_shot in range(root.childCount()):
            shot = root.child(id_shot)
            shot_widget: ShotItem = self.tree.itemWidget(shot, 0)
            data = shot.data(0, QtCore.Qt.UserRole)
            node = data['node']
            
            if not shot_widget.is_checked():
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
                continue
            
            name = name_context.eval()
            value = value_context.eval()
            if name == LAYER_IDENTIFIER: 
                exec_layer = value

        edit_context_option = [
            n for n in node.inputs()
            if n.type().name() == 'editcontextoptions'
        ]
        if not len(edit_context_option):
            return
        edit_context_option: hou.LopNode = edit_context_option[0]
        for i in range(1, edit_context_option.parm("optioncount").eval()+1):
            name_context = edit_context_option.parm(f'optionname{i}')
            value_context = edit_context_option.parm(f'optionstrvalue{i}')
            if not name_context or not value_context:
                continue
            name = name_context.eval()
            value = value_context.eval()
            if name == SHOT_IDENTIFIER: 
                exec_shot = value

        
        if not exec_shot:
            return
        if not exec_layer:
            return
        return (exec_shot, exec_layer)          
            

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

    batch_selector = BatchSelector(render_nodes)
    batch_selector.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    batch_selector.show()