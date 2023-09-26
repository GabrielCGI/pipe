import os
import sys
from PySide2.QtWidgets import QDialog, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import Qt
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from megaload import megaload_loader1
import importlib
importlib.reload(megaload_loader1)

print("dev")
FolderIcon = r"R:\pipeline\pipe\maya\scripts\megaload\_FolderIcon.png"
EmptyImg = r"R:\pipeline\pipe\maya\scripts\megaload\preview_exemple.png"

class Megaload(QDialog):
    def __init__(self, parent=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(Megaload, self).__init__(parent)

        self.setWindowTitle("Megaload")

        # Set up layout
        self.main_layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()
        self.mid_layout = QHBoxLayout()
        self.but_layout = QHBoxLayout()

        # Set up the UI elements
        self.path_edit = QLineEdit(self)
        self.path_edit.textEdited.connect(self.update_image)

        # Create and set up the "Browser" button
        self.browser_button = QPushButton("", self)
        self.browser_button.setIcon(QIcon(FolderIcon))
        self.browser_button.setMaximumWidth(25)
        self.browser_button.clicked.connect(self.browse_directory)

        # Image display
        self.image_label = QLabel(self)
        pixmap = QPixmap(EmptyImg)
        pixmap = pixmap.scaled(300, 300)

        self.image_label.setPixmap(pixmap)

        self.load_button = QPushButton("Load", self)
        self.load_button.clicked.connect(self.run_loader)

        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.close)

        # Add the UI elements to the layout
        self.top_layout.addWidget(self.path_edit)
        self.top_layout.addWidget(self.browser_button)
        self.mid_layout.addWidget(self.image_label)
        self.but_layout.addWidget(self.load_button)
        self.but_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.mid_layout)
        self.main_layout.addLayout(self.but_layout)
        self.setLayout(self.main_layout)

    def browse_directory(self):
        # Open a directory dialog with a default directory
        directory_path = QFileDialog.getExistingDirectory(self, "Select a directory", "R:/megascan/Downloaded")
        if directory_path:
            self.path_edit.setText(directory_path)
            self.update_image()

    def update_image(self):

        directory = self.path_edit.text()
        if os.path.isdir(directory):
            preview_file = [f for f in os.listdir(directory) if f.endswith("_Preview.png")]
        else:
            preview_file = None
        if preview_file:
            image_path = os.path.join(directory, preview_file[0])
        else:
            image_path = EmptyImg


        pixmap = QPixmap(image_path)
        pixmap = pixmap.scaled(300, 300)
        self.image_label.setPixmap(pixmap)

    def run_loader(self):
        directory = self.path_edit.text()
        if os.path.exists(directory):
            megaload_loader1.run_loader(directory)