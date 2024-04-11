import os
import pymel.core as pm
from maya import cmds
from PySide2 import QtWidgets
from PySide2.QtWidgets import QWidget, QDesktopWidget, QLabel
from PySide2.QtCore import Qt, QPoint



def set_to_procedural_null(sel):

    descendants = sel.listRelatives(allDescendents=True)

    # Iterate through each descendant
    for desc in descendants:
        # Check if the descendant has the 'ai_translator' attribute
        if desc.hasAttr('ai_translator'):
            # Set the 'ai_translator' attribute to 'procedural'
            desc.ai_translator.set('procedural')

def lock_transforms(sel):
    """
    Locks all transform attributes (translate, rotate, scale) for the selection and its children.

    Parameters:
    sel (list): A list of selected nodes.
    """
    # Attributes to lock
    attributes_to_lock = ['translateX', 'translateY', 'translateZ',
                          'rotateX', 'rotateY', 'rotateZ',
                          'scaleX', 'scaleY', 'scaleZ']


        # Include the node itself plus all descendants in the processing
    descendants = [sel] + sel.listRelatives(allDescendents=True, type="transform")
    print(descendants )

        # Iterate through each node to process
    for n in descendants:
        # Iterate through each attribute and lock it
        for attr in attributes_to_lock:
            n.attr(attr).lock()

def importProxyFromSelection(force=False):

    # Iterate over selected objects
    for transform in pm.selected():
        # Initialize a flag to check for existing proxy groups
        proxyExists = False

        # Check for existing child groups with "proxy" in the name
        for child in transform.getChildren(type='transform'):
            if "proxy" in child.name():
                if force:
                    # Delete the existing proxy group if force is True
                    pm.delete(child)
                else:
                    # Skip this selection if force is False
                    proxyExists = True
                    break

        # Skip the rest of the loop if a proxy exists and force is False
        if proxyExists:
            print("skip proxy --> "+transform )
            continue

        # Check for shape nodes under the transform
        for shape in transform.getShapes():
            # Check if the shape is an aiStandIn
            if shape.nodeType() == 'aiStandIn':
                dso_path = shape.getAttr('dso')
                # Check if a proxy file exists
                proxy_path = os.path.splitext(dso_path)[0] + '_proxy.abc'
                if os.path.exists(proxy_path):
                    # Create an empty group for the proxy
                    proxy_group = pm.group(em=True, name=f"{transform.name()}_proxy")

                    # Import the Alembic file and reparent it under the "proxy" group
                    pm.AbcImport(proxy_path, mode="import", rpr=proxy_group)

                    # Match transform of the group to the aiStandIn's transform
                    pm.matchTransform(proxy_group, transform)
                    pm.parent(proxy_group, transform)
                    set_to_procedural_null(proxy_group)
                    lock_transforms(proxy_group)

def set_standInDrawOverride(selectionOnly=False, state=0):

    if selectionOnly:
        nodes = pm.selected()
    else:
        nodes = pm.ls(type='aiStandIn')  # List all aiStandIn nodes in the scene

    # Filter aiStandIn nodes
    aiStandIn_nodes = [node for node in nodes if node.nodeType() == 'aiStandIn']
    print(aiStandIn_nodes)
    print (state)
    # Set the standInDrawOverride attribute to 3 for each aiStandIn node
    for node in aiStandIn_nodes:
        if node.hasAttr('standInDrawOverride'):
            node.standInDrawOverride.set(state)
        else:
            pm.warning(f"{node} does not have a 'standInDrawOverride' attribute.")

def set_aiStandIn_mode(nodes, mode):
    """
    Sets the .mode attribute on a list of aiStandIn nodes.

    Parameters:
    nodes (list): List of aiStandIn nodes.
    mode (int): Value to set the .mode attribute to.
    """
    for node in nodes:
        if node.nodeType() == 'aiStandIn' and node.hasAttr('mode'):
            node.mode.set(mode)

def proxy_visibility(visibility, selectionOnly):
    if selectionOnly:
        # Get only the selected nodes and their descendants
        selected_nodes = pm.selected()
        nodes = []
        for node in selected_nodes:
            # Include the node if it's a transform and has "proxy" in its name
            if "proxy" in node.name().lower() and node.type() == "transform":
                nodes.append(node)
            # Also consider the descendants of the selected node
            descendants = node.listRelatives(allDescendents=True, type='transform')
            for desc in descendants:
                if "proxy" in desc.name().lower():
                    nodes.append(desc)
    else:
        # Get all transform nodes in the scene that have "proxy" in their name
        nodes = pm.ls('*proxy*', type='transform')

    for node in nodes:
        node.visibility.set(visibility)



