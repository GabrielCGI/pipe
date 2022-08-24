from maya import OpenMayaUI as omui
from PySide2 import QtCore
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
import maya.cmds as cmds
def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class TestTool(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(TestTool, self).__init__(parent)
        self.qtSignal = QtCore.Signal()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.createUI()
        self.create_connections()
        #################################################################
    def createUI(self):
        self.setWindowTitle("Skin Weights Tool")
        self.setWindowFlags(QtCore.Qt.Tool)
        self.resize(300, 400) # re-size the window
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.jointTitle = QtWidgets.QLabel(" Doctor")
        self.jointTitle.setStyleSheet("color: white;background-color: black;")
        self.jointTitle.setFixedSize(300,30)
        self.jointList = QtWidgets.QListWidget(self)
        self.jointList.resize(300, 300)
        for i in range(10):
            self.jointList.addItem('Item %s' % (i + 1))


        self.skinTitle = QtWidgets.QLabel(" Current Skin Weights")
        self.skinTitle.setStyleSheet("color: white;background-color: black;")
        self.skinTitle.setFixedSize(300,30)

        self.displayInfLabel1 = QtWidgets.QLabel("Inf1");
        self.displayInfLabel2 = QtWidgets.QLabel("Inf2");
        self.displayInfLabel3 = QtWidgets.QLabel("Inf3");
        self.displayInfLabel4 = QtWidgets.QLabel("Inf4");

        self.infLabelLayout = QtWidgets.QHBoxLayout()
        self.infLabelLayout.addWidget(self.displayInfLabel1)
        self.infLabelLayout.addWidget(self.displayInfLabel2)
        self.infLabelLayout.addWidget(self.displayInfLabel3)
        self.infLabelLayout.addWidget(self.displayInfLabel4)

        self.displayWeight1 = QtWidgets.QLineEdit("0");
        self.displayWeight2 = QtWidgets.QLineEdit("0");
        self.displayWeight3 = QtWidgets.QLineEdit("0");
        self.displayWeight4 = QtWidgets.QLineEdit("0");

        self.weightLayout = QtWidgets.QHBoxLayout()
        self.weightLayout.addWidget(self.displayWeight1)
        self.weightLayout.addWidget(self.displayWeight2)
        self.weightLayout.addWidget(self.displayWeight3)
        self.weightLayout.addWidget(self.displayWeight4)

        self.skinWeightGrid = QtWidgets.QGridLayout()
        self.skinWeightGrid.addLayout(self.infLabelLayout, 0, 0)
        self.skinWeightGrid.addLayout(self.weightLayout, 1, 0)

        self.ignoreSubdivision = QtWidgets.QCheckBox("ignoreSubdivision")
        self.color = QtWidgets.QCheckBox("Color")
        self.position = QtWidgets.QCheckBox("Position")
        self.rotation = QtWidgets.QCheckBox("Rotation")

        self.runButton = QtWidgets.QPushButton("Assign")

        self.mainLayout.addWidget(self.jointTitle)
        self.mainLayout.addWidget(self.jointList)
        self.mainLayout.addWidget(self.skinTitle)
        self.mainLayout.addLayout(self.skinWeightGrid)
        self.mainLayout.addWidget(self.ignoreSubdivision)
        self.mainLayout.addWidget(self.color)
        self.mainLayout.addWidget(self.position)
        self.mainLayout.addWidget(self.runButton)

    def create_connections(self):
        self.ignoreSubdivision.clicked.connect(self.ignore)

    def ignore(self):
        print("ignor")
        cmds.setAttr("defaultArnoldRenderOptions.ignoreSubdivision", 1)
def showUI():
    global ui
    try:
        ui.close()
    except:
        pass
    ui = TestTool()
    # useful line of code that gets rid of lots of errors during testing
    ui.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    ui.show()
"""
import importlib
import turbotron_pyside
importlib.reload(turbotron_pyside)
try:
    ui.deleteLater()
except:
    pass
ui= turbotron_pyside.TestTool()
ui.createUI()
ui.show()
"""
