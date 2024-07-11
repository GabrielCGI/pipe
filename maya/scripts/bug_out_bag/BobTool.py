import maya.cmds as cmds

# Get the Maya version as an integer
maya_version = int(cmds.about(version=True).split()[0])

# Conditional imports based on the Maya version
if maya_version <= 2022:
    # For Maya 2022 and earlier, using PySide2
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from PySide2.QtWidgets import *
    from PySide2.QtCore import *
else:
    # For Maya 2025 and later, using PySide6
    from PySide6 import QtCore
    from PySide6 import QtWidgets
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *

# Continue with your script logic below...


import pymel.core as pm

from .BobElement import *
from .BobCollapsibleWidget import *


class BobTool(BobElement, ABC):
    def __init__(self, name, pref_name, tooltip=""):
        """
        Constructor
        :param name
        :param pref_name
        :param tooltip
        """
        super(BobTool, self).__init__(name)
        self.__tooltip = tooltip
        self._pref_name = pref_name
        self._prefs = None

    def populate(self):
        """
        Populate the UI of the tool
        :return: layout
        """
        layout = QVBoxLayout()
        collapsible = BobCollapsibleWidget(self._name, self._pref_name, self._prefs, bg_color="rgb(50, 50, 50)",
                                           widget_color="rgb(80, 80, 100)", margins=[3, 3, 3, 3])
        collapsible.setToolTip(self.__tooltip)
        layout.addWidget(collapsible)
        return layout

    def on_selection_changed(self):
        """
        By default do nothing on selection changed
        :return:
        """
        pass

    def on_dag_changed(self):
        """
        By default do nothing on dag changed
        :return:
        """
        pass

    def save_prefs(self):
        """
        By default do nothing on prefs saving
        :return:
        """
        pass

    def retrieve_prefs(self):
        """
        By default do nothing on prefs retrieving
        :return:
        """
        pass

    def set_prefs(self, prefs):
        """
        Setter of prefs
        :param prefs
        :return:
        """
        self._prefs = prefs
