import os
import re
import sys

try:
    from PySide2 import QtCore #type: ignore
    from PySide2 import QtGui #type: ignore
    from PySide2 import QtWidgets #type: ignore
    from PySide2.QtWidgets import * #type: ignore
    from PySide2.QtCore import * #type: ignore
    from PySide2.QtGui import * #type: ignore
except:
    try:
        from PySide6 import QtCore
        from PySide6 import QtGui
        from PySide6 import QtWidgets
        from PySide6.QtWidgets import *
        from PySide6.QtCore import *
        from PySide6.QtGui import *
    except:
        sys.exit(1)

from common.utils import *
from common.Prefs import *
import nuke
from .AutoCompFactory import AutoCompFactory
from .ShuffleMode import ShuffleMode

# ######################################################################################################################
_COLOR_GREY_DISABLE = 105,105,105
# ######################################################################################################################

class AutoComp(QWidget):
    
    def __init__(self, prt=None):
        super(AutoComp, self).__init__(prt)
        self.__selected_channels = []
        self.__selected_read_node = None
        # UI attributes
        self.__ui_width = 400
        self.__ui_height = 150
        self.__ui_min_width = 250
        self.__ui_min_height = 150
        
        if qVersion() >= "5.14.0":
            self.__ui_pos = QGuiApplication.primaryScreen().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2
        else:
            self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2 # type: ignore


        # name the window
        self.setWindowTitle("AutoComp")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()

    def showEvent(self, arg__1):
        """
        Add callbacks
        :return:
        """
        self.remove_callbacks()
        nuke.addKnobChanged(self.__on_read_node_selected, nodeClass="Read")
        self.__on_read_node_selected()

    def remove_callbacks(self):
        """
        Remove callbacks
        :return:
        """
        try:
            reads_callbacks = nuke.knobChangeds["Read"]
            for read_callback in reads_callbacks:
                read_function = read_callback[0]
                if read_function.__name__ == "__on_read_node_selected":
                    nuke.removeKnobChanged(read_function, nodeClass="Read")
        except:
            return

    @staticmethod
    def __get_header_ui(title, button = None):
        """
        Generate a header layout for a subpart (with hline and facultative button)
        :param title
        :param button
        :return: header
        """
        header = QHBoxLayout()
        line = QFrame()
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Raised)
        header.addWidget(line)
        lbl_shot_to_autocomp = QLabel(title)
        header.addWidget(lbl_shot_to_autocomp)
        if button is not None:
            lbl_shot_to_autocomp.setContentsMargins(15, 0, 0, 0)
            button.setContentsMargins(0,0,15,0)
            header.addWidget(button)
        else:
            lbl_shot_to_autocomp.setContentsMargins(15, 0, 15, 0)
        line = QFrame()
        line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Raised)
        header.addWidget(line)
        return header

    def __create_ui(self):
        """
        Create the ui
        :return:
        """
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setSpacing(10)
        main_lyt.setAlignment(Qt.AlignTop)
        self.setLayout(main_lyt)

        # SHUFFLE READ CHANNEL PART

        shuffle_read_channel_lyt = QVBoxLayout()
        shuffle_read_channel_lyt.setSpacing(8)
        shuffle_read_channel_lyt.setContentsMargins(0, 0, 0, 15)
        main_lyt.addLayout(shuffle_read_channel_lyt)

        shuffle_read_channel_lyt.addLayout(AutoComp.__get_header_ui("Shuffle Read Channel"))

        self.__ui_lbl_selected_read_node = QLineEdit()
        self.__ui_lbl_selected_read_node.setPlaceholderText("Read node selected name")
        self.__ui_lbl_selected_read_node.setReadOnly(True)
        self.__ui_lbl_selected_read_node.setAlignment(Qt.AlignCenter)
        self.__ui_lbl_selected_read_node.setStyleSheet("font-weight:bold")
        shuffle_read_channel_lyt.addWidget(self.__ui_lbl_selected_read_node)

        self.__ui_channel_list = QListWidget()
        self.__ui_channel_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_channel_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.__ui_channel_list.itemSelectionChanged.connect(self.__on_channel_selected)
        shuffle_read_channel_lyt.addWidget(self.__ui_channel_list)

        self.__ui_shuffle_channel_btn = QPushButton("Shuffle selected channels")
        self.__ui_shuffle_channel_btn.setFixedHeight(30)
        self.__ui_shuffle_channel_btn.clicked.connect(self.__shuffle_channel)
        shuffle_read_channel_lyt.addWidget(self.__ui_shuffle_channel_btn)

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__refresh_shuffle_channel_btn()


    def __refresh_read_node_ui(self):
        """
        Refresh the channel list of the selected read node
        :return:
        """
        self.__ui_channel_list.clear()
        if self.__selected_read_node is not None:
            self.__ui_lbl_selected_read_node.setText(self.__selected_read_node.name())

            lg_channels = ShuffleMode.get_light_group_channels(self.__selected_read_node)
            present_channels = ShuffleMode.get_present_channels(self.__selected_read_node)
            self.__ui_channel_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
            for channel in lg_channels:
                item: QListWidgetItem = QListWidgetItem(channel)
                item.setData(Qt.UserRole, channel)
                if channel in present_channels:
                    item.setForeground(QColor(*_COLOR_GREY_DISABLE))
                self.__ui_channel_list.addItem(item)
        else:
            self.__ui_lbl_selected_read_node.setText("")

    def __refresh_shuffle_channel_btn(self):
        """
        Refresh the shuffle channel button
        :return:
        """
        self.__ui_shuffle_channel_btn.setEnabled(len(self.__selected_channels) > 0)

    def __on_channel_selected(self):
        """
        On Channel selected retrieve selected and refresh the shuffle channel button
        :return:
        """
        items = self.__ui_channel_list.selectedItems()
        del self.__selected_channels[:]
        for item in items:
            self.__selected_channels.append(item.data(Qt.UserRole))
        self.__refresh_shuffle_channel_btn()

    def __on_read_node_selected(self):
        """
        On Read Node selected in the Graph change the selected read node and refresh the ui
        :return:
        """
        try:
            node = nuke.thisNode()
            knob = nuke.thisKnob()
        except:
            return
        if knob is not None and knob.name() == "selected" and node.Class() == "Read" and node.isSelected():
            self.__selected_read_node = node
        else:
            read_nodes_selected = nuke.selectedNodes("Read")
            if len(read_nodes_selected) == 0:
                self.__selected_read_node = None
            else:
                self.__selected_read_node = read_nodes_selected[0]
        self.__refresh_read_node_ui()

    def __shuffle_channel(self):
        """
        Shuffle selected channels of the selected read node
        :return:
        """
        undo = nuke.Undo()
        undo.begin()
        try:
            AutoCompFactory.shuffle_channel_mode(self.__selected_read_node, self.__selected_channels)
            undo.end()
        except:
            undo.end()