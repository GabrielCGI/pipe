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
        print("---------------------------")

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
            print("Skip proxy: "+transform)
            continue
        proxy_found = False
        # Check for shape nodes under the transform
        for shape in transform.getShapes():

            # Check if the shape is an aiStandIn
            if shape.nodeType() == 'aiStandIn':
                dso_path = shape.getAttr('dso')
                try:
                    version_number = int(dso_path.split('/')[-2])  # Extracting the version number
                    base_path = '/'.join(dso_path.split('/')[:-2]) + '/'  # Base path without version and file
                except Exception as e:

                    pm.warning("Fail on %s"%transform)
                    print(e)
                    continue


                # Try finding a valid proxy file by decrementing versions
                while version_number >= 0:

                    test_version = f"{version_number:04d}"
                    proxy_path = os.path.join(base_path, test_version, os.path.basename(os.path.splitext(dso_path)[0] + '_proxy.abc'))

                    if os.path.exists(proxy_path):
                        proxy_found = True
                        # Create an empty group for the proxy
                        proxy_group = pm.group(em=True, name=f"{transform.name()}_proxy")

                        # Import the Alembic file and reparent it under the "proxy" group
                        pm.AbcImport(proxy_path, mode="import", rpr=proxy_group)

                        # Match transform of the group to the aiStandIn's transform
                        pm.matchTransform(proxy_group, transform)
                        pm.parent(proxy_group, transform)
                        # Assuming set_to_procedural_null and lock_transforms are defined elsewhere
                        set_to_procedural_null(proxy_group)
                        lock_transforms(proxy_group)
                        print("Proxy found for %s: %s"%(transform,proxy_path))
                        connectTime(transform)
                        break
                    version_number -= 1

        if not proxy_found:
            cmds.warning( "No proxy found for %s"%dso_path )
        pm.select(transform)




def set_standInDrawOverride(selectionOnly=False, state=0, proxy_check=True):
    if selectionOnly:
        nodes_selected = pm.selected()
        nodes = nodes_selected + pm.listRelatives(nodes_selected, allDescendents=True, type='aiStandIn')

        # Remove duplicates that might occur if children are also selected
        nodes = list(set(nodes))

    else:
        nodes = pm.ls(type='aiStandIn')  # List all aiStandIn nodes in the scene

    # Filter aiStandIn nodes
    aiStandIn_nodes = [node for node in nodes if node.nodeType() == 'aiStandIn'and "publish/ass" not in node.dso.get()]

    for node in aiStandIn_nodes:
        if not node.hasAttr('standInDrawOverride'):
            pm.warning(f"{node} does not have a 'standInDrawOverride' attribute.")
            continue

        # Perform proxy check if required
        if proxy_check and state == 3:
            has_proxy = False
            for child in node.getParent().listRelatives(children=True):
                if "proxy" in child.name().lower():
                    has_proxy = True
                    break

            # If a proxy child is found, make the standIn invisible
            if has_proxy:
                node.standInDrawOverride.set(3)  # Make invisible
            else:
                # If no proxy and state is explicitly set to make visible, apply the state
                if state != 3:  # Assuming 3 means invisible, adjust according to your needs
                    node.standInDrawOverride.set(state)
                # If the intention is to always leave non-proxy standIns visible regardless of the state argument,
                # you might want to force a visible state here instead of applying 'state'.
                # For example, node.standInDrawOverride.set(0) to force visibility.
        else:
            # If proxy check is not required, just apply the provided state
            node.standInDrawOverride.set(state)

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
    nodes = []
    if selectionOnly:
        selected_nodes = pm.selected()
        for node in selected_nodes:
            if "proxy" in node.name().lower() and node.type() == "transform":
                nodes.append(node)
            descendants = node.listRelatives(allDescendents=True, type='transform')
            for desc in descendants:
                if "proxy" in desc.name().lower():
                    nodes.append(desc)
    else:
        # Get all transform nodes with "proxy" in their name
        proxy_nodes = pm.ls('*proxy*', type='transform')
        for node in proxy_nodes:
            nodes.append(node)
            # Include children of the node
            children = node.listRelatives(allDescendents=True, type='transform')
            nodes.extend(children)

    for node in nodes:
        node.visibility.set(visibility)

def connectTime(node):
        # Get the current selection
        try:
            standIn = node.getShape()

        except:
            cmds.warning('Fail to get shape on %s'%node)
            return
        if not standIn:
            cmds.warning("No standIn found.")
            return

        # Check if the selected node is an aiStandIn
        if standIn.type() != "aiStandIn":
            cmds.warning("Selected node is not an aiStandIn.")
            return

        # Search for the first AlembicNode connected to any child shape
        for child in node.getChildren(ad=True, type="shape"):
            # List all connections of type AlembicNode to this child
            alembic_nodes = pm.listConnections(child, type="AlembicNode")
            if alembic_nodes:
                alembic_node = alembic_nodes[0]
                break
        else:
            cmds.warning("No AlembicNode found connected to any child shape.")
            return

        # Create a plusMinusAverage node to invert the offset
        pma_node = pm.createNode('plusMinusAverage', name='invert_frameOffset_pma')
        pma_node.operation.set(2)  # Set operation to subtraction

        pma_node.input1D[0].set(0)  # Set the first input to 0

        # Connect the frameOffset of aiStandIn to the input of the plusMinusAverage
        pm.connectAttr(standIn + ".frameOffset", pma_node.input1D[1])

        # Connect the output of the plusMinusAverage to the offset of AlembicNode
        pm.connectAttr(pma_node + ".output1D", alembic_node + ".offset", f=True)

        # Connect frameNumber of aiStandIn directly to time of AlembicNode
        pm.connectAttr(standIn + ".frameNumber", alembic_node + ".time", f=True)


