import os
import sys
import re

from functools import partial

import pymel.core as pm
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from shiboken2 import wrapInstance

from common.utils import *

from common.Prefs import *

import maya.OpenMaya as OpenMaya

from .LookStandin import LookAsset, LookPresentState
from .LookFactory import LookFactory

# ######################################################################################################################

_FILE_NAME_PREFS = "look_loader"


# ######################################################################################################################


class LookLoader(QDialog):

    def __init__(self, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(LookLoader, self).__init__(prnt)

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__standins = {}
        self.__refresh_selection = True
        self.__standin_obj_selected = None
        self.__file_looks_selected = []
        self.__selection_callback = None
        self.__replace_looks = False

        self.__retrieve_current_project_dir()
        self.__look_factory = LookFactory(self.__current_project_dir)

        # UI attributes
        self.__ui_width = 700
        self.__ui_height = 350
        self.__ui_min_width = 500
        self.__ui_min_height = 250
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("Look Loader")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # retrieve datas
        self.__retrieve_standins()

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()

    def __save_prefs(self):
        """
        Save preferences
        :return:
        """
        size = self.size()
        self.__prefs["window_size"] = {"width": size.width(), "height": size.height()}
        pos = self.pos()
        self.__prefs["window_pos"] = {"x": pos.x(), "y": pos.y()}
        self.__prefs["replace_looks"] = self.__replace_looks

    def __retrieve_prefs(self):
        """
        Retrieve preferences
        :return:
        """
        if "window_size" in self.__prefs:
            size = self.__prefs["window_size"]
            self.__ui_width = size["width"]
            self.__ui_height = size["height"]

        if "window_pos" in self.__prefs:
            pos = self.__prefs["window_pos"]
            self.__ui_pos = QPoint(pos["x"], pos["y"])

        if "replace_looks" in self.__prefs:
            self.__replace_looks = self.__prefs["replace_looks"]

    def showEvent(self, arg__1: QShowEvent) -> None:
        """
        Create callback
        :return:
        """
        self.__selection_callback = \
            OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.__on_scene_selection_changed)

    def hideEvent(self, arg__1: QCloseEvent) -> None:
        """
        Remove callback and save preferences
        :return:
        """
        OpenMaya.MMessage.removeCallback(self.__selection_callback)
        self.__save_prefs()

    def __retrieve_current_project_dir(self):
        """
        Retrieve the current project dir specified in the Illogic maya launcher
        :return:
        """
        self.__current_project_dir = os.getenv("CURRENT_PROJECT_DIR")
        if self.__current_project_dir is None:
            self.__error_current_project_dir()

    def __error_current_project_dir(self):
        """
        Delete the window and show an error message
        :return:
        """
        self.deleteLater()
        msg = QMessageBox()
        msg.setWindowTitle("Error current project directory not found")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Current project directory not found")
        msg.setInformativeText(
            "Current project directory has not been found. You should use an Illogic Maya Launcher")
        msg.exec_()

    def __create_ui(self):
        """
        Create the ui
        :return:
        """
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        # asset_path = os.path.dirname(__file__) + "/assets/asset.png"

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(10, 15, 10, 15)
        main_lyt.setSpacing(8)
        self.setLayout(main_lyt)

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(0,0,0,5)
        main_lyt.addLayout(grid_layout)
        grid_layout.setRowStretch(1, 1)
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.addWidget(QLabel("Standins"), 0, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(QLabel("Looks"), 0, 1, alignment=Qt.AlignCenter)

        # Standin Table
        self.__ui_standin_table = QTableWidget(0, 4)
        self.__ui_standin_table.setHorizontalHeaderLabels(["Name", "Standin Name", "Number looks", "UVs"])
        self.__ui_standin_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__ui_standin_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.__ui_standin_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_standin_table.verticalHeader().hide()
        self.__ui_standin_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__ui_standin_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_standin_table.itemSelectionChanged.connect(self.__on_standin_select_changed)
        grid_layout.addWidget(self.__ui_standin_table, 1, 0, 2,1)

        # List of Looks
        self.__ui_looks_list = QListWidget()
        self.__ui_looks_list.setSpacing(2)
        self.__ui_looks_list.setStyleSheet("font-size:14px")
        self.__ui_looks_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_looks_list.itemSelectionChanged.connect(self.__on_look_selected_changed)
        grid_layout.addWidget(self.__ui_looks_list, 1, 1)

        # Toggle replace
        self.__ui_toggle_replace_look_btn = QRadioButton("Replace looks")
        self.__ui_toggle_replace_look_btn.clicked.connect(self.__on_replace_looks_checked)
        grid_layout.addWidget(self.__ui_toggle_replace_look_btn, 2, 1, alignment=Qt.AlignCenter)

        # Button
        self.__ui_add_looks_to_standin_btn = QPushButton("Set Looks to the StandIn")
        self.__ui_add_looks_to_standin_btn.clicked.connect(self.__on_add_looks_to_standin)
        main_lyt.addWidget(self.__ui_add_looks_to_standin_btn)

    def __refresh_ui(self):
        """
        Refresh the ui according to the model attribute
        :return:
        """
        self.__refresh_standin_table()
        self.__refresh_btn()
        self.__ui_toggle_replace_look_btn.setChecked(self.__replace_looks)

    def __refresh_btn(self):
        """
        Refresh the buttons
        :return:
        """
        self.__ui_add_looks_to_standin_btn.setEnabled(self.__standin_obj_selected is not None and
                                                      len(self.__file_looks_selected) > 0)

    def __refresh_standin_table(self):
        """
        Refresh the standin table
        :return:
        """
        refresh_selection = self.__refresh_selection
        self.__refresh_selection = False
        self.__ui_standin_table.setRowCount(0)
        row_index = 0
        row_selected = None
        for standin_obj in self.__standins.values():
            self.__ui_standin_table.insertRow(row_index)

            if standin_obj is self.__standin_obj_selected:
                row_selected = row_index

            object_name = standin_obj.get_object_name()
            standin_name = standin_obj.get_standin_name()

            object_name_item = QTableWidgetItem(object_name)
            object_name_item.setData(Qt.UserRole, standin_obj)
            self.__ui_standin_table.setItem(row_index, 0, object_name_item)

            standin_name_item = QTableWidgetItem(standin_name)
            standin_name_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_standin_table.setItem(row_index, 1, standin_name_item)

            nb_looks = len(standin_obj.get_looks())
            nb_looks_item = QTableWidgetItem(str(nb_looks))
            nb_looks_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_standin_table.setItem(row_index, 2, nb_looks_item)

            if standin_obj.is_uv_up_to_date():
                up_to_date_lbl = QTableWidgetItem("Up to date")
                up_to_date_lbl.setTextAlignment(Qt.AlignCenter)
                self.__ui_standin_table.setItem(row_index, 3, up_to_date_lbl)
            else:
                update_uv_btn = QPushButton("Update")
                update_uv_btn.setStyleSheet("margin:3px")
                update_uv_btn.clicked.connect(standin_obj.update_uvs)
                update_uv_btn.clicked.connect(self.__refresh_standin_table)
                self.__ui_standin_table.setCellWidget(row_index, 3, update_uv_btn)

            row_index += 1
        if row_selected is not None:
            self.__ui_standin_table.selectRow(row_selected)
        self.__refresh_selection = refresh_selection

    def __refresh_looks_list(self):
        """
        Refresh the looks
        :return:
        """
        self.__ui_looks_list.clear()
        if self.__standin_obj_selected is not None:
            looks = self.__standin_obj_selected.get_looks()
            for look_name, look_data in looks.items():
                look_list_widget = QListWidgetItem(look_name)
                look_list_widget.setData(Qt.UserRole, look_data[0])
                self.__ui_looks_list.addItem(look_list_widget)
                if look_data[1] == LookPresentState.AlreadyPlugged:
                    look_list_widget.setTextColor(QColor(0, 255, 255).rgba())
                elif look_data[1] == LookPresentState.AnteriorVersionPlugged:
                    look_list_widget.setTextColor(QColor(255, 255, 0).rgba())

    def __retrieve_standins(self):
        """
        Retrieve the standins : all valid standin if selection is None
        or all valid standins within selection
        :return:
        """
        self.__standins.clear()
        selection = pm.ls(selection=True)
        if len(selection) > 0:
            for sel in selection:
                if pm.objectType(sel, isType="aiStandIn"):
                    # Standin found
                    look_obj = self.__look_factory.generate(sel)
                    if look_obj is not None: self.__standins[look_obj.get_object_name()] = look_obj
                elif pm.objectType(sel, isType="transform"):
                    prt = sel.getParent()
                    if prt is not None and pm.objectType(prt, isType="transform"):
                        shape = prt.getShape()
                        if shape is not None and pm.objectType(shape, isType="aiStandIn"):
                            # Proxy of Standin found
                            look_obj = self.__look_factory.generate(shape)
                            if look_obj is not None: self.__standins[look_obj.get_object_name()] = look_obj

                for rel in pm.listRelatives(sel, allDescendents=True, type="aiStandIn"):
                    look_obj = self.__look_factory.generate(rel)
                    if look_obj is not None: self.__standins[look_obj.get_object_name()] = look_obj
        else:
            for standin in pm.ls(type="aiStandIn"):
                if standin.name().startswith("frame"):
                    continue
                look_obj = self.__look_factory.generate(standin)
                if look_obj is not None: self.__standins[look_obj.get_object_name()] = look_obj

        self.__standins = dict(sorted(self.__standins.items()))


    def __on_replace_looks_checked(self, state):
        self.__replace_looks = state

    def __on_scene_selection_changed(self, *args, **kwargs):
        """
        On scene selection changed
        :param args
        :param kwargs
        :return:
        """
        if self.__refresh_selection:
            self.__retrieve_standins()
            self.__refresh_standin_table()
            self.__on_standin_select_changed()

    def __on_standin_select_changed(self):
        """
        On standin selected changed in standin table
        :return:
        """
        if self.__refresh_selection:
            rows_selected = self.__ui_standin_table.selectionModel().selectedRows()
            if len(rows_selected) > 0:
                row_selected = rows_selected[0]
                self.__standin_obj_selected = self.__ui_standin_table.item(row_selected.row(), 0).data(Qt.UserRole)
            else:
                self.__standin_obj_selected = None
            self.__refresh_looks_list()
            self.__refresh_btn()

    def __on_look_selected_changed(self):
        """
        On Look selected changed in Look list
        :return:
        """
        self.__file_looks_selected.clear()
        selected_items = self.__ui_looks_list.selectedItems()
        for item in selected_items:
            self.__file_looks_selected.append(item.data(Qt.UserRole))
        self.__refresh_btn()

    def __on_add_looks_to_standin(self):
        """
        Add selected looks to selected standin
        :return:
        """
        self.__refresh_selection = False
        self.__standin_obj_selected.add_looks(self.__file_looks_selected, self.__replace_looks)
        self.__standin_obj_selected.retrieve_looks(self.__current_project_dir)
        self.__refresh_selection = True
        self.__refresh_standin_table()
        self.__refresh_looks_list()
