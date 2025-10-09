
from PySide6.QtCore import Qt
import hou

try:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from PySide2 import QtGui
    QT_FOUND = True
except:
    try:
        from PySide6 import QtCore
        from PySide6 import QtWidgets
        from PySide6 import QtGui
        QT_FOUND = True
    except:
        QT_FOUND = False
        
        

class SliderLineEdit(QtWidgets.QLineEdit):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mouse event
        self.middleMousePressed = False
    
    def valueChanged(self, newValue):
        self.setText(str(newValue))
        
    def mousePressEvent(self, event):
        
        if event.button() == QtCore.Qt.MouseButton.MiddleButton:
            
            if self.text() == "":
                currentValue = 0
            else:
                try:
                    currentValue = float(self.text())
                except:
                    return
                
            try:
                hou.ui.openValueLadder(
                    initial_value=currentValue,
                    value_changed_callback=self.valueChanged)
            except hou.OperationFailed:
                return
            
            self.middleMousePressed = True
            
    def mouseMoveEvent(self, event):
        if self.middleMousePressed:
            hou.ui.updateValueLadder(
                event.globalX(),
                event.globalY(),
                bool(event.modifiers() & QtCore.Qt.AltModifier),
                bool(event.modifiers() & QtCore.Qt.ShiftModifier)
            )
    
    def mouseReleaseEvent(self, event):
        if (event.button() == QtCore.Qt.MiddleButton
            and self.middleMousePressed):
            hou.ui.closeValueLadder()
            self.middleMousePressed = False
    
