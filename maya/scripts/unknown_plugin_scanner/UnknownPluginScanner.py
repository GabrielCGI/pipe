import re
import os
import sys
import json
import subprocess
import threading

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from functools import partial
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
import maya.OpenMaya as OpenMaya

import pymel.core as pm

from common.utils import *
from common.Prefs import *
from .Reference import Reference

# ######################################################################################################################

_FILE_NAME_PREFS = "unknown_plugin_scanner"

# ######################################################################################################################


class UnknownPluginScanner(QDialog):

    def __init__(self, prnt=wrapInstance(int(omui.MQtUtil.mainWindow()), QWidget)):
        super(UnknownPluginScanner, self).__init__(prnt)

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__refs = []
        self.__retrieve_refs()
        self.__current_path = None
        self.__progress_value = 0
        self.__refreshing=False
        self.__refreshing_lock = threading.Lock()

        # UI attributes
        self.__ui_width = 500
        self.__ui_height = 700
        self.__ui_min_width = 300
        self.__ui_min_height = 300
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()

        # name the window
        self.setWindowTitle("Unknown Plugin Scanner")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

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
        pass

    # Remove callbacks
    def hideEvent(self, arg__1: QCloseEvent) -> None:
        self.__save_prefs()

    # Create the ui
    def __create_ui(self):
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(8, 10, 8, 10)
        main_lyt.setSpacing(8)
        self.setLayout(main_lyt)

        self.__ui_scan_btn = QPushButton("Scan referenced files for Unknown Node")
        self.__ui_scan_btn.clicked.connect(self.__scan_for_unknown_plugins)
        main_lyt.addWidget(self.__ui_scan_btn)

        self.__progress_bar = QProgressBar()
        self.__progress_bar.setFixedHeight(20)
        main_lyt.addWidget(self.__progress_bar)

        self.__ui_tree_refs = QTreeWidget()
        self.__ui_tree_refs.setStyleSheet("QTreeWidget::item{padding: 3px 0;}")
        self.__ui_tree_refs.setHeaderHidden(True)
        self.__ui_tree_refs.itemSelectionChanged.connect(self.__on_ref_selected)
        main_lyt.addWidget(self.__ui_tree_refs)

        self.__ui_line_edit = QLineEdit()
        self.__ui_line_edit.setPlaceholderText("Path of the selected reference")
        self.__ui_line_edit.setReadOnly(True)
        main_lyt.addWidget(self.__ui_line_edit)

    # Refresh the ui according to the model attributes
    def __refresh_ui(self):
        self.__refresh_tree_list(True)
        self.__refresh_line_edit()
        self.__refresh_progress_bar()

    def __refresh_progress_bar(self):
        with self.__refreshing_lock:
            self.__progress_bar.setValue(self.__progress_value)

    def __refresh_tree_list(self, waiting_for_scan_if_empty = False):
        with self.__refreshing_lock:
            self.__ui_tree_refs.clear()
            for ref in self.__refs:
                item = QTreeWidgetItem([ref.get_name()])
                item.setData(0, Qt.UserRole, ref)
                self.__ui_tree_refs.addTopLevelItem(item)
                ukn_plugins = ref.get_unknown_plugin_names()
                if len(ukn_plugins)>0:
                    for ukn_plugin in ukn_plugins:
                        child = QTreeWidgetItem([ukn_plugin])
                        child.setData(0, Qt.UserRole, ref)
                        item.addChild(child)
                else:
                    if waiting_for_scan_if_empty:
                        child = QTreeWidgetItem(["Waiting for scan ..."])
                        child.setData(0, Qt.UserRole, ref)
                        child.setDisabled(True)
                        item.addChild(child)
                    else:
                        item.setDisabled(True)
            self.__ui_tree_refs.expandAll()

    def __refresh_line_edit(self):
        self.__ui_line_edit.setText(self.__current_path if self.__current_path is not None else "")

    def __retrieve_refs(self):
        self.__refs.clear()
        refs = pm.ls(references=True)
        for ref in refs:
            ref_obj = Reference(ref)
            if ref.isLoaded() and re.match(r"^.*\.(?:ma|mb)$", ref_obj.get_filepath()):
                self.__refs.append(ref_obj)

    def __on_ref_selected(self):
        items = self.__ui_tree_refs.selectedItems()
        if len(items) == 0:
            self.__current_path = None
        else:
            self.__current_path = items[0].data(0,Qt.UserRole).get_filepath()
        self.__refresh_line_edit()

    def __scan_for_unknown_plugins(self):
        self.__progress_value = 1
        self.__refresh_progress_bar()
        with self.__refreshing_lock:
            self.__ui_scan_btn.setDisabled(True)

        msg_result = "UNKNOWN_NODE_SCANNER_RESULT"
        filepath = __file__
        folder = os.path.dirname(filepath)
        exec_file = os.path.join(folder, "scan_ref.py")
        input_data = [(ref.get_name(), ref.get_filepath()) for ref in self.__refs]
        process = subprocess.Popen(
            [r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe", exec_file, msg_result, json.dumps(input_data)],
            stdout=subprocess.PIPE, universal_newlines=True, shell=True)
        nb_ref = len(self.__refs)
        self.__refs.clear()
        self.__refresh_tree_list()
        for stdout_line in iter(process.stdout.readline, ""):
            stdout_line = stdout_line.strip("\n")
            if not stdout_line.startswith(msg_result):
                continue
            match = re.match(r"^" + msg_result + " (.*)$", stdout_line)
            result_data = json.loads(match.group(1))
            ref = Reference(data=result_data)
            self.__refs.append(ref)
            self.__progress_value = min(self.__progress_value + 100 / nb_ref, 100)

            try:
                self.__refresh_progress_bar()
                self.__refresh_tree_list()
            except:
                pass

        try:
            self.__progress_value = 100
            self.__refresh_progress_bar()
            with self.__refreshing_lock:
                self.__ui_scan_btn.setDisabled(False)
        except:
            pass
        process.stdout.close()
        process.wait()
