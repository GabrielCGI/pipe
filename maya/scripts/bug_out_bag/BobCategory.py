import maya.cmds as cmds

# Get the Maya version as an integer
maya_version = int(cmds.about(version=True).split()[0])

# Define the import based on the Maya version
if maya_version <= 2022:
    # For Maya 2022 and earlier, using PySide2 and Shiboken2
    from PySide2 import QtCore
    from PySide2 import QtGui
    from PySide2 import QtWidgets
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
    from shiboken2 import wrapInstance
else:
    # For Maya 2025 and later, using PySide6 and Shiboken6
    from PySide6 import QtCore
    from PySide6 import QtGui
    from PySide6 import QtWidgets
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from shiboken6 import wrapInstance
    
import common.utils
from .BobElement import *
from .BobCollapsibleWidget import *


class BobCategory(BobElement):
    def __init__(self, name, prefs, bob_tools):
        """
        Constructor
        :param name
        :param prefs
        :param bob_tools : array of tools
        """
        super().__init__(name)
        self.__prefs = prefs
        self._bob_tools = bob_tools
        for bob_tool in bob_tools:
            bob_tool.set_prefs(self.__prefs)

    def populate(self):
        """
        Populate the category UI
        :return:
        """
        scroll = QScrollArea()
        scroll.setFocusPolicy(Qt.NoFocus)
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(3, 6, 3, 8)
        layout.setSpacing(5)

        for bob_tool in self._bob_tools:
            layout_tool = bob_tool.populate()
            layout.addLayout(layout_tool)

        layout.addStretch(1)

        widget.setLayout(layout)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        return scroll

    def on_selection_changed(self):
        """
        Distribute the selection changed event to tools
        :return:
        """
        for bob_tool in self._bob_tools:
            bob_tool.on_selection_changed()

    def on_dag_changed(self):
        """
        Distribute the dag changed event to tools
        :return:
        """
        for bob_tool in self._bob_tools:
            bob_tool.on_dag_changed()

    def save_prefs(self):
        """
        Distribute the save prefs function to tools
        :return:
        """
        for bob_tool in self._bob_tools:
            bob_tool.save_prefs()

    def retrieve_prefs(self):
        """
        Distribute the retrieve prefs function to tools
        :return:
        """
        for bob_tool in self._bob_tools:
            bob_tool.retrieve_prefs()