class NodesSetter(QtWidgets.QMainWindow):
    
    """Basic form widget to modify a parm value in houdini.

    Args:
        QtWidgets (QtWidgets.QMainWindow): inherits from a QMainWindow.
    """    
    
    def __init__(self, selectedNodes: list[hou.OpNode], parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Set nodes parameters")
        self.setMinimumSize(400, 160)
        
        self.selectedNodes: list[hou.OpNode] = selectedNodes
        self.parm = ""
        self.parmLabel = ""
        
        self.intializeLayout()
        self.setDetailsMenu()
            
    def intializeLayout(self):
        """
        Initialize global widget form.
        """
        self.vbox = QtWidgets.QVBoxLayout()
        self.formLayout = QtWidgets.QFormLayout()
        
        parmLabel = QtWidgets.QLabel("<h4>Parameter to edit :</h4>")
        self.parmEdit = QtWidgets.QLineEdit()
        self.parmEdit.setMinimumWidth(150)
        self.parmEdit.setText(self.parmLabel)
        self.formLayout.addRow(parmLabel, self.parmEdit)
        
        parmSelectButton = QtWidgets.QPushButton("Select a parameters...")
        parmSelectButton.clicked.connect(self.selectParm)
        self.formLayout.addRow(parmSelectButton)
        
        # Multiply Line
        mulHbox = QtWidgets.QHBoxLayout()
        
        mulLabel = QtWidgets.QLabel("<h4>Value to Multiply :</h4>")
        mulHbox.addWidget(mulLabel)
        
        self.mulEdit = SliderLineEdit()
        self.mulEdit.setToolTip("Value to multiply to the current "
                                "parameters value (use the reciprocal to divide)")
        mulHbox.addWidget(self.mulEdit)
        
        mulButton = QtWidgets.QPushButton("Multiply")
        mulButton.clicked.connect(self.multiply)
        mulButton.setMinimumWidth(80)
        mulHbox.addWidget(mulButton)
        
        self.formLayout.addRow(mulHbox)
        
        # Add Line
        addHbox = QtWidgets.QHBoxLayout()
        
        addLabel = QtWidgets.QLabel("<h4>Value to add:</h4>")
        addHbox.addWidget(addLabel)
        
        self.addEdit = SliderLineEdit()
        self.addEdit.setToolTip("Value to add to the current "
                         "parameters value (use the opposite to substract)")
        addHbox.addWidget(self.addEdit)
        
        addButton = QtWidgets.QPushButton("Add")
        addButton.clicked.connect(self.add)
        addButton.setMinimumWidth(80)
        addHbox.addWidget(addButton)
        
        self.formLayout.addRow(addHbox)
        
        self.adaptSize(mulLabel, addLabel)
        
        # Animation
        self.animation = QtCore.QPropertyAnimation(self, b"size")
        self.animation.setDuration(300) 
        
        self.vbox.addLayout(self.formLayout)
        
        central = QtWidgets.QWidget()
        central.setLayout(self.vbox)
        self.setCentralWidget(central)  
    
    def setDetailsMenu(self):
        """Setup logs menu.
        """        
        
        toggleDetails = QtWidgets.QCheckBox("Show Details")
        toggleDetails.stateChanged.connect(self.toggleDetails)
        
        self.formLayout.addRow(toggleDetails)
        
        self.details = QtWidgets.QWidget()
        self.details.setVisible(False)
        self.details.setMinimumHeight(400)
        self.vbox.addWidget(self.details)
        
        vboxDetail = QtWidgets.QVBoxLayout()
        vboxDetail.setAlignment(QtCore.Qt.AlignCenter)
        
        changeLog = QtWidgets.QWidget()
        changeLog.setObjectName("changelog")
        changeLog.setStyleSheet("#changelog {background: #131313;}")
        changeLog.setMinimumSize(300, 300)
        vboxDetail.addWidget(changeLog)
        
        vboxChangeLog = QtWidgets.QVBoxLayout()
        changeLog.setLayout(vboxChangeLog)
        vboxChangeLog.setAlignment(QtCore.Qt.AlignTop)
        
        self.logsLabel = QtWidgets.QLabel()
        vboxChangeLog.addWidget(self.logsLabel)
        
        self.details.setLayout(vboxDetail)
        
        self.updateLog()
        
    def updateLog(self):
        """
        Update log with current value of selected parameters.
        """
        
        logs = ""
        
        if self.parm == "":
            logs = "No parameters selected"
        else:
            logs = f"{self.parmLabel}:\n"
            
            for node in self.selectedNodes:
                logs += f"{node.name()} = {node.parm(self.parm.name()).eval():.4f}\n"
        self.logsLabel.setText(logs)
        
    def toggleDetails(self, state):
        """Callback to hide or unhide logs.

        Args:
            state (int): Checkbox state.
        """        
        
        detailsSize = 400
        if state:
            self.details.setVisible(True)
            offset = self.minimumHeight() + detailsSize
            self.setMinimumHeight(offset)
            self.animate_resize(self.minimumHeight(), offset)
        else:
            offset = self.minimumHeight() - detailsSize
            self.setMinimumHeight(offset)
            self.animate_resize(self.minimumHeight(), offset)
            self.details.setVisible(False)
                
    def adaptSize(self, widget1: QtWidgets.QLabel, widget2: QtWidgets.QLabel):
        """Adapt widget label width to have the same size as the largest one.

        Args:
            widget1 (QtWidgets.QLabel): One label.
            widget2 (QtWidgets.QLabel): The other label.
        """        
        
        fontMetrics1 = QtGui.QFontMetrics(widget1.font())
        fontMetrics2 = QtGui.QFontMetrics(widget2.font())
        
        text_width1 = fontMetrics1.horizontalAdvance(widget1.text())
        text_width2 = fontMetrics2.horizontalAdvance(widget2.text())
        
        text_width = max(text_width1, text_width2)
        
        widget1.setMinimumWidth(text_width - 50)
        widget2.setMinimumWidth(text_width - 50)
        
    def animate_resize(self, from_size, to_size):
        """Animate resize.

        Args:
            from_size (int): initial size
            to_size (int): new size
        """        
        
        self.animation.setStartValue(from_size)
        self.animation.setEndValue(to_size)
        self.animation.start()

    def add(self):
        """
        Add value of every selected nodes parameters if it exists.
        """
        
        if self.parm == "":
            hou.ui.displayMessage("No parameter selected")
            return
        
        for node in self.selectedNodes:
            parm = node.parm(self.parm.name())
            if (parm is not None 
                and parm.parmTemplate().type() == hou.parmTemplateType.Float):
                try:
                    addValue = float(self.addEdit.text())
                except:
                    hou.ui.displayMessage(
                        text="Please enter a numerical value",
                        severity=hou.severityType.Message)
                    return
                parmvalue = float(parm.eval())
                parm.set(parmvalue + addValue)  
        self.updateLog()
         
    def multiply(self):
        """
        Multiply value of every selected nodes parameters if it exists.
        """        
        
        if self.parm == "":
            hou.ui.displayMessage("No parameter selected")
            return
        
        for node in self.selectedNodes:
            parm = node.parm(self.parm.name())
            if (parm is not None 
                and parm.parmTemplate().type() == hou.parmTemplateType.Float):
                try:
                    mulValue = float(self.mulEdit.text())
                except:
                    hou.ui.displayMessage(
                        text="Please enter a numerical value",
                        severity=hou.severityType.Message)
                    return
                parmvalue = float(parm.eval())
                parm.set(parmvalue * mulValue)       
        self.updateLog()
        
    def selectParm(self):
        """
        Open houdini dialog to select a parm.
        """
        
        # Get every parameters that has a readable label and use floats
        parms_list: list[hou.Parm] = []
        for parm in self.selectedNodes[0].parms():
            if (parm.parmTemplate().label()
                and parm.parmTemplate().type() == hou.parmTemplateType.Float):
                parms_list.append(parm)
                
        
        parms_label = [p.parmTemplate().label() for p in parms_list]
        
        tuple_list = []
        for i, parm_label in enumerate(parms_label):
            if parms_label.count(parm_label) > 1:
                tuple_list.append(parm_label)
            
            if parm_label in tuple_list:
                parms_label[i] = f"{parm_label} ({parms_list[i].name()})"

        selectedParms = hou.ui.selectFromList(
            choices=parms_label, title="Select a parameter",
            column_header="Parameters", exclusive=True, sort=True)
        
        
        if len(selectedParms):
            self.parm = parms_list[selectedParms[0]]
            self.parmLabel = parms_label[selectedParms[0]]
            self.parmEdit.setText(self.parmLabel)
            self.updateLog()
                
    def closeEvent(self, event):
        """
        Event made to unlink this widget from houdini when closed.
        """
        
        self.setParent(None)
        return super().closeEvent(event)             
        
def showUI():
    """
    Basic routine to initialize the dialog.
    """
    
    if not QT_FOUND:
        hou.ui.displayMessage(
            "Error: No QT Found",
            severity=hou.severityType.Error
        )
        return
    
    selectedNodes = hou.selectedNodes()
    
    if len(selectedNodes) == 0:
        hou.ui.displayMessage(
            "Please select at least 1 node",
            severity=hou.severityType.Message)
        return
        
    dialog = NodesSetter(selectedNodes)
    dialog.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    dialog.show()