# Your createGarland function here...



class ProxyManagerUI(QWidget):
    def __init__(self, parent=None):
        super(ProxyManagerUI, self).__init__(parent)


        self.setWindowTitle("Simple Window")
        self.setMinimumSize(350, 100)
        self.create_widgets()
        self.create_layouts()

    def create_widgets(self):
        """
        Creates the widgets for the window
        """
        self.btn_action1 = QtWidgets.QPushButton("Import proxy for selection")
        self.checkbox_action1 = QtWidgets.QCheckBox("Force")
        # Connect the buttons to their respective slot functions


        self.viewportLabel = QtWidgets.QLabel("Viewport stand in:")
        self.btn_viewportOn = QtWidgets.QPushButton("On")
        self.btn_viewportOff = QtWidgets.QPushButton("Off")
        self.proxLabel = QtWidgets.QLabel("Viewport Proxy:")
        self.btn_proxOn = QtWidgets.QPushButton("On")
        self.btn_proxOff = QtWidgets.QPushButton("Off")
        self.drawModeLabel = QtWidgets.QLabel("Draw Mode:")
        self.drawModeComboBox = QtWidgets.QComboBox()
        self.drawModeComboBox.addItems(["Bounding Box", "Shaded", "Point Cloud", "Polywire"])
        self.selectionOnlyCheckbox = QtWidgets.QCheckBox("Selection only")

        self.btn_action1.clicked.connect(self.action1)
        self.btn_viewportOn.clicked.connect(self.btn_viewportOn_clicked)
        self.btn_viewportOff.clicked.connect(self.btn_viewportOff_clicked)
        self.btn_proxOn.clicked.connect(self.btn_proxOn_clicked)
        self.btn_proxOff.clicked.connect(self.btn_proxOff_clicked)
        self.drawModeComboBox.currentIndexChanged.connect(self.onDrawModeChange)

    def create_layouts(self):
        """
        Creates the layouts and adds widgets to them
        """
        main_layout = QtWidgets.QVBoxLayout(self)
        action1_layout = QtWidgets.QHBoxLayout()
        action1_layout.addWidget(self.btn_action1)
        action1_layout.addWidget(self.checkbox_action1)
        main_layout.addLayout(action1_layout)

        viewportLayout = QtWidgets.QHBoxLayout()
        proxLayout = QtWidgets.QHBoxLayout()
        viewportLayout.addWidget(self.viewportLabel)
        viewportLayout.addWidget(self.btn_viewportOn)
        viewportLayout.addWidget(self.btn_viewportOff)
        proxLayout.addWidget(self.proxLabel)
        proxLayout.addWidget(self.btn_proxOn)
        proxLayout.addWidget(self.btn_proxOff)
        drawModeLayout = QtWidgets.QHBoxLayout()
        drawModeLayout.addWidget(self.drawModeLabel)
        drawModeLayout.addWidget(self.drawModeComboBox)

        main_layout.addLayout(viewportLayout)
        main_layout.addLayout(proxLayout)
        main_layout.addLayout(drawModeLayout)
        main_layout.addWidget(self.selectionOnlyCheckbox)
    def action1(self):
        print("Action 1 executed")
        force_import = self.checkbox_action1.isChecked()
        importProxyFromSelection(force=force_import)

    def btn_viewportOn_clicked(self):
        set_standInDrawOverride(self.selectionOnlyCheckbox.isChecked(), state=0)
        print("Action 2 executed")
    def btn_viewportOff_clicked(self):
        set_standInDrawOverride(self.selectionOnlyCheckbox.isChecked(), state=3)
        print("Action off executed")
    def btn_proxOn_clicked(self):
        proxy_visibility(1,self.selectionOnlyCheckbox.isChecked())
    def btn_proxOff_clicked(self):
        proxy_visibility(0, self.selectionOnlyCheckbox.isChecked())
    def onDrawModeChange(self):
        dicDraw = {"Shaded": 6, "Point Cloud": 4, "Bounding Box": 0, "Polywire": 2}
        drawMode = self.drawModeComboBox.currentText()
        print(f"Draw Mode changed to: {drawMode}")
        mode_value = dicDraw.get(drawMode)
        if self.selectionOnlyCheckbox.isChecked():
            selected_nodes = pm.selected()
            set_aiStandIn_mode(selected_nodes, mode_value)
        else:
            all_nodes = pm.ls(type='aiStandIn')
            set_aiStandIn_mode(all_nodes, mode_value)

# Run the UI
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    ui = ProxyManagerUI()
    ui.show()
    app.exec_()
