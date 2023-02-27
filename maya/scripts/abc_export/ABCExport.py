import os
from functools import partial

import sys
import json

from pymel.core import *
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from shiboken2 import wrapInstance

try:
    from utils import *
    from Prefs import *
except:
    pass

import maya.OpenMaya as OpenMaya

from ABCExportAsset import *

# ######################################################################################################################

_FILE_NAME_PREFS = "abc_export"


# ######################################################################################################################

main_window = omui.MQtUtil.mainWindow()
class ABCExport(QDialog):

    # Get the directory parent of the scene
    @staticmethod
    def __get_dir_name():
        scene_name = sceneName()
        if len(scene_name) > 0:
            dirname = os.path.dirname(os.path.dirname(scene_name))
        else:
            dirname = None
        return dirname

    # Test if a folder is an abc folder and if it exists
    @staticmethod
    def __is_abc_folder(folder):
        return re.match(r".*/abc(?:/|\\)?$", folder) and os.path.exists(folder)

    @staticmethod
    def get_database(database_path):
        assets = {}
        list_assets = [asset for asset in os.listdir(database_path) if
                       os.path.isfile(os.path.join(database_path, asset))]
        for asset in list_assets:
            filepath = os.path.join(database_path, asset)
            with open(filepath) as json_file:
                asset_data = json.load(json_file)
            asset_name, file_extension = os.path.splitext(asset)
            assets[asset_name] = asset_data
        return assets

    def __init__(self, prnt=wrapInstance(int(main_window), QWidget) if main_window is not None else None):
        super(ABCExport, self).__init__(prnt)

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__start_frame = int(playbackOptions(min=True, query=True))
        self.__end_frame = int(playbackOptions(max=True, query=True))
        self.__folder_path = ""
        found = self.__retrieve_database_dir()
        if not found:
            return
        self.__abcs = []
        self.__selected_abcs = []
        self.__retrieve_abcs()

        # UI attributes
        self.__ui_width = 400
        self.__ui_height = 400
        self.__ui_min_width = 350
        self.__ui_min_height = 250
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("ABC Export")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()

    # Don't show the window if the database hasn't been found
    def show(self) -> None:
        if self.__database_path is not None:
            super(ABCExport, self).show()

    # Retrieve the database folder
    def __retrieve_database_dir(self):
        self.__database_path = None
        database_path = os.getenv("CURRENT_PROJECT_DIR")
        # If database not found close the window
        if database_path is None:
            self.__stop_and_display_error()
            return False
        else:
            database_path += "/assets/_database"
            if not os.path.exists(database_path):
                self.__stop_and_display_error()
                return False
        self.__database_path = database_path
        return True

    # Delete the window and show an error message
    def __stop_and_display_error(self):
        self.deleteLater()
        msg = QMessageBox()
        msg.setWindowTitle("Error Database not found")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Database not found")
        msg.setInformativeText("Asset Database has not been found. You should use an Illogic Maya Launcher")
        msg.exec_()

    # Save preferences
    def __save_prefs(self):
        size = self.size()
        self.__prefs["window_size"] = {"width": size.width(), "height": size.height()}
        pos = self.pos()
        self.__prefs["window_pos"] = {"x": pos.x(), "y": pos.y()}

    # Retrieve preferences
    def __retrieve_prefs(self):
        if "window_size" in self.__prefs:
            size = self.__prefs["window_size"]
            self.__ui_width = size["width"]
            self.__ui_height = size["height"]

        if "window_pos" in self.__prefs:
            pos = self.__prefs["window_pos"]
            self.__ui_pos = QPoint(pos["x"], pos["y"])

    # Remove callbacks
    def hideEvent(self, arg__1: QCloseEvent) -> None:
        self.__save_prefs()

    # Create the ui
    def __create_ui(self):
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        browse_icon_path = os.path.dirname(__file__) + "/assets/browse.png"

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(8, 12, 8, 12)
        main_lyt.setSpacing(5)
        self.setLayout(main_lyt)

        # Folder selection layout
        folder_lyt = QHBoxLayout()
        main_lyt.addLayout(folder_lyt)
        self.__ui_folder_path = QLineEdit(self.__folder_path)
        self.__ui_folder_path.setFixedHeight(27)
        self.__ui_folder_path.textChanged.connect(self.__on_folder_changed)
        folder_lyt.addWidget(self.__ui_folder_path)
        browse_btn = QPushButton()
        browse_btn.setIconSize(QtCore.QSize(18, 18))
        browse_btn.setFixedSize(QtCore.QSize(24, 24))
        browse_btn.setIcon(QIcon(QPixmap(browse_icon_path)))
        browse_btn.clicked.connect(partial(self.__browse_folder))
        folder_lyt.addWidget(browse_btn)

        # Asset Table
        self.__ui_abcs_table = QTableWidget(0, 2)
        self.__ui_abcs_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__ui_abcs_table.verticalHeader().hide()
        self.__ui_abcs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_abcs_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_abcs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_abcs_table.itemSelectionChanged.connect(self.__on_abcs_selection_changed)
        main_lyt.addWidget(self.__ui_abcs_table)

        # Frame Start End layout
        frame_lyt = QHBoxLayout()
        main_lyt.addLayout(frame_lyt)
        label_start_end = QLabel("Start/end frame")
        frame_lyt.addWidget(label_start_end)
        self.__ui_start_frame = QLineEdit(str(self.__start_frame))
        self.__ui_start_frame.setValidator(QRegExpValidator(QRegExp(r"[0-9]*")))
        self.__ui_start_frame.textChanged.connect(self.__on_start_frame_changed)
        self.__ui_start_frame.editingFinished.connect(self.__on_start_frame_edited)
        frame_lyt.addWidget(self.__ui_start_frame)
        self.__ui_end_frame = QLineEdit(str(self.__end_frame))
        self.__ui_end_frame.setValidator(QRegExpValidator(QRegExp(r"[0-9]*")))
        self.__ui_end_frame.textChanged.connect(self.__on_end_frame_changed)
        self.__ui_end_frame.editingFinished.connect(self.__on_end_frame_edited)
        frame_lyt.addWidget(self.__ui_end_frame)

        # Submit Export button
        self.__export_btn = QPushButton("Export selection")
        self.__export_btn.clicked.connect(self.__export_selected_abcs)
        main_lyt.addWidget(self.__export_btn)

    # Refresh the ui according to the model attribute
    def __refresh_ui(self):
        self.__refresh_btn()
        self.__refresh_abcs_table()

    # Refresh the submit button
    def __refresh_btn(self):
        nb_abcs_selected = len(self.__selected_abcs)
        enabled = True
        tooltip = ""
        if nb_abcs_selected == 0:
            enabled = False
            tooltip = "Select atleast one abc to export"
        elif not self.__is_abc_folder(self.__folder_path):
            enabled = False
            tooltip = "The export folder must be named \"abc\""
        self.__export_btn.setEnabled(enabled)
        self.__export_btn.setToolTip(tooltip)

    # Refresh the asset table
    def __refresh_abcs_table(self):
        selected_abcs = self.__selected_abcs

        # If the folder is valid we display the "Next version" column
        abc_folder_valid = self.__is_abc_folder(self.__folder_path)
        if abc_folder_valid:
            col_count = 2
            head_labels = ["Asset", "Next version"]
        else:
            col_count = 1
            head_labels = ["Asset"]
        self.__ui_abcs_table.setColumnCount(col_count)
        self.__ui_abcs_table.setHorizontalHeaderLabels(head_labels)
        self.__ui_abcs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        if abc_folder_valid:
            self.__ui_abcs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.__ui_abcs_table.setRowCount(0)
        row_index = 0
        selected_rows = []
        for abc in self.__abcs:
            self.__ui_abcs_table.insertRow(row_index)
            if abc in selected_abcs:
                selected_rows.append(row_index)

            # Name asset
            asset_name_item = QTableWidgetItem(abc.get_name_with_num())
            asset_name_item.setData(Qt.UserRole, abc)
            self.__ui_abcs_table.setItem(row_index, 0, asset_name_item)

            # If the folder is valid we display the "Next version" item
            if abc_folder_valid:
                next_version_item = QTableWidgetItem(
                    str(ABCExportAsset.next_version(os.path.join(self.__folder_path, abc.get_name_with_num()))).zfill(
                        4))
                next_version_item.setTextAlignment(Qt.AlignCenter)
                self.__ui_abcs_table.setItem(row_index, 1, next_version_item)

            row_index += 1

        # Select the previous selected rows
        self.__ui_abcs_table.setSelectionMode(QAbstractItemView.MultiSelection)
        for row_index in selected_rows:
            self.__ui_abcs_table.selectRow(row_index)
        self.__ui_abcs_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

    # Browse a new abc folder
    def __browse_folder(self):
        dirname = ABCExport.__get_dir_name()
        folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select ABC Directory", dirname)
        if re.match(r".*/abc(?:/|\\)?$", folder_path) and folder_path != self.__folder_path:
            self.__ui_folder_path.setText(folder_path)

    # Retrieve the folder path on folder linedit change
    def __on_folder_changed(self):
        self.__folder_path = self.__ui_folder_path.text()
        self.__refresh_ui()

    # Retrieve the start frame value on edit and change end frame
    # if it is lower than the start frame
    def __on_start_frame_changed(self):
        start_frame = self.__ui_start_frame.text()
        self.__start_frame = 1 if len(start_frame) == 0 or int(start_frame) <= 0 else int(start_frame)
        if self.__start_frame >= self.__end_frame:
            self.__ui_end_frame.setText(str(self.__start_frame + 1))

    # Change the end frame
    def __on_end_frame_changed(self):
        end_frame = self.__ui_end_frame.text()
        self.__end_frame = self.__start_frame + 1 if len(end_frame) == 0 or int(
            end_frame) <= self.__start_frame else int(end_frame)

    # On start frame loose focus refresh the display
    def __on_start_frame_edited(self):
        self.__ui_start_frame.setText(str(self.__start_frame))

    # On end frame loose focus refresh the display
    def __on_end_frame_edited(self):
        self.__ui_end_frame.setText(str(self.__end_frame))

    # Retrieve the abcs selected on rows selected in the asset table
    def __on_abcs_selection_changed(self):
        self.__selected_abcs.clear()
        for selected_row in self.__ui_abcs_table.selectionModel().selectedRows():
            self.__selected_abcs.append(self.__ui_abcs_table.item(selected_row.row(), 0).data(Qt.UserRole))
        self.__refresh_btn()

    # Retrieve all the asset datas in the database of the current project
    def __get_database(self):
        return ABCExport.get_database(self.__database_path)

    # Retrieve all the geos of an asset in the scene
    @staticmethod
    def list_existing_geos(database, name, namespace_found):
        geos = database[name]["geo"]
        new_geos = []
        for g in geos:
            geo_ns_replaced = g.replace(g.split(":")[0], namespace_found)
            if objExists(geo_ns_replaced):
                new_geos.append(geo_ns_replaced)
        return new_geos

        # Retrieve all the abcs existing in the scene and build the list of abc

    @staticmethod
    def retrieve_abcs(database_path):
        abcs = []
        abcs_by_name = {}
        existing_assets = ABCExport.get_database(database_path)
        references = listReferences()
        namespaces = namespaceInfo(listOnlyNamespaces=True, recurse=True)
        assets_found = {}
        # Retrieve all the rigging in references
        for ref in references:
            match = re.match(r".*\/(.+)_rigging[a-zA-Z_\.]*[0-9]{3,4}\.m[ab]", ref.unresolvedPath())
            if match:
                assets_found[ref.fullNamespace] = match.groups()[0]
        # Retrieve all the rigging in namespaces
        for ns in namespaces:
            match = re.match(r"(.+)_rigging[a-zA-Z_\.]*[0-9]{3,4}$", ns)
            if match:
                assets_found[ns] = match.groups()[0]

        for namespace, name in assets_found.items():
            name_found = None
            namespace_found = None
            # Retrieve all the rigging found in database
            for name_existing in existing_assets.keys():
                if name_existing == name:
                    name_found = name
                    namespace_found = namespace
                    break

            # Create all the ABCs if they have geos
            if name_found is not None:
                geos = ABCExport.list_existing_geos(existing_assets, name_found, namespace_found)
                valid = True
                if not geos:
                    valid = False
                else:
                    for geo in geos:
                        if len(ls(geo)) > 1:
                            valid = False
                            break
                if valid:
                    if name_found not in abcs_by_name:
                        abcs_by_name[name_found] = []
                    abcs_by_name[name_found].append(ABCExportAsset(name_found, namespace_found, geos))

        # If many abcs with the same name, we change their num to defferenciate them
        for name_existing, abcs_existing in abcs_by_name.items():
            if len(abcs_existing) > 1:
                i = 0
                for abc in abcs_existing:
                    abc.set_num(i)
                    i += 1
            abcs.extend(abcs_existing)
        return abcs

    # Retrieve all the abcs existing in the scene and build the list of abc
    def __retrieve_abcs(self):
        self.__abcs = ABCExport.retrieve_abcs(self.__database_path)

    # Export all the selected abcs
    def __export_selected_abcs(self):
        self.__export_btn.setEnabled(False)
        for abc in self.__selected_abcs:
            abc.export(self.__folder_path, self.__start_frame, self.__end_frame)
        self.__selected_abcs.clear()
        self.__refresh_ui()