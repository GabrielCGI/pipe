import sys
from PySide2.QtWidgets import QDialog, QWidget, QVBoxLayout, QLineEdit, QPushButton
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance

from megaload import megaload_loader


class Megaload(QDialog):
    def __init__(self, parent=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(Megaload, self).__init__(parent)


        # Set up layout
        self.layout = QVBoxLayout()


        # Set up the UI elements
        self.path_edit = QLineEdit(self)
        self.load_button = QPushButton("Load", self)
        self.load_button.clicked.connect(self.run_loader)


        # Add the UI elements to the layout
        self.layout.addWidget(self.path_edit)
        self.layout.addWidget(self.load_button)

        self.setLayout(self.layout)

    def run_loader(self):
        directory = self.path_edit.text()
        megaload_loader.run_loader(directory)
        print("DONE")