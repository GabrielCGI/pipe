import os
from functools import partial

import sys

import pymel.core as pm
import maya.OpenMayaUI as omui

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from shiboken2 import wrapInstance

import utils

from Prefs import *
from Standin import *

import maya.OpenMaya as OpenMaya

# ######################################################################################################################

_FILE_NAME_PREFS = "asset_loader"


# ######################################################################################################################

class AssetLoader(QtWidgets.QDialog):

    def __init__(self, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)):
        super(AssetLoader, self).__init__(prnt)

        # Common Preferences (common preferences on all illogic tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Assets
        self.__asset_path = os.path.dirname(__file__) + "/assets"

        # Model attributes
        self.__standins = {}
        self.__sel_standins = []
        self.__variants_and_versions_enabled = False
        self.__standing_table_refresh_select = True

        # UI attributes
        self.__ui_width = 850
        self.__ui_height = 500
        self.__ui_min_width = 600
        self.__ui_min_height = 300
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width,self.__ui_height)/2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("Asset Loader")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # retrieve datas
        self.__retrieve_standins()

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()
        self.__select_all_standin()
        self.__create_callback()

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
            self.__ui_pos = QPoint(pos["x"],pos["y"])

    # Create callbacks
    def __create_callback(self):
        self.__selection_callback = \
            OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self.__scene_selection_changed)

    # Remove callbacks
    def hideEvent(self, arg__1: QtGui.QCloseEvent) -> None:
        OpenMaya.MMessage.removeCallback(self.__selection_callback)
        self.__save_prefs()

    # On scene changed we want to retrieve the standins selected and refresh the ui
    def __scene_selection_changed(self, *args, **kwargs):
        self.__retrieve_standins()
        self.__refresh_standin_table()
        self.__select_all_standin()
        self.__on_standin_select_changed()

    # Test if a Transform ndoe has a standin in child shape
    @staticmethod
    def __test_trsf_has_standin(trsf):
        if trsf is not None:
            shape = trsf.getShape()
            if shape is not None and pm.objectType(shape, isType="aiStandIn"):
                return True
        return False

    # Retrieve the standins
    def __retrieve_standins(self):
        self.__standins.clear()

        selection = pm.ls(selection=True)
        if len(selection)>0:
            standins = {}
            for sel in selection:
                if pm.objectType(sel, isType="aiStandIn"):
                    # Standin found
                    standins[sel.name()] = Standin(sel)
                elif pm.objectType(sel, isType="transform"):
                    prt = sel.getParent()
                    if prt is not None and pm.objectType(prt, isType="transform"):
                        shape = prt.getShape()
                        if shape is not None and pm.objectType(shape, isType="aiStandIn"):
                            # Proxy of Standin found
                            standins[shape.name()] = Standin(shape)

                for rel in pm.listRelatives(sel, allDescendents=True, type="aiStandIn"):
                    standins[rel.name()] = Standin(rel)

            for name, standin in standins.items():
                if standin.is_valid():
                    self.__standins[name] = standin
        else:
            standins = pm.ls(type="aiStandIn")
            for standin in standins:
                standin_inst = Standin(standin)
                if standin_inst.is_valid() and not standin_inst.is_up_to_date():
                    self.__standins[standin.name()] = standin_inst

        self.__standins = dict(sorted(self.__standins.items()))



    # Create the ui
    def __create_ui(self):
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(8, 10, 8, 10)
        self.setLayout(main_lyt)

        # ML.1 : Top grid layout
        top_grid_layout = QGridLayout()
        top_grid_layout.setSpacing(8)
        top_grid_layout.setColumnStretch(0, 2)
        top_grid_layout.setColumnStretch(1, 1)
        main_lyt.addLayout(top_grid_layout)

        # ML.1.1 : Left title
        left_title = QLabel("Standins in Scene")
        left_title.setAlignment(Qt.AlignCenter)
        top_grid_layout.addWidget(left_title, 0, 0)
        # ML.1.2 : Right title
        right_title = QLabel("Variant - Version")
        right_title.setAlignment(Qt.AlignCenter)
        top_grid_layout.addWidget(right_title, 0, 1)

        # ML.1.3 : Table Standins
        self.__ui_standin_table = QTableWidget(0, 4)
        self.__ui_standin_table.setHorizontalHeaderLabels(["Name", "Asset", "Variant", "Version"])
        self.__ui_standin_table.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.__ui_standin_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.__ui_standin_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__ui_standin_table.verticalHeader().hide()
        self.__ui_standin_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__ui_standin_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.__ui_standin_table.itemSelectionChanged.connect(self.__on_standin_select_changed)
        top_grid_layout.addWidget(self.__ui_standin_table, 1, 0)
        # ML.1.4 : Content Right layout
        content_right_layout = QVBoxLayout()
        top_grid_layout.addLayout(content_right_layout, 1, 1)
        # ML.1.4.1 : Lists layout
        right_lists_layout = QHBoxLayout()
        content_right_layout.addLayout(right_lists_layout)
        # ML.1.4.1.1 : Variant List
        self.__ui_variant_list = QListWidget()
        self.__ui_variant_list.setSpacing(2)
        self.__ui_variant_list.setStyleSheet("font-size:14px")
        self.__ui_variant_list.itemSelectionChanged.connect(self.__on_variant_selected_changed)
        right_lists_layout.addWidget(self.__ui_variant_list, 3)
        # ML.1.4.1.2 : Version List
        self.__ui_version_list = QListWidget()
        self.__ui_version_list.setStyleSheet("font-size:16px")
        self.__ui_version_list.setSpacing(4)
        self.__ui_version_list.setFixedWidth(70)
        self.__ui_version_list.itemSelectionChanged.connect(self.__refresh_btn)
        right_lists_layout.addWidget(self.__ui_version_list)
        # ML.1.4.2 : Button set version
        self.__ui_submit_version_btn = QPushButton("Set version")
        self.__ui_submit_version_btn.clicked.connect(self.__set_version)
        content_right_layout.addWidget(self.__ui_submit_version_btn)
        # ML.1.5 : Buttons left layout
        btn_left_lyt = QHBoxLayout()
        top_grid_layout.addLayout(btn_left_lyt, 2, 0)
        # ML.1.5.1 : Select out of date standins
        self.__ui_select_ood_standins_btn = QPushButton()
        self.__ui_select_ood_standins_btn.clicked.connect(self.__select_all_ood)
        self.__ui_select_ood_standins_btn.setIcon(QIcon(self.__asset_path + "/warning.png"))
        height_hint = self.__ui_select_ood_standins_btn.sizeHint().height()
        self.__ui_select_ood_standins_btn.setFixedSize(QSize(height_hint, height_hint))
        btn_left_lyt.addWidget(self.__ui_select_ood_standins_btn)
        # ML.1.5.2 : Update to last
        self.__ui_update_to_last_btn = QPushButton("Update to last")
        self.__ui_update_to_last_btn.clicked.connect(self.__update_to_last)
        btn_left_lyt.addWidget(self.__ui_update_to_last_btn)
        # ML.1.6 : Buttons right layout
        btn_right_lyt = QHBoxLayout()
        top_grid_layout.addLayout(btn_right_lyt, 2, 1)
        # ML.1.6.1 : To SD Button
        self.__ui_to_sd_btn = QPushButton("to SD")
        self.__ui_to_sd_btn.clicked.connect(self.__set_to_sd)
        btn_right_lyt.addWidget(self.__ui_to_sd_btn)
        # ML.1.6.2 : To HD Button
        self.__ui_to_hd_btn = QPushButton("to HD")
        self.__ui_to_hd_btn.clicked.connect(self.__set_to_hd)
        btn_right_lyt.addWidget(self.__ui_to_hd_btn)

        # ML.2 : Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        main_lyt.addWidget(sep)

        # ML.3 : Button bottom
        bottom_btn_lyt = QHBoxLayout()
        bottom_btn_lyt.setAlignment(Qt.AlignCenter)
        main_lyt.addLayout(bottom_btn_lyt)
        # ML.3.1 : Convert to maya button
        self.__ui_to_maya_btn = QPushButton("Convert to Maya")
        self.__ui_to_maya_btn.setFixedWidth(180)
        self.__ui_to_maya_btn.clicked.connect(self.__convert_to_maya)
        bottom_btn_lyt.addWidget(self.__ui_to_maya_btn)
        # ML.3.2 : Add transforms
        self.__ui_add_transforms = QPushButton("Add Transforms")
        self.__ui_add_transforms.setFixedWidth(180)
        self.__ui_add_transforms.setEnabled(False)  # TODO to implement
        bottom_btn_lyt.addWidget(self.__ui_add_transforms)

    # Refresh the ui according to the model attribute
    def __refresh_ui(self):
        self.__refresh_standin_table()
        self.__check_variants_versions_enabled()
        self.__refresh_variants_list()
        self.__refresh_versions_list()
        self.__refresh_btn()

    # Select all the standins selected
    def __select_all_standin(self):
        self.__ui_standin_table.selectAll()

    # Check if the selected standins can be treated as one in the variants and version editor
    def __check_variants_versions_enabled(self):
        self.__variants_and_versions_enabled = False
        standin_curr = None
        for standin in self.__sel_standins:
            if standin_curr is None:
                standin_curr = standin
                self.__variants_and_versions_enabled = True

            if standin_curr.get_standin_name() != standin.get_standin_name() \
                    or standin_curr.get_active_variant() != standin.get_active_variant() \
                    or standin_curr.get_active_version() != standin.get_active_version():
                self.__variants_and_versions_enabled = False
                break

    # Refresh the standins table and their data
    def __refresh_standin_table(self):
        standing_table_refresh_select_prev = self.__standing_table_refresh_select
        self.__standing_table_refresh_select = False
        self.__ui_standin_table.setRowCount(0)
        row_index = 0
        rows_selected = []
        for standin in self.__standins.values():
            self.__ui_standin_table.insertRow(row_index)
            object_name = standin.get_object_name()
            standin_name = standin.get_standin_name()

            if standin in self.__sel_standins:
                rows_selected.append(row_index)

            active_variant = standin.get_active_variant()
            active_version = standin.get_active_version()

            if standin.is_up_to_date():
                version_str = active_version
                asset_icon = self.__asset_path + "/valid.png"
            else:
                version_str = active_version + " -> " + standin.last_version()
                asset_icon = self.__asset_path + "/warning.png"

            object_name_item = QTableWidgetItem(object_name)
            object_name_item.setIcon(QIcon(asset_icon))
            object_name_item.setData(Qt.UserRole, standin)
            self.__ui_standin_table.setItem(row_index, 0, object_name_item)

            standin_name_item = QTableWidgetItem(standin_name)
            standin_name_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_standin_table.setItem(row_index, 1, standin_name_item)

            variant_item = QTableWidgetItem(active_variant)
            variant_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_standin_table.setItem(row_index, 2, variant_item)

            version_item = QTableWidgetItem(version_str)
            version_item.setTextAlignment(Qt.AlignCenter)
            self.__ui_standin_table.setItem(row_index, 3, version_item)
            row_index += 1

        self.__ui_standin_table.setSelectionMode(QAbstractItemView.MultiSelection)
        for row_index in rows_selected:
            self.__ui_standin_table.selectRow(row_index)
        self.__ui_standin_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.__standing_table_refresh_select = standing_table_refresh_select_prev

    # Refrsh the list of variants
    def __refresh_variants_list(self):
        self.__ui_variant_list.clear()
        self.__ui_variant_list.setEnabled(self.__variants_and_versions_enabled)
        if self.__variants_and_versions_enabled:
            standin = self.__sel_standins[0]
            active_variant = standin.get_active_variant()
            var_vers = standin.get_versions()
            for variant in var_vers.keys():
                variant_list_widget = QListWidgetItem(variant)
                self.__ui_variant_list.addItem(variant_list_widget)
                if active_variant == variant:
                    self.__ui_variant_list.setItemSelected(variant_list_widget, True)
                    variant_list_widget.setTextColor(QColor(0, 255, 255).rgba())

    # Refresh the list of versions
    def __refresh_versions_list(self):
        self.__ui_version_list.clear()
        self.__ui_version_list.setEnabled(self.__variants_and_versions_enabled)
        if self.__variants_and_versions_enabled:
            standin = self.__sel_standins[0]
            variants_and_versions = standin.get_versions()
            active_variant = standin.get_active_variant()
            try:
                selected_variant = self.__ui_variant_list.selectedItems()[0].text()
            except:
                return
            versions_active_variant = variants_and_versions[selected_variant]
            active_version = standin.get_active_version()
            for version in versions_active_variant:
                version_list_widget = QListWidgetItem(version[0])
                self.__ui_version_list.addItem(version_list_widget)
                if active_variant == selected_variant and active_version == version[0]:
                    self.__ui_version_list.setItemSelected(version_list_widget, True)
                    version_list_widget.setTextColor(QColor(0, 255, 255).rgba())

    # Refresh the buttons
    def __refresh_btn(self):
        many_sel_standin = len(self.__sel_standins) > 0
        version_items = self.__ui_version_list.selectedItems()
        variant_items = self.__ui_variant_list.selectedItems()
        variant = None
        version = None
        if len(variant_items) > 0 and len(version_items) > 0:
            variant = variant_items[0].text()
            version = version_items[0].text()

        has_sd = False
        has_hd = False
        up_to_date = False
        set_version = False
        for standin in self.__sel_standins:
            if not standin.is_up_to_date():
                up_to_date = True
            if standin.has_version_in_sd():
                has_sd = True
            if standin.has_version_in_hd():
                has_hd = True
            if standin.get_active_version() != version or standin.get_active_variant() != variant:
                set_version = True

        self.__ui_update_to_last_btn.setEnabled(up_to_date)
        self.__ui_submit_version_btn.setEnabled(self.__variants_and_versions_enabled and set_version and
                                                len(version_items) > 0)

        self.__ui_to_sd_btn.setEnabled(has_sd)
        self.__ui_to_hd_btn.setEnabled(has_hd)

        self.__ui_to_maya_btn.setEnabled(many_sel_standin)

    # Retrieve the standins selected when the selection in the standing table changes
    def __on_standin_select_changed(self):
        if self.__standing_table_refresh_select:
            self.__sel_standins.clear()
            for s in self.__ui_standin_table.selectionModel().selectedRows():
                self.__sel_standins.append(self.__ui_standin_table.item(s.row(), 0).data(Qt.UserRole))
            self.__check_variants_versions_enabled()
            self.__refresh_variants_list()
            self.__refresh_versions_list()
            self.__refresh_btn()

    def __on_variant_selected_changed(self):
        self.__refresh_btn()
        self.__refresh_versions_list()

    # Select all the standins that are out of dates
    def __select_all_ood(self):
        self.__ui_standin_table.clearSelection()
        self.__ui_standin_table.setSelectionMode(QAbstractItemView.MultiSelection)
        for i in range(self.__ui_standin_table.rowCount()):
            standin = self.__ui_standin_table.item(i, 0).data(Qt.UserRole)
            if not standin.is_up_to_date():
                self.__ui_standin_table.selectRow(i)
        self.__ui_standin_table.setSelectionMode(QAbstractItemView.ExtendedSelection)

    # Set the variant and the version selected to the standins selected
    def __set_version(self):
        if self.__variants_and_versions_enabled:
            version_items = self.__ui_version_list.selectedItems()
            variant_items = self.__ui_variant_list.selectedItems()
            if len(variant_items) > 0 and len(version_items) > 0:
                version_item = version_items[0]
                variant_item = variant_items[0]
                for standin in self.__sel_standins:
                    standin.set_active_variant_version(variant_item.text(), version_item.text())
                self.__refresh_ui()

    # Update all the standins selected versions to the last of their variant
    def __update_to_last(self):
        for standin in self.__sel_standins:
            standin.update_to_last()
        self.__refresh_ui()

    # Set to an SD variant
    def __set_to_sd(self):
        for standin in self.__sel_standins:
            standin.set_to_sd()
        self.__refresh_ui()

    # Set to an HD variant
    def __set_to_hd(self):
        for standin in self.__sel_standins:
            standin.set_to_hd()
        self.__refresh_ui()

    # Convert the standins selected to Maya object
    def __convert_to_maya(self):
        self.__standing_table_refresh_select = False
        standins = self.__sel_standins
        for standin in standins:
            standin.convert_to_maya()
        self.__standing_table_refresh_select = True
        self.__refresh_ui()
