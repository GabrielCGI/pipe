import os
import re
import glob
import sys
import time
from pathlib import Path

try:
    from PySide2 import QtCore as Qtc#type: ignore
    from PySide2 import QtGui as Qtg #type: ignore
    from PySide2 import QtWidgets as Qt #type: ignore
except:
    try:
        from PySide6 import QtCore as Qtc
        from PySide6 import QtGui as Qtg
        from PySide6 import QtWidgets as Qt
    except:
        sys.exit(1)

from functools import partial
from enum import Enum

from common.utils import *
from common.Prefs import *
import nuke
from .AutoCompFactory import AutoCompFactory
from .ShuffleMode import ShuffleMode

from .performance_profiler import profile_function

# ######################################################################################################################
_DEBOUNCE_DELAY = 0.05
_LAST_CALL = 0

_RENDER_FOLDER = os.path.join("Renders", "3dRender")

_COLOR_GREY_DISABLE = 105,105,105
# ######################################################################################################################

class AutoComp(Qt.QWidget):
    
    class ReadStates(Enum):
        COMPLETE = os.path.dirname(__file__) + "/assets/green_dot.svg"
        IMCOMPLETE = os.path.dirname(__file__) + "/assets/orange_dot.svg"
        EMPTY = os.path.dirname(__file__) + "/assets/red_dot.svg"
    
    def __init__(self, prt=None):
        super(AutoComp, self).__init__(prt)
        from . import pcore

        self.pcore = pcore
        self.__selected_channels = []
        self.__selected_read_node = None
        self.__read_nodes_list_for_update = []
        self.__selected_read_nodes_for_update_data = []
        self.__read_node_versions = {}
        self.complete_mode = True

        # UI attributes
        self.__ui_width = 400
        self.__ui_height = 150
        self.__ui_min_width = 250
        self.__ui_min_height = 150
        
        if Qtc.qVersion() >= "5.14.0":
            self.__ui_pos = Qtg.QGuiApplication.primaryScreen().availableGeometry().center() - Qtc.QPoint(self.__ui_width, self.__ui_height) / 2
        else:
            self.__ui_pos = Qt.QDesktopWidget().availableGeometry().center() - Qtc.QPoint(self.__ui_width, self.__ui_height) / 2 # type: ignore


        # name the window
        self.setWindowTitle("AutoComp")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(Qtc.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(Qtc.Qt.WA_DeleteOnClose)

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
        nuke.addOnScriptSave(self.__refresh_read_nodes_to_update)
        self.__on_read_node_selected()

    def remove_callbacks(self):
        """
        Remove callbacks
        :return:
        """
        try:
            reads_cbs = nuke.knobChangeds["Read"]
            for callback in reads_cbs:
                cb_function = callback[0]
                if cb_function.__name__ == "__on_read_node_selected":
                    nuke.removeKnobChanged(cb_function, nodeClass="Read")
        except:
            return
        try:
            on_script_saved_cbs = nuke.callbacks.onScriptSaves['Root']
            for i in range(len(on_script_saved_cbs)-1, -1, -1):
                cb_function = on_script_saved_cbs[i][0]
                if cb_function.__name__ == "__refresh_read_nodes_to_update":
                    nuke.removeOnScriptSave(cb_function)
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
        header = Qt.QHBoxLayout()
        line = Qt.QFrame()
        line.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Minimum)
        line.setFrameShape(Qt.QFrame.HLine)
        line.setFrameShadow(Qt.QFrame.Raised)
        header.addWidget(line)
        lbl_shot_to_autocomp = Qt.QLabel(title)
        header.addWidget(lbl_shot_to_autocomp)
        if button is not None:
            lbl_shot_to_autocomp.setContentsMargins(15, 0, 0, 0)
            button.setContentsMargins(0,0,15,0)
            header.addWidget(button)
        else:
            lbl_shot_to_autocomp.setContentsMargins(15, 0, 15, 0)
        line = Qt.QFrame()
        line.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Minimum)
        line.setFrameShape(Qt.QFrame.HLine)
        line.setFrameShadow(Qt.QFrame.Raised)
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
        
        reload_icon_path = os.path.dirname(__file__) + "/assets/reload.png"
        
        # Main Layout
        main_lyt = Qt.QVBoxLayout()
        main_lyt.setSpacing(10)
        main_lyt.setAlignment(Qtc.Qt.AlignTop)
        self.setLayout(main_lyt)

        # SHUFFLE READ CHANNEL PART

        shuffle_read_channel_lyt = Qt.QVBoxLayout()
        shuffle_read_channel_lyt.setSpacing(8)
        shuffle_read_channel_lyt.setContentsMargins(0, 0, 0, 15)
        main_lyt.addLayout(shuffle_read_channel_lyt)

        shuffle_read_channel_lyt.addLayout(AutoComp.__get_header_ui("Shuffle Read Channel"))

        self.__ui_lbl_selected_read_node = Qt.QLineEdit()
        self.__ui_lbl_selected_read_node.setPlaceholderText("Read node selected name")
        self.__ui_lbl_selected_read_node.setReadOnly(True)
        self.__ui_lbl_selected_read_node.setAlignment(Qtc.Qt.AlignCenter)
        self.__ui_lbl_selected_read_node.setStyleSheet("font-weight:bold")
        shuffle_read_channel_lyt.addWidget(self.__ui_lbl_selected_read_node)

        self.__ui_channel_list = Qt.QListWidget()
        self.__ui_channel_list.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)
        self.__ui_channel_list.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Minimum)
        self.__ui_channel_list.itemSelectionChanged.connect(self.__on_channel_selected)
        shuffle_read_channel_lyt.addWidget(self.__ui_channel_list)

        self.__ui_shuffle_channel_btn = Qt.QPushButton("Shuffle selected channels")
        self.__ui_shuffle_channel_btn.setFixedHeight(30)
        self.__ui_shuffle_channel_btn.clicked.connect(self.__shuffle_channel)
        shuffle_read_channel_lyt.addWidget(self.__ui_shuffle_channel_btn)
        
        shuffle_advanced_setting_lyt = Qt.QHBoxLayout()
        
        self.horizontal_padding_spb = Qt.QDoubleSpinBox()
        self.horizontal_padding_spb.setPrefix("Horizontal padding : ")
        self.horizontal_padding_spb.setValue(1.0)
        self.horizontal_padding_spb.setSingleStep(0.2)
        shuffle_advanced_setting_lyt.addWidget(self.horizontal_padding_spb)
        
        self.vertical_padding_spb = Qt.QDoubleSpinBox()
        self.vertical_padding_spb.setPrefix("Vertical padding : ")
        self.vertical_padding_spb.setValue(1.0)
        self.vertical_padding_spb.setSingleStep(0.2)
        shuffle_advanced_setting_lyt.addWidget(self.vertical_padding_spb)
        
        shuffle_read_channel_lyt.addLayout(shuffle_advanced_setting_lyt)
        
        # UPDATE READS PART

        update_reads_lyt = Qt.QVBoxLayout()
        update_reads_lyt.setSpacing(8)
        update_reads_lyt.setContentsMargins(0, 0, 0, 15)
        main_lyt.addLayout(update_reads_lyt)

        refresh_reads_to_update_btn = Qt.QPushButton()
        refresh_reads_to_update_btn.setIconSize(Qtc.QSize(16, 16))
        refresh_reads_to_update_btn.setFixedSize(Qtc.QSize(24, 24))
        refresh_reads_to_update_btn.setIcon(Qtg.QIcon(Qtg.QPixmap(reload_icon_path)))
        refresh_reads_to_update_btn.clicked.connect(partial(self.__refresh_read_nodes_to_update))

        update_reads_lyt.addLayout(AutoComp.__get_header_ui("Get Reads versions", button = refresh_reads_to_update_btn))

        self.__ui_read_nodes_table = Qt.QTableWidget(0, 5)
        self.__ui_read_nodes_table.setHorizontalHeaderLabels(["Name", "Layer", "Actual", "Last", "Selected"])
        self.__ui_read_nodes_table.setSizePolicy(Qt.QSizePolicy.Minimum, Qt.QSizePolicy.MinimumExpanding)
        self.__ui_read_nodes_table.horizontalHeader().setSectionResizeMode(4, Qt.QHeaderView.Stretch)
        self.__ui_read_nodes_table.setSelectionBehavior(Qt.QAbstractItemView.SelectRows)
        self.__ui_read_nodes_table.verticalHeader().hide()
        self.__ui_read_nodes_table.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)
        self.__ui_read_nodes_table.setEditTriggers(Qt.QTableWidget.NoEditTriggers)
        self.__ui_read_nodes_table.itemSelectionChanged.connect(self.__on_read_node_list_item_selected)
        update_reads_lyt.addWidget(self.__ui_read_nodes_table)

        self.ui_update_mode_complete_rbtn = Qt.QRadioButton("Complete only")
        self.ui_update_mode_complete_rbtn.setChecked(True)
        self.ui_update_mode_complete_rbtn.toggled.connect(self.__on_update_mode_changed)
        update_reads_lyt.addWidget(self.ui_update_mode_complete_rbtn)
        
        ui_update_mode_incomplete_rbtn = Qt.QRadioButton("Complete and Incomplete")
        ui_update_mode_incomplete_rbtn.toggled.connect(self.__on_update_mode_changed)
        update_reads_lyt.addWidget(ui_update_mode_incomplete_rbtn)

        self.__ui_update_reads_btn = Qt.QPushButton("Update selected read nodes")
        self.__ui_update_reads_btn.setFixedHeight(30)
        self.__ui_update_reads_btn.clicked.connect(self.__update_selected_reads)
        update_reads_lyt.addWidget(self.__ui_update_reads_btn)
        
        self.__ui_update_all_reads_btn = Qt.QPushButton("Update all read nodes")
        self.__ui_update_all_reads_btn.setFixedHeight(30)
        self.__ui_update_all_reads_btn.clicked.connect(self.__update_all_reads)
        update_reads_lyt.addWidget(self.__ui_update_all_reads_btn)
        
    def __on_update_mode_changed(self):
        self.complete_mode = self.ui_update_mode_complete_rbtn.isChecked()

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__refresh_shuffle_channel_btn()
        self.__refresh_read_nodes_to_update()

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
            self.__ui_channel_list.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)
            for channel in lg_channels:
                item = Qt.QListWidgetItem(channel)
                item.setData(Qtc.Qt.UserRole, channel)
                if channel in present_channels:
                    item.setForeground(Qtg.QColor(*_COLOR_GREY_DISABLE))
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
            self.__selected_channels.append(item.data(Qtc.Qt.UserRole))
        self.__refresh_shuffle_channel_btn()

    def __on_read_node_selected(self):
        """
        On Read Node selected in the Graph change the selected read node and refresh the ui
        :return:
        """
        global _LAST_CALL
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
        # prevent too many refresh in a short amount of time with a delay
        now = time.time()
        if now - _LAST_CALL < _DEBOUNCE_DELAY:
            return
        _LAST_CALL = now
        self.__refresh_read_node_ui()

    def __shuffle_channel(self):
        """
        Shuffle selected channels of the selected read node
        :return:
        """
        undo = nuke.Undo()
        undo.begin()
        try:
            AutoCompFactory.shuffle_channel_mode(
                self.__selected_read_node,
                self.__selected_channels,
                self.horizontal_padding_spb.value(),
                self.vertical_padding_spb.value()
            )
            undo.end()
        except:
            undo.end()
    
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
        camera_nodes = nuke.allNodes("Camera3")

        if not read_nodes:
            return  # Exit if no read nodes are found

        # Updated pattern to include frame sequence capture
        read_pattern = re.compile(
            r"(.*"
            + (_RENDER_FOLDER).replace("\\", "/")
            + r"/[^/]+)"                       # First group -> Full path + "Renders/3drender" + LAYER
            + r"/(v\d{3,9})"                   # Second group -> Version folder (v followed by n digits)
            + r"/([^\/]*)"                     # Third group -> "beauty"
            + r"/([^\.]+)"                     # Fourth group -> Shot_name
            + r"(\.(\d{3,9})|\.%04d)\.exr"     # Fifth frame -> Sequence
        )
        camera_pattern = re.compile(
            r"(.*"
            + r"Export"
            + r"/[^/]+)"                       # First group -> Full path + "Export" + _sublayer_
            + r"/(v\d{3,9})"                   # Second group -> Version folder (v followed by n digits)
        )

        for read_node in read_nodes:
            path = read_node.knob("file").value().replace("\\", "/")
            match = read_pattern.search(path)

            # continue
            if not match:
                continue  # Skip the iteration if the pattern doesn't match

            # Fetch base directory, version directory, "beauty", shot name and frame sequence
            base_directory, version_number, parent_directory, shot_name, frame_sequence, _ = match.groups()
            base_var = base_directory.split('/')[-1]
            
            # Normalize the frame sequence
            frame_sequence = "####"  # Default frame sequence

            # List every version directory and take the highest version
            entries = os.listdir(base_directory)
            directories = [entry for entry in entries if os.path.isdir(os.path.join(base_directory, entry)) and not entry.endswith(")")]
            if not directories:
                continue  # Skip if no directories found
            directories.sort()
            
            base_directory_path = Path(base_directory)
            sequence = base_directory_path.parts[4]
            shot = base_directory_path.parts[5]
            frame_range = self.pcore.entities.getShotRange(
                {"type": "shot", "sequence": sequence, "shot": shot}
            )
            
            current_state, _, _ = self.__get_state_from_version(os.path.join(base_directory, version_number), frame_range)
            if current_state == self.ReadStates.COMPLETE:
                read_node.knob("label").setText("")
            last_directory = directories[-1]
            last_version = last_directory.split('.')[-1]
            # Replace the version number this the string if there is a new one
            shot_name = re.sub(r"v\d{3,9}", last_version, shot_name)
            
            # Build the shot file name
            map_name = shot_name + "." + frame_sequence + ".exr"

            # Build the path to the last version
            last_version_path = os.path.join(base_directory, last_directory, parent_directory, map_name).replace("\\", "/")

            self.__read_nodes_list_for_update.append((base_var, version_number, last_version, last_version_path, read_node))

            self.__read_node_versions[read_node.name()] = {}
            for version in directories:
                version_directory = os.path.join(base_directory, version)
                state, rendered_frames, shots_frames = self.__get_state_from_version(version_directory, frame_range)
                
                shot_name = re.sub(r"v\d{3,9}", version, shot_name)
                map_name = shot_name + "." + frame_sequence + ".exr"
                version_path = os.path.join(base_directory, version, parent_directory, map_name).replace("\\", "/")
                
                self.__read_node_versions[read_node.name()][version] = {
                    "filepath": version_path,
                    "state": state,
                    "rendered_frames": rendered_frames,
                    "total_frames": shots_frames
                }

        for camera_node in camera_nodes:
            path = camera_node.knob("file").value().replace("\\", "/")
            match = camera_pattern.search(path)

            # continue
            if not match:
                continue  # Skip the iteration if the pattern doesn't match

            # Fetch base directory, version directory, "beauty", shot name and frame sequence
            base_directory, version_number = match.groups()

            # List every version directory and take the highest version
            entries = os.listdir(base_directory)
            directories = [entry for entry in entries if os.path.isdir(os.path.join(base_directory, entry)) and not entry.endswith(")")]
            if not directories:
                continue  # Skip if no directories found
            directories.sort()
            
            last_directory = directories[-1]
            last_version = last_directory.split('.')[-1]
            
            last_version_path = re.sub(r"v\d{3,9}", last_version, path)
            self.__read_nodes_list_for_update.append(("CAMERA", version_number, last_version, last_version_path, camera_node))
            
            self.__read_node_versions[camera_node.name()] = {}
            for version in directories:
                version_path = re.sub(r"v\d{3,9}", version, path)
                self.__read_node_versions[camera_node.name()][version] = {
                    "filepath": version_path,
                }
                
        self.__read_nodes_list_for_update = sorted(self.__read_nodes_list_for_update, reverse=True, key=lambda x: x[-1].name())


    def __get_state_from_version(self, version_directory, frame_range, threshold=0.15):
        if frame_range is None:
            return (self.ReadStates.EMPTY, 0, 0)
        pattern = os.path.join(version_directory, "*", "*.exr")
        all_frames = glob.glob(pattern)
        nb_shot_frames = frame_range[1] - frame_range[0] + 1
        if len(all_frames) == nb_shot_frames:
            return (self.ReadStates.COMPLETE, len(all_frames), nb_shot_frames)
        frame_progression = len(all_frames) / nb_shot_frames
        if frame_progression > threshold:
            return (self.ReadStates.IMCOMPLETE, len(all_frames), nb_shot_frames)
        else:
            return (self.ReadStates.EMPTY, len(all_frames), nb_shot_frames)

    def __refresh_update_reads_table(self):
        """
        Refresh the Update Reads Table
        :return:
        """
        self.__ui_read_nodes_table.setRowCount(0)
        row_index = 0
        
        for layer, current_version, last_version, last_version_path, read_node in self.__read_nodes_list_for_update:
            self.__ui_read_nodes_table.insertRow(row_index)

            name_item = Qt.QTableWidgetItem(read_node.name())
            if current_version == last_version:
                name_item.setData(Qtc.Qt.UserRole, (read_node, None))
            else:
                name_item.setData(Qtc.Qt.UserRole, (read_node, last_version_path))
            name_item.setTextAlignment(Qtc.Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 0, name_item)

            layer_item = Qt.QTableWidgetItem(layer)
            layer_item.setTextAlignment(Qtc.Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 1, layer_item)

            current_version_item = Qt.QTableWidgetItem(current_version)
            current_version_item.setTextAlignment(Qtc.Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 2, current_version_item)

            last_version_item = Qt.QTableWidgetItem(last_version)
            last_version_item.setTextAlignment(Qtc.Qt.AlignCenter)
            self.__ui_read_nodes_table.setItem(row_index, 3, last_version_item)
            
            version_widget = Qt.QWidget()
            version_lyt = Qt.QHBoxLayout()
            version_lyt.setContentsMargins(0, 0, 0, 0)
            version_widget.setLayout(version_lyt)
            version_selection_cbb = Qt.QComboBox()
            last_version_full = 0
            read_datas = self.__read_node_versions[read_node.name()]
            for item_index, version in enumerate(read_datas.keys()):
                if read_node.Class() == "Read":
                    color_icon = self.__get_color_from_read_version(read_node, version)
                    rendered_frames = read_datas[version]["rendered_frames"]
                    shots_frames = read_datas[version]["total_frames"]
                    state = read_datas[version]["state"]
                    if self.complete_mode:
                        if state == self.ReadStates.COMPLETE:
                            last_version_full = item_index
                    else:
                        if (state == self.ReadStates.COMPLETE
                            or state == self.ReadStates.IMCOMPLETE):
                            last_version_full = item_index    
                    version_selection_cbb.addItem(color_icon, f"{version} - {rendered_frames}/{shots_frames}")
                else:
                    version_selection_cbb.addItem(version)
                    last_version_full = item_index
            
            version_selection_cbb.setCurrentIndex(last_version_full)
            version_lyt.addWidget(version_selection_cbb)
                
            self.__ui_read_nodes_table.setCellWidget(row_index, 4, version_widget)

            if current_version == last_version:
                name_item.setForeground(Qtg.QColor(*_COLOR_GREY_DISABLE))
                layer_item.setForeground(Qtg.QColor(*_COLOR_GREY_DISABLE))
                current_version_item.setForeground(Qtg.QColor(*_COLOR_GREY_DISABLE))
                last_version_item.setForeground(Qtg.QColor(*_COLOR_GREY_DISABLE))

    def __get_color_from_read_version(self, read_node, version):
        try:
            state = self.__read_node_versions[read_node.name()][version]['state']
        except Exception as e:
            state = self.ReadStates.EMPTY
        return Qtg.QIcon(state.value)

    def __on_read_node_list_item_selected(self):
        """
        On Read Node selected in Update Reads Table Retrieve selected and refresh the update button
        :return:
        """
        rows_selected = self.__ui_read_nodes_table.selectionModel().selectedRows()
        del self.__selected_read_nodes_for_update_data[:]
        for row_selected in rows_selected:
            self.__selected_read_nodes_for_update_data.append(
                self.__ui_read_nodes_table.item(row_selected.row(), 0).data(Qtc.Qt.UserRole)
            )
        for node in nuke.allNodes():
            node.setSelected(False)
        unknown_node_found = False
        for node, _ in self.__selected_read_nodes_for_update_data:
            try:
                node.setSelected(True)
            except:
                unknown_node_found = True
                break
        if unknown_node_found:
            self.__retrieve_read_nodes_to_update()
            self.__refresh_update_reads_table()
        self.__on_read_node_selected()
        self.__refresh_update_read_node_btn()
        
    def __refresh_update_read_node_btn(self):
        """
        Refresh the Update Reads Node button
        :return:
        """
        self.__ui_update_reads_btn.setEnabled(len(self.__selected_read_nodes_for_update_data) > 0)

    def __update_read(self, read_node: nuke.Node, version):
        version_datas = self.__read_node_versions[read_node.name()][version]
        version_path = version_datas["filepath"]
        read_node.knob("file").setValue(version_path)
        if read_node.Class() == "Read":
            version_state = version_datas["state"]
            read_node.knob("on_error").setValue("black")
            if not version_state == self.ReadStates.COMPLETE:
                rendered_frames = version_datas["rendered_frames"]
                shots_frames = version_datas["total_frames"]
                read_node.knob("label").setText(
                    f"Incomplete: Missing {shots_frames - rendered_frames}"
                    f" frames out of {shots_frames}"
                )

    def __update_selected_reads(self):
        """
        Update selected read nodes in the Update Reads Table to the last version of their layer
        :return:
        """
        rows_selected = self.__ui_read_nodes_table.selectionModel().selectedRows()
        for row_selected in rows_selected:
            cbb_parent = self.__ui_read_nodes_table.cellWidget(row_selected.row(), 4)
            cbb = cbb_parent.findChild(Qt.QComboBox)
            version_selected = cbb.currentText()
            version_selected = version_selected.split(" ")[0]
            read_datas = self.__ui_read_nodes_table.item(row_selected.row(), 0).data(Qtc.Qt.UserRole)
            read_node, _ = read_datas
            self.__update_read(read_node, version_selected)
        self.__refresh_read_nodes_to_update()   
        
    def __update_all_reads(self):
        """
        Update selected read nodes in the Update Reads Table to the last version of their layer
        :return:
        """
        for row in range(self.__ui_read_nodes_table.rowCount()):
            cbb_parent = self.__ui_read_nodes_table.cellWidget(row, 4)
            cbb = cbb_parent.findChild(Qt.QComboBox)
            version_selected = cbb.currentText()
            version_selected = version_selected.split(" ")[0]
            read_datas = self.__ui_read_nodes_table.item(row, 0).data(Qtc.Qt.UserRole)
            read_node, _ = read_datas
            self.__update_read(read_node, version_selected)
        self.__refresh_read_nodes_to_update()