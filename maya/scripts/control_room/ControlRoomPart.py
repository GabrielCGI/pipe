from abc import *

import maya.OpenMaya as OpenMaya

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from common.utils import *


class ControlRoomPart(ABC):
    def __init__(self, control_room, name, part_name):
        """
        Constructor
        :param control_room
        :param name
        :param part_name
        """
        self._control_room = control_room
        self._name = name
        self._part_name = part_name
        self._preset_hovered = False

    def create_ui(self):
        """
        Generate the UI of the part
        :return:
        """
        lyt = QVBoxLayout()
        lyt.setSpacing(2)
        lyt.setAlignment(Qt.AlignTop)

        title_label = QLabel(self._name)
        title_label.setContentsMargins(5, 5, 5, 5)
        title_label.setStyleSheet("background-color:#5D5D5D;font-weight:bold")
        lyt.addWidget(title_label, 0, Qt.AlignTop)

        lyt.addLayout(self.populate())
        return lyt

    @abstractmethod
    def populate(self):
        """
        Generate the UI content of the part
        :return:
        """
        pass

    @abstractmethod
    def refresh_ui(self):
        """
        Refresh the part's UI
        :return:
        """
        pass

    @abstractmethod
    def add_callbacks(self):
        """
        Add the callbacks
        :return:
        """
        pass

    @abstractmethod
    def remove_callbacks(self):
        """
        Remove the callbacks
        :return:
        """
        pass

    @abstractmethod
    def add_to_preset(self, preset):
        """
        Generate the part's attributes in the preset
        :param preset:
        :return:
        """
        pass

    @abstractmethod
    def apply(self, preset):
        """
        Apply the preset
        :param preset:
        :return:
        """
        pass
