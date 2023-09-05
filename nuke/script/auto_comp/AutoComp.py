import os
import re
import sys

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from functools import partial
from shiboken2 import wrapInstance

from common.utils import *
from common.Prefs import *
import nuke
from nukescripts import panels
from .AutoCompFactory import AutoCompFactory
from .ShuffleMode import ShuffleMode
from .UnpackMode import UnpackMode

# ######################################################################################################################

_FILE_NAME_PREFS = "auto_comp"

_DEFAULT_SHOT_DIR = "I:/"

_UNPACK_MODES_DIR = os.path.dirname(__file__) + "/mode"

_COLOR_GREY_DISABLE = 105,105,105


# ######################################################################################################################


class AutoComp(QWidget):
    @staticmethod
    def __is_correct_shot_folder(folder):
        """
        Test if a folder is a correct shot path
        :param folder
        :return: is correct shot folder
        """
        return os.path.isdir(os.path.join(folder, "render_out")) and os.path.isdir(folder)

    def __init__(self, prt=None):
        super(AutoComp, self).__init__(prt)
        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__shot_path = r""
        # self.__shot_path = ""
        self.__unpack_modes = []
        self.__selected_unpack_mode = None
        self.__selected_layers = []
        self.__selected_channels = []
        self.__selected_read_node = None
        self.__read_nodes_list_for_update = []
        self.__selected_read_nodes_for_update_data = []

        self.__retrieve_unpack_modes(_UNPACK_MODES_DIR)

        # UI attributes
        self.__ui_width = 400
        self.__ui_height = 150
        self.__ui_min_width = 250
        self.__ui_min_height = 150
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()
        self.__retrieve_default_unpack_mode()
        self.__retrieve_read_nodes_to_update()

        self.__scan_layers()

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

    def hideEvent(self, arg__1):
        """
        Save preferences on hide
        :return:
        """
        # self.remove_callbacks()
        self.__save_prefs()

    def remove_callbacks(self):
        """
        Remove callbacks
        :return:
        """
        nuke.removeKnobChanged(self.__on_read_node_selected, nodeClass="Read")

    def __save_prefs(self):
        """
        Save preferences
        :return:
        """
        if self.__selected_unpack_mode is not None:
            self.__prefs["unpack_mode"] = self.__selected_unpack_mode.get_name()

    def __retrieve_prefs(self):
        """
        Retrieve preferences
        :return:
        """
        self.__retrieve_unpack_mode_prefs()

    def __retrieve_unpack_mode_prefs(self):
        """
        Retrieve the mode stored in preferences
        :return:
        """
        if "unpack_mode" in self.__prefs:
            sel_unpack_mode_name = self.__prefs["unpack_mode"]
            for unpack_mode in self.__unpack_modes:
                if unpack_mode.get_name() == str(sel_unpack_mode_name):
                    self.__selected_unpack_mode = unpack_mode
                    break

    def __retrieve_unpack_modes(self, unpack_mode_dir):
        """
        Retrieve all the modes in mode config files
        :param unpack_mode_dir
        :return:
        """
        del self.__unpack_modes[:]
        for unpack_mode_filename in os.listdir(unpack_mode_dir):
            if not unpack_mode_filename.endswith(".json"):
                continue
            unpack_mode_filepath = os.path.join(unpack_mode_dir, unpack_mode_filename)
            if not os.path.isfile(unpack_mode_filepath):
                continue
            unpack_mode = AutoCompFactory.get_unpack_mode(unpack_mode_filepath)
            if unpack_mode is not None:
                self.__unpack_modes.append(unpack_mode)

    def __retrieve_default_unpack_mode(self):
        """
        Retrieve the default Unpack Mode
        :return:
        """
        if self.__selected_unpack_mode is None and len(self.__unpack_modes) > 0:
            self.__selected_unpack_mode = self.__unpack_modes[0]

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

        browse_icon_path = os.path.dirname(__file__) + "/assets/browse.png"
        reload_icon_path = os.path.dirname(__file__) + "/assets/reload.png"

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setSpacing(10)
        main_lyt.setAlignment(Qt.AlignTop)
        self.setLayout(main_lyt)

        # SHOT TO AUTOCOMP PART

        shot_to_autocomp_lyt = QVBoxLayout()
        shot_to_autocomp_lyt.setSpacing(8)
        shot_to_autocomp_lyt.setContentsMargins(0, 0, 0, 15)
        main_lyt.addLayout(shot_to_autocomp_lyt)

        shot_path_lyt = QVBoxLayout()
        shot_path_lyt.setAlignment(Qt.AlignCenter)
        shot_to_autocomp_lyt.addLayout(shot_path_lyt)

        shot_path_lyt.addLayout(AutoComp.__get_header_ui("Shot to AutoComp"))

        browse_shot_path_lyt = QHBoxLayout()
        shot_path_lyt.addLayout(browse_shot_path_lyt)

        self.__ui_shot_path = QLineEdit(self.__shot_path)
        self.__ui_shot_path.setPlaceholderText("Path of the shot to AutoComp")
        self.__ui_shot_path.textChanged.connect(self.__on_folder_changed)
        browse_shot_path_lyt.addWidget(self.__ui_shot_path)

        browse_btn = QPushButton()
        browse_btn.setIconSize(QtCore.QSize(18, 18))
        browse_btn.setFixedSize(QtCore.QSize(24, 24))
        browse_btn.setIcon(QIcon(QPixmap(browse_icon_path)))
        browse_btn.clicked.connect(partial(self.__browse_folder))
        browse_shot_path_lyt.addWidget(browse_btn)

        unpack_mode_lyt = QVBoxLayout()
        unpack_mode_lyt.setSpacing(5)
        unpack_mode_lyt.setAlignment(Qt.AlignTop)
        shot_to_autocomp_lyt.addLayout(unpack_mode_lyt)

        lbl_unpack_mode = QLabel("Unpack Mode")
        unpack_mode_lyt.addWidget(lbl_unpack_mode)

        self.__ui_unpack_mode = QComboBox()
        for unpack_mode in self.__unpack_modes:
            if unpack_mode.is_valid():
                self.__ui_unpack_mode.addItem(unpack_mode.get_name(), userData=unpack_mode)
        self.__ui_unpack_mode.currentIndexChanged.connect(self.__on_unpack_mode_changed)
        unpack_mode_lyt.addWidget(self.__ui_unpack_mode)

        content_shot_autocomp_lyt = QGridLayout()
        content_shot_autocomp_lyt.setSpacing(5)
        shot_to_autocomp_lyt.addLayout(content_shot_autocomp_lyt)

        content_shot_autocomp_lyt.addWidget(QLabel("Layer found [Layer Type]"),0,1)
        content_shot_autocomp_lyt.addWidget(QLabel("Layer Types"),0,0)

        self.__ui_start_vars_list = QListWidget()
        self.__ui_start_vars_list.setStyleSheet("QListWidget::item{padding: 3px;}")
        self.__ui_start_vars_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.__ui_start_vars_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        content_shot_autocomp_lyt.addWidget(self.__ui_start_vars_list,1,0)

        self.__ui_layers_list = QListWidget()
        self.__ui_layers_list.setStyleSheet("QListWidget::item{padding: 3px;}")
        self.__ui_layers_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_layers_list.itemSelectionChanged.connect(self.__on_layer_selected)
        self.__ui_layers_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        content_shot_autocomp_lyt.addWidget(self.__ui_layers_list,1,1)


        self.__ui_autocomp_btn = QPushButton("AutoComp")
        self.__ui_autocomp_btn.setFixedHeight(25)
        self.__ui_autocomp_btn.clicked.connect(self.__unpack)
        content_shot_autocomp_lyt.addWidget(self.__ui_autocomp_btn, 2, 0)

        self.__ui_shuffle_layer_btn = QPushButton("Shuffle selected layer")
        self.__ui_shuffle_layer_btn.setFixedHeight(25)
        self.__ui_shuffle_layer_btn.clicked.connect(self.__shuffle_layer)
        content_shot_autocomp_lyt.addWidget(self.__ui_shuffle_layer_btn,2,1)

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

        # UPDATE READS PART

        update_reads_lyt = QVBoxLayout()
        update_reads_lyt.setSpacing(8)
        update_reads_lyt.setContentsMargins(0, 0, 0, 15)
        main_lyt.addLayout(update_reads_lyt)

        refresh_reads_to_update_btn = QPushButton()
        refresh_reads_to_update_btn.setIconSize(QtCore.QSize(16, 16))
        refresh_reads_to_update_btn.setFixedSize(QtCore.QSize(24, 24))
        refresh_reads_to_update_btn.setIcon(QIcon(QPixmap(reload_icon_path)))
        refresh_reads_to_update_btn.clicked.connect(partial(self.__refresh_read_nodes_to_update))

        update_reads_lyt.addLayout(AutoComp.__get_header_ui("Update Reads", button = refresh_reads_to_update_btn))

        self.__ui_read_nodes_table = QTableWidget(0, 4)
        self.__ui_read_nodes_table.setHorizontalHeaderLabels(["Name","Layer", "Actual", "Last"])
        self.__ui_read_nodes_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        self.__ui_read_nodes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.__ui_read_nodes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_read_nodes_table.verticalHeader().hide()
        self.__ui_read_nodes_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_read_nodes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_read_nodes_table.itemSelectionChanged.connect(self.__on_read_node_list_item_selected)
        update_reads_lyt.addWidget(self.__ui_read_nodes_table)

        self.__ui_update_reads_btn = QPushButton("Update selected read nodes")
        self.__ui_update_reads_btn.setFixedHeight(30)
        self.__ui_update_reads_btn.clicked.connect(self.__update_read)
        update_reads_lyt.addWidget(self.__ui_update_reads_btn)

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__refresh_shot_autocomp_btn()
        self.__refresh_unpack_modes()
        self.__refresh_layers_list()
        self.__refresh_start_vars_list()
        self.__refresh_read_node_ui()
        self.__refresh_shuffle_channel_btn()
        self.__refresh_update_reads_table()
        self.__refresh_update_read_node_btn()

    def __refresh_shot_autocomp_btn(self):
        """
        Refresh all the button of the shot to autocomp part
        :return:
        """
        self.__refresh_shuffle_layer_btn()
        self.__refresh_autocomp_btn()

    def __refresh_shuffle_layer_btn(self):
        """
        Refresh the shuffle layer button
        :return:
        """
        self.__ui_shuffle_layer_btn.setEnabled(
            len(self.__selected_layers) > 0 and self.__selected_unpack_mode is not None and
            os.path.isdir(os.path.join(self.__shot_path, "render_out")))

    def __refresh_autocomp_btn(self):
        """
        Refresh the autocomp button
        :return:
        """
        self.__ui_autocomp_btn.setEnabled(
            self.__selected_unpack_mode is not None and os.path.isdir(os.path.join(self.__shot_path, "render_out")))

    def __refresh_unpack_modes(self):
        """
        Refresh the unpack mode combobox
        :return:
        """
        for index in range(self.__ui_unpack_mode.count()):
            if self.__ui_unpack_mode.itemData(index, Qt.UserRole) == self.__selected_unpack_mode:
                self.__ui_unpack_mode.setCurrentIndex(index)

    def __refresh_layers_list(self):
        """
        Refresh the layer start var list of the current mode
        :return:
        """
        self.__ui_layers_list.clear()
        # Check existence shot path
        if not os.path.isdir(self.__shot_path): return

        if self.__shot_path.endswith("render_out"):
            render_path = self.__shot_path
        else:
            render_path = os.path.join(self.__shot_path, "render_out")

        # Check existence render path
        if not os.path.isdir(render_path): return

        # Check Unpack Mode valid
        if self.__selected_unpack_mode is None: return

        for render_layer in os.listdir(render_path):
            item = QListWidgetItem()
            # Check layer folder contains shot
            if UnpackMode.get_last_seq_from_layer(os.path.join(render_path, render_layer)) is None: continue
            start_var = self.__selected_unpack_mode.is_layer_scanned(render_layer)
            # Determine if known layer or unknown
            if not start_var:
                name = render_layer
                item.setTextColor(QColor(170,170,255))
            else:
                name = render_layer + "   ["+start_var.get_name()+"]"

            item.setData(Qt.UserRole, render_layer)
            item.setText(name)
            self.__ui_layers_list.addItem(item)

    def __refresh_start_vars_list(self):
        """
        Refresh the layer start var list of the current mode
        :return:
        """
        self.__ui_start_vars_list.clear()
        if self.__selected_unpack_mode is not None:
            start_vars = [var for var in self.__selected_unpack_mode.get_var_set().get_start_vars()]
            for var in start_vars:
                var_str = str(var)
                item = QListWidgetItem()
                item.setData(Qt.UserRole, var)
                item.setText(var_str)
                self.__ui_start_vars_list.addItem(item)
                if not self.__selected_unpack_mode.is_layer_name_scanned(var_str):
                    item.setTextColor(QColor(150,150,150))

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
                item = QListWidgetItem(channel)
                item.setData(Qt.UserRole, channel)
                if channel in present_channels:
                    item.setTextColor(QColor(*_COLOR_GREY_DISABLE))
                self.__ui_channel_list.addItem(item)
        else:
            self.__ui_lbl_selected_read_node.setText("")

    def __refresh_shuffle_channel_btn(self):
        """
        Refresh the shuffle channel button
        :return:
        """
        self.__ui_shuffle_channel_btn.setEnabled(len(self.__selected_channels) > 0)

    def __refresh_update_read_node_btn(self):
        """
        Refresh the Update Reads Node button
        :return:
        """
        self.__ui_update_reads_btn.setEnabled(len(self.__selected_read_nodes_for_update_data) > 0)

    def __refresh_update_reads_table(self):
        """
        Refresh the Update Reads Table
        :return:
        """
        self.__ui_read_nodes_table.setRowCount(0)
        row_index = 0
        for layer, current_version, last_version, last_version_path, read_node in self.__read_nodes_list_for_update:
            self.__ui_read_nodes_table.insertRow(row_index)

            name_item = QTableWidgetItem(read_node.name())
            if current_version == last_version:
                name_item.setData(Qt.UserRole, (read_node, None))
            else:
                name_item.setData(Qt.UserRole, (read_node, last_version_path))
            self.__ui_read_nodes_table.setItem(row_index, 0, name_item)

            layer_item = QTableWidgetItem(layer)
            layer_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 1, layer_item)

            current_version_item = QTableWidgetItem(current_version)
            current_version_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 2, current_version_item)

            last_version_item = QTableWidgetItem(last_version)
            last_version_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 3, last_version_item)

            if current_version == last_version:
                name_item.setTextColor(QColor(*_COLOR_GREY_DISABLE))
                layer_item.setTextColor(QColor(*_COLOR_GREY_DISABLE))
                current_version_item.setTextColor(QColor(*_COLOR_GREY_DISABLE))
                last_version_item.setTextColor(QColor(*_COLOR_GREY_DISABLE))

    def __browse_folder(self):
        """
        Browse a new abc folder
        :return:
        """
        dirname = nuke.root()['name'].value()
        if len(dirname) == 0:
            dirname = _DEFAULT_SHOT_DIR
        shot_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Shot Directory", dirname)
        self.__set_shot_path(shot_path)

    def __set_shot_path(self, shot_path):
        """
        Check and set a new shot path
        :param shot_path
        :return:
        """
        if AutoComp.__is_correct_shot_folder(shot_path) and shot_path != self.__shot_path:
            self.__ui_shot_path.setText(shot_path)

    def __on_folder_changed(self):
        """
        Retrieve the folder path on folder linedit change
        :return:
        """
        self.__shot_path = self.__ui_shot_path.text()
        self.__scan_layers()
        self.__refresh_shot_autocomp_btn()
        self.__refresh_start_vars_list()
        self.__refresh_layers_list()

    def __on_unpack_mode_changed(self, index):
        """
        On Unpack Mode combobox value changed retrieve the datas of the mode and rescan layers
        :param index
        :return:
        """
        self.__selected_unpack_mode = self.__ui_unpack_mode.itemData(index, Qt.UserRole)
        self.__scan_layers()
        self.__refresh_start_vars_list()
        self.__refresh_layers_list()
        self.__selected_layers = []
        self.__refresh_shuffle_layer_btn()

    def __on_layer_selected(self):
        """
        On Layer selected refresh the shuffle layer button
        :return:
        """
        self.__selected_layers = []
        for item in self.__ui_layers_list.selectedItems():
            self.__selected_layers.append(item.data(Qt.UserRole))
        self.__refresh_shuffle_layer_btn()

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

    def __on_read_node_list_item_selected(self):
        """
        On Read Node selected in Update Reads Table Retrieve selected and refresh the update button
        :return:
        """
        rows_selected = self.__ui_read_nodes_table.selectionModel().selectedRows()
        del self.__selected_read_nodes_for_update_data[:]
        for row_selected in rows_selected:
            self.__selected_read_nodes_for_update_data.append(
                self.__ui_read_nodes_table.item(row_selected.row(), 0).data(Qt.UserRole))
        for node in nuke.allNodes():
            node.setSelected(False)
        unknown_node_found = False
        for node, version_path in self.__selected_read_nodes_for_update_data:
            try:
                node.setSelected(True)
            except:
                unknown_node_found = True
                break
        if unknown_node_found:
            self.__retrieve_read_nodes_to_update()
            self.__refresh_update_reads_table()
        self.__refresh_update_read_node_btn()

    def __refresh_read_nodes_to_update(self):
        """
        Retrieve the read nodes and refresh the tables
        :return:
        """
        self.__retrieve_read_nodes_to_update()
        self.__refresh_update_reads_table()

    def __retrieve_read_nodes_to_update(self):
        """
        Refresh the read nodes list for the Update Reads Part
        :return:
        """
        del self.__read_nodes_list_for_update[:]
        read_nodes = nuke.allNodes("Read")
        for read_node in read_nodes:
            path = read_node.knob("file").value().replace("\\", "/")
            # Check the current path to retrieve the layer and current version
            match = re.match(r"^([\w\/\:\.]+\/render_out\/(\w+))\/\w+\.([0-9]+)\/[\w\.%]+\.[a-z]+$", path)
            if not match: continue
            folder_versions = match.group(1)
            if not os.path.isdir(folder_versions): continue
            versions = sorted(os.listdir(folder_versions), reverse=True)
            last_version = None
            last_version_path = None
            # Retrieve the last version for the layer found
            for version_dirname in versions:
                version_dirpath = os.path.join(folder_versions,version_dirname)
                for seq_file in os.listdir(version_dirpath):
                    match_version = re.match(r"^("+version_dirname+")\.[0-9]{4}(\.\w+)$", seq_file)
                    if match_version is not None:
                        last_version = match_version.group(1).split(".")[-1]
                        last_version_path = \
                            os.path.join(version_dirpath,
                                         match_version.group(1)+".####"+match_version.group(2)).replace("\\","/")
                        break
                if last_version is not None:
                    break
            if last_version is None: continue
            # Store the retrieved data
            self.__read_nodes_list_for_update.append(
                (match.group(2), match.group(3),last_version,last_version_path, read_node))
        # Sort the data to have the out of date nodes at first and then alphabetically
        self.__read_nodes_list_for_update = sorted(self.__read_nodes_list_for_update, reverse=True,
                                                   key=lambda x: (x[1] == x[2], x[0]))

    def __scan_layers(self):
        """
        Scan the layers with the current unpack mode
        :return:
        """
        if self.__selected_unpack_mode is not None:
            self.__selected_unpack_mode.scan_layers(self.__shot_path)

    def __reinit_auto_comp(self):
        """
        Reinit the unpack mode to eventually start a new autocomp
        :return:
        """
        self.__retrieve_unpack_modes(_UNPACK_MODES_DIR)
        self.__retrieve_unpack_mode_prefs()
        self.__retrieve_default_unpack_mode()
        self.__scan_layers()

    def __shuffle_layer(self):
        """
        Shuffle a specific layer with the current mode
        :return:
        """
        AutoCompFactory.shuffle_layer(
            self.__selected_unpack_mode.get_config_path(), self.__shot_path, self.__selected_layers)

    def __unpack(self):
        """
        Run the autocomp, store the mode in the preferences and refresh the ui
        :return:
        """
        self.__prefs["unpack_mode"] = self.__selected_unpack_mode.get_name()
        self.__selected_unpack_mode.unpack(self.__shot_path)
        self.__reinit_auto_comp()
        self.__refresh_read_nodes_to_update()

    def __update_read(self):
        """
        Update selected read nodes in the Update Reads Table to the last version of their layer
        :return:
        """
        for read_node,new_path in self.__selected_read_nodes_for_update_data:
            if new_path is not None:
                read_node.knob("file").setValue(new_path)
        self.__refresh_read_nodes_to_update()

    def __shuffle_channel(self):
        """
        Shuffle selected channels of the selected read node
        :return:
        """
        AutoCompFactory.shuffle_channel_mode(self.__selected_read_node, self.__selected_channels)
