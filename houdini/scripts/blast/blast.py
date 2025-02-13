
from pathlib import Path
import hou

import blast.prim_tree as pt

from PySide2 import QtCore
from PySide2 import QtWidgets

UNPACK_NODE_TYPE = 'unpackusd::2.0'
BLAST_NODE_TYPE = 'blast'
MERGE_NODE_TYPE = 'merge'

class Blast(QtWidgets.QWidget):
    """Basic QT interface to select a depth and apply
    create as blast as possible from it.
    """
    
    
    def __init__(self, parent = None):
        super().__init__(parent)
        
        self.initialize = self.processPath()
        if not self.initialize:
            return
        
        self.setMinimumSize(300, 150)
        
        vbox = QtWidgets.QVBoxLayout()
        
        label = QtWidgets.QLabel("Select depth: ")
        vbox.addWidget(label)
        
        self.depthLabel = QtWidgets.QLabel()
        
        self.depthComboBox = QtWidgets.QComboBox()
        self.depthComboBox.currentTextChanged.connect(self.onDepthChanged)
        self.depthComboBox.addItems([str(i+1) for i in range(self.max_length)])
        vbox.addWidget(self.depthComboBox)
        
        vbox.addWidget(self.depthLabel)
        
        button = QtWidgets.QPushButton(text="Apply")
        button.clicked.connect(self.buildBlast)
        vbox.addWidget(button)
        
        self.setLayout(vbox)

    def buildBlast(self):
        """
        Build blast node for each path for the selected depth.
        """

        selectedLength = self.depthComboBox.currentText()
        
        network = self.selectedNode.parent()
        
        selectedPaths = self.path_per_length[selectedLength]
        selectedPathsSize = len(selectedPaths)
        
        if not len(selectedPaths):
            hou.ui.displayMessage(
                "No prims found",
                severity=hou.severityType.Message)
            return
        
        # Final merge node
        merge: hou.SopNode = network.createNode(node_type_name=MERGE_NODE_TYPE)
        
        # Position settings
        step = 2.0
        startingPoint = float(selectedPathsSize) / 2.0
        startingStep = step * -startingPoint
        merge.setPosition(self.selectedNode.position() + hou.Vector2(0, 2 * -step))
        
        for i, path in enumerate(selectedPaths):
            blast: hou.SopNode = network.createNode(node_type_name=BLAST_NODE_TYPE)
            
            currentX = startingStep + i*step
            offset = hou.Vector2(currentX, -step)
            blast.setPosition(self.selectedNode.position() + offset)
            
            blast.setInput(0, self.selectedNode)
            blast.parm('group').set(f"@path={path}")
            blast.parm("negate").set(True)
            
            merge.setInput(i, blast)
            
    def getPossiblePath(self, node: hou.SopNode):
        """Get every path from an unpack node USD in primitive mode.

        Args:
            node (hou.SopNode): Selected node.

        Raises:
            ValueError: Raise an error when the node type do not correspond.

        Returns:
            list[str]: List of all primitives paths found.
        """        
        
        
        if node.type().name() != UNPACK_NODE_TYPE:
            raise ValueError(f"Unexpected type {node.type().name()}"
                            f"Please use {UNPACK_NODE_TYPE} type instead")
            
        mode = node.parm("output").eval()
        
        match mode:
            # Packed Prims mode
            case 0:
                geometry = node.geometry()
                path_list = []
                for prim in geometry.prims():
                    path_list.append(prim.attribValue("path"))
                    
                path_list = list(set(path_list))
                path_list.sort()
                return path_list
            
            # Polygon mode
            case 1:
                node.parm("output").set(0)
                
                geometry = node.geometry()
                path_list = []
                for prim in geometry.prims():
                    path_list.append(prim.attribValue("path"))
                    
                path_list = list(set(path_list))
                path_list.sort()
                
                node.parm("output").set(1)
                return path_list
                
            case _:
                hou.ui.displayMessage(
                    "Could not get unpack mode (Packed prims or Polygons)",
                    severity=hou.severityType.Message)

    def processPath(self):
        """ From an unpacked node, build a tree with each primitive
        path then sort each path by length.

        Returns:
            bool: True if we could parse each primitive path. 
        """        
        
        self.selectedNode = hou.selectedNodes()
        
        if not self.selectedNode:
            hou.ui.displayMessage(
                "Please select an USD unpack node",
                severity=hou.severityType.Message)
            return False
        self.selectedNode = self.selectedNode[0]
        
        if self.selectedNode.type().name() != UNPACK_NODE_TYPE:
            hou.ui.displayMessage(
                "Please select an USD unpack node",
                severity=hou.severityType.Message)
            return False
        
        self.path_list = self.getPossiblePath(self.selectedNode)
        
        
        self.max_length = 0
        self.path_per_length = {}
        print(f"Number of prim: {len(self.path_list)}")
        for path in self.path_list:
            pathObj = Path(path)
            path_length = len(pathObj.parts)
            if path_length > self.max_length:
                self.max_length = path_length

        self.tree = pt.PrimTree()
        self.tree.addPaths(self.path_list)
        
        for i in range(self.max_length):
            paths = self.tree.getPathsFromDepth(i+1)
            print(f"Number of paths for length {i+1} : {len(paths)}")
            self.path_per_length[str(i+1)] = paths
            
        return True
        
    def onDepthChanged(self, text):
        """Callback every depth in changed in combobox.

        Args:
            text (str): Current depth.
        """        
        
        primsSize = None
        try:
            primsSize = len(self.path_per_length[text])
        except:
            primsSize = 0
        
        
        self.depthLabel.setText(
            f"Number of primitive selected: {primsSize}"
        )
        
    def closeEvent(self, event):
        """
        Event made to unlink this widget from houdini when closed.
        """
        
        self.setParent(None)
        return super().closeEvent(event)        

def run():
    """Small routine to start the UI and link it to houdini window.
    """    
    
    dialog = Blast()
    if dialog.initialize:
        dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        dialog.show()