# Your createGarland function here...



class ProxyManagerUI(QWidget):
    def __init__(self, parent=None):
        super(ProxyManagerUI, self).__init__(parent)


        self.setWindowTitle("proxy manager")
        self.setMinimumSize(350, 100)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.create_widgets()
        self.create_layouts()

    def create_widgets(self):
        """
        Creates the widgets for the window
        """
        self.btn_action1 = QtWidgets.QPushButton("Import proxy")
        self.checkbox_action1 = QtWidgets.QCheckBox("Force")
        # Connect the buttons to their respective slot functions


        self.viewportLabel = QtWidgets.QLabel("StandIn:")
        self.btn_viewportOn = QtWidgets.QPushButton("Show ASS")
        self.btn_viewportOff = QtWidgets.QPushButton("Hide ASS")
        self.btn_viewportOffAll = QtWidgets.QPushButton("Hide all")
        self.btn_connectTime = QtWidgets.QPushButton("Connect time")
        self.proxLabel = QtWidgets.QLabel("Proxy:")
        self.btn_proxOn = QtWidgets.QPushButton("Show GEO")
        self.btn_proxOff = QtWidgets.QPushButton("Hide GEO")
        self.drawModeLabel = QtWidgets.QLabel("StandIn Display:")
        self.drawModeComboBox = QtWidgets.QComboBox()
        self.drawModeComboBox.addItems(["Bounding Box", "Shaded", "Point Cloud", "Polywire"])
        self.selectionOnlyCheckbox = QtWidgets.QCheckBox("Selection only")
        self.line = QtWidgets.QFrame()
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line2 = QtWidgets.QFrame()
        self.line2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line3 = QtWidgets.QFrame()
        self.line3.setFrameShape(QtWidgets.QFrame.HLine)
        self.btn_action1.clicked.connect(self.action1)
        self.btn_viewportOn.clicked.connect(self.btn_viewportOn_clicked)
        self.btn_viewportOff.clicked.connect(self.btn_viewportOff_clicked)
        self.btn_viewportOffAll.clicked.connect(self.btn_viewportOffAll_clicked)
        self.btn_proxOn.clicked.connect(self.btn_proxOn_clicked)
        self.btn_proxOff.clicked.connect(self.btn_proxOff_clicked)
        self.btn_connectTime.clicked.connect(self.btn_connectTime_clicked)

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
        main_layout.addWidget(self.line)

        viewportLayout = QtWidgets.QHBoxLayout()
        proxLayout = QtWidgets.QHBoxLayout()
        #viewportLayout.addWidget(self.viewportLabel)
        viewportLayout.addWidget(self.btn_viewportOn)
        viewportLayout.addWidget(self.btn_viewportOff)
        #viewportLayout.addWidget(self.btn_viewportOffAll)
        #proxLayout.addWidget(self.proxLabel)
        proxLayout.addWidget(self.btn_proxOn)
        proxLayout.addWidget(self.btn_proxOff)
        drawModeLayout = QtWidgets.QHBoxLayout()
        drawModeLayout.addWidget(self.drawModeLabel)
        drawModeLayout.addWidget(self.drawModeComboBox)

        main_layout.addLayout(viewportLayout)
        main_layout.addLayout(proxLayout)
        main_layout.addWidget(self.line2)
        main_layout.addLayout(drawModeLayout)
        main_layout.addWidget(self.selectionOnlyCheckbox)
        main_layout.addWidget(self.line3)
        main_layout.addWidget(self.btn_connectTime)
    def action1(self):
        print("Action 1 executed")
        force_import = self.checkbox_action1.isChecked()
        importProxyFromSelection(force=force_import)


    def btn_viewportOn_clicked(self):
        set_standInDrawOverride(self.selectionOnlyCheckbox.isChecked(), state=0)
        print("Action 2 executed")
    def btn_viewportOff_clicked(self):
        set_standInDrawOverride(self.selectionOnlyCheckbox.isChecked(), state=3, proxy_check=False)
    def btn_viewportOffAll_clicked(self):
        set_standInDrawOverride(self.selectionOnlyCheckbox.isChecked(), state=3, proxy_check=False)
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

    def btn_connectTime_clicked(self):
        for node in pm.selected():
            connectTime(node)


# Run the UI
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    ui = ProxyManagerUI()
    ui.show()
    app.exec_()
