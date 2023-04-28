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

from .LookStandin import LookStandin, LookPresentState

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

        # UI attributes
        self.__ui_width = 600
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

    def showEvent(self, arg__1: QShowEvent) -> None:
        self.__selection_callback = \
            OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.__on_scene_selection_changed)

    def hideEvent(self, arg__1: QCloseEvent) -> None:
        OpenMaya.MMessage.removeCallback(self.__selection_callback)
        self.__save_prefs()

    # Create the ui
    def __create_ui(self):
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
        main_lyt.addLayout(grid_layout)
        grid_layout.setRowStretch(1, 1)
        grid_layout.setColumnStretch(0, 2)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.addWidget(QLabel("Standins"), 0, 0, alignment=Qt.AlignCenter)
        grid_layout.addWidget(QLabel("Looks"), 0, 1, alignment=Qt.AlignCenter)

        # Standin Table
        self.__ui_standin_table = QTableWidget(0, 3)
        self.__ui_standin_table.setHorizontalHeaderLabels(["Name", "Standin Name", "Number looks"])
        self.__ui_standin_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__ui_standin_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.__ui_standin_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_standin_table.verticalHeader().hide()
        self.__ui_standin_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__ui_standin_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_standin_table.itemSelectionChanged.connect(self.__on_standin_select_changed)
        grid_layout.addWidget(self.__ui_standin_table, 1, 0)

        # List of Looks
        self.__ui_looks_list = QListWidget()
        self.__ui_looks_list.setSpacing(2)
        self.__ui_looks_list.setStyleSheet("font-size:14px")
        self.__ui_looks_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_looks_list.itemSelectionChanged.connect(self.__on_look_selected_changed)
        grid_layout.addWidget(self.__ui_looks_list, 1, 1)

        # Button
        self.__ui_add_looks_to_standin_btn = QPushButton("Add Looks to the StandIn")
        self.__ui_add_looks_to_standin_btn.clicked.connect(self.__on_add_looks_to_standin)
        main_lyt.addWidget(self.__ui_add_looks_to_standin_btn)

    # Refresh the ui according to the model attribute
    def __refresh_ui(self):
        self.__refresh_standin_table()
        self.__refresh_btn()

    # Refresh the buttons
    def __refresh_btn(self):
        self.__ui_add_looks_to_standin_btn.setEnabled(self.__standin_obj_selected is not None and
                                                      len(self.__file_looks_selected)>0)

    # Refresh the standin table
    def __refresh_standin_table(self):
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
            row_index += 1
        if row_selected is not None:
            self.__ui_standin_table.selectRow(row_selected)
        self.__refresh_selection = refresh_selection

    # Refresh the looks
    def __refresh_looks_list(self):
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

    # Retrieve the standins : all valid standin if selection is None
    # or all valid standins within selection
    def __retrieve_standins(self):
        self.__standins.clear()
        standins = []
        selection = pm.ls(selection=True)
        if len(selection) > 0:
            for sel in selection:
                if pm.objectType(sel, isType="aiStandIn"):
                    # Standin found
                    standins.append(LookStandin(sel))
                elif pm.objectType(sel, isType="transform"):
                    prt = sel.getParent()
                    if prt is not None and pm.objectType(prt, isType="transform"):
                        shape = prt.getShape()
                        if shape is not None and pm.objectType(shape, isType="aiStandIn"):
                            # Proxy of Standin found
                            standins.append(LookStandin(shape))

                for rel in pm.listRelatives(sel, allDescendents=True, type="aiStandIn"):
                    standins.append(LookStandin(rel))
        else:
            standins = [LookStandin(standin) for standin in pm.ls(type="aiStandIn")]

        for standin in standins:
            if standin.is_valid():
                self.__standins[standin.get_object_name()] = standin
        self.__standins = dict(sorted(self.__standins.items()))

    # On scene selection changed
    def __on_scene_selection_changed(self, *args, **kwargs):
        if self.__refresh_selection:
            self.__retrieve_standins()
            self.__refresh_standin_table()
            self.__on_standin_select_changed()

    # On standin selected changed in standin table
    def __on_standin_select_changed(self):
        if self.__refresh_selection:
            rows_selected = self.__ui_standin_table.selectionModel().selectedRows()
            if len(rows_selected) > 0:
                row_selected = rows_selected[0]
                self.__standin_obj_selected = self.__ui_standin_table.item(row_selected.row(), 0).data(Qt.UserRole)
            else:
                self.__standin_obj_selected = None
            self.__refresh_looks_list()
            self.__refresh_btn()


    # On Look selected changed in Look list
    def __on_look_selected_changed(self):
        self.__file_looks_selected.clear()
        selected_items = self.__ui_looks_list.selectedItems()
        for item in selected_items:
            self.__file_looks_selected.append(item.data(Qt.UserRole))
        self.__refresh_btn()

    # Add selected looks to selected standin
    def __on_add_looks_to_standin(self):
        self.__refresh_selection = False
        self.__standin_obj_selected.add_looks(self.__file_looks_selected)
        self.__standin_obj_selected.retrieve_looks()
        self.__refresh_selection = True
        self.__refresh_standin_table()
        self.__refresh_looks_list()
