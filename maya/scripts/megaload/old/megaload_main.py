from PySide2 import QtWidgets
import sys
import importlib
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance

from megaload import megaload_ui
from megaload import megaload_loader

importlib.reload(megaload_ui)
importlib.reload(megaload_loader)

class MainController:
    def __init__(self):
        self.main_window = megaload_ui.MainUI()
        self.main_window.load_button.clicked.connect(self.load_3d_action)

    def load_3d_action(self):
        directory = self.main_window.path_edit.text()
        megaload_loader.run_loader(directory)

    def show(self):
        self.main_window.show()
