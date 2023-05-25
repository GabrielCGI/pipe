import os
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

# ######################################################################################################################

_FILE_NAME_PREFS = "auto_comp"

_DEFAULT_SHOT_DIR = "I:/"

_UNPACK_MODES_DIR = os.path.dirname(__file__) + "/mode"

# ######################################################################################################################


class AutoComp(QWidget):
    # Test if a folder is a correct shot path
    @staticmethod
    def __is_correct_shot_folder(folder):
        return os.path.isdir(os.path.join(folder, "render_out")) and os.path.isdir(folder)

    def __init__(self, prt=None):
        super(AutoComp, self).__init__(prt)
        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        # Model attributes
        self.__shot_path = r"I:\battlestar_2206\shots\lordsMobile_shot050" #TODO remove
        # self.__shot_path = ""
        self.__unpack_modes=[]
        self.__selected_unpack_mode=None
        self.__selected_layer=None

        self.__retrieve_unpack_modes(_UNPACK_MODES_DIR)

        # UI attributes
        self.__ui_width = 400
        self.__ui_height = 150
        self.__ui_min_width = 250
        self.__ui_min_height = 150
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        self.__retrieve_prefs()
        self.__retrieve_selected_unpack_mode()

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

    # Remove callbacks
    def hideEvent(self, arg__1):
        self.__save_prefs()

    # Save preferences
    def __save_prefs(self):
        if self.__selected_unpack_mode is not None:
            self.__prefs["unpack_mode"] = self.__selected_unpack_mode.get_name()

    # Retrieve preferences
    def __retrieve_prefs(self):
        self.__retrieve_unpack_mode_prefs()

    def __retrieve_unpack_mode_prefs(self):
        if "unpack_mode" in self.__prefs:
            sel_unpack_mode_name = self.__prefs["unpack_mode"]
            for unpack_mode in self.__unpack_modes:
                if unpack_mode.get_name() == str(sel_unpack_mode_name):
                    self.__selected_unpack_mode = unpack_mode
                    break

    def __retrieve_unpack_modes(self, unpack_mode_dir):
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

    def __retrieve_selected_unpack_mode(self):
        if self.__selected_unpack_mode is None and len(self.__unpack_modes) > 0:
            self.__selected_unpack_mode = self.__unpack_modes[0]


    # Create the ui
    def __create_ui(self):
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        browse_icon_path = os.path.dirname(__file__) + "/assets/browse.png"

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setSpacing(5)
        main_lyt.setAlignment(Qt.AlignTop)
        self.setLayout(main_lyt)

        shot_path_lyt = QVBoxLayout()
        shot_path_lyt.setAlignment(Qt.AlignCenter)
        main_lyt.addLayout(shot_path_lyt)

        lbl_shot_to_autocomp = QLabel("Shot to AutoComp")
        shot_path_lyt.addWidget(lbl_shot_to_autocomp)

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
        main_lyt.addLayout(unpack_mode_lyt)

        lbl_unpack_mode = QLabel("Unpack Mode")
        unpack_mode_lyt.addWidget(lbl_unpack_mode)

        self.__ui_unpack_mode = QComboBox()
        for unpack_mode in self.__unpack_modes:
            if unpack_mode.is_valid():
                self.__ui_unpack_mode.addItem(unpack_mode.get_name(), userData=unpack_mode)
        self.__ui_unpack_mode.currentIndexChanged.connect(self.__on_unpack_mode_changed)
        unpack_mode_lyt.addWidget(self.__ui_unpack_mode)

        rule_set_lyt = QGridLayout()
        rule_set_lyt.setSpacing(5)
        rule_set_lyt.setColumnStretch(0, 1)
        rule_set_lyt.setColumnStretch(1, 2)
        main_lyt.addLayout(rule_set_lyt)

        self.__ui_start_vars_list = QListWidget()
        self.__ui_start_vars_list.setSpacing(2)
        self.__ui_start_vars_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__ui_start_vars_list.currentItemChanged.connect(self.__on_layer_selected)
        self.__ui_start_vars_list.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Minimum)
        rule_set_lyt.addWidget(self.__ui_start_vars_list,0,0)

        self.__ui_relations_list = QListWidget()
        self.__ui_relations_list.setSpacing(2)
        self.__ui_relations_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.__ui_relations_list.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Minimum)
        rule_set_lyt.addWidget(self.__ui_relations_list,0,1)

        self.__ui_autocomp_btn = QPushButton("AutoComp")
        self.__ui_autocomp_btn.setFixedHeight(30)
        self.__ui_autocomp_btn.clicked.connect(self.__unpack)
        rule_set_lyt.addWidget(self.__ui_autocomp_btn,1,0,1,3)

        self.__ui_shuffle_btn = QPushButton("Shuffle selected layer")
        self.__ui_shuffle_btn.setFixedHeight(30)
        self.__ui_shuffle_btn.clicked.connect(self.__shuffle_layer)
        rule_set_lyt.addWidget(self.__ui_shuffle_btn,2,0,1,3)

        main_lyt.addLayout(rule_set_lyt)

    # Refresh the ui according to the model attribute
    def __refresh_ui(self):
        self.__refresh_btn()
        self.__refresh_unpack_modes()
        self.__refresh_start_vars_list()
        self.__refresh_relations_list()

    def __refresh_btn(self):
        self.__refresh_shuffle_btn()
        self.__refresh_autocomp_btn()

    def __refresh_shuffle_btn(self):
        self.__ui_shuffle_btn.setEnabled(
            self.__selected_layer is not None and self.__selected_unpack_mode is not None and
            os.path.isdir(os.path.join(self.__shot_path, "render_out")))

    def __refresh_autocomp_btn(self):
        self.__ui_autocomp_btn.setEnabled(
            self.__selected_unpack_mode is not None and os.path.isdir(os.path.join(self.__shot_path, "render_out")))

    def __refresh_unpack_modes(self):
        for index in range(self.__ui_unpack_mode.count()):
            if self.__ui_unpack_mode.itemData(index, Qt.UserRole) == self.__selected_unpack_mode:
                self.__ui_unpack_mode.setCurrentIndex(index)

    def __refresh_start_vars_list(self):
        self.__ui_start_vars_list.clear()
        if self.__selected_unpack_mode is not None:
            start_vars = [var for var in self.__selected_unpack_mode.get_var_set().get_start_vars()]
            for var in start_vars:
                var_str = str(var)
                item = QListWidgetItem(var_str)
                item.setData(Qt.UserRole, var)
                self.__ui_start_vars_list.addItem(item)
                if not self.__selected_unpack_mode.layer_is_scanned(var_str):
                    item.setFlags(Qt.NoItemFlags)

    def __refresh_relations_list(self):
        self.__ui_relations_list.clear()
        if self.__selected_unpack_mode is not None:
            relations_str = []
            for rel in self.__selected_unpack_mode.get_merge_mode().get_relations():
                relations_str.append(str(rel))
            for rel_str in relations_str:
                self.__ui_relations_list.addItem(QListWidgetItem(rel_str))

    # Browse a new abc folder
    def __browse_folder(self):
        dirname = nuke.root()['name'].value()
        if len(dirname) == 0:
            dirname = _DEFAULT_SHOT_DIR
        shot_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Shot Directory", dirname)
        self.__set_shot_path(shot_path)

    def __set_shot_path(self, shot_path):
        if AutoComp.__is_correct_shot_folder(shot_path) and shot_path != self.__shot_path:
            self.__ui_shot_path.setText(shot_path)

    # Retrieve the folder path on folder linedit change
    def __on_folder_changed(self):
        self.__shot_path = self.__ui_shot_path.text()
        self.__scan_layers()
        self.__refresh_btn()

    def __on_unpack_mode_changed(self, index):
        self.__selected_unpack_mode = self.__ui_unpack_mode.itemData(index, Qt.UserRole)
        self.__scan_layers()
        self.__refresh_start_vars_list()
        self.__refresh_relations_list()
        self.__selected_layer = None
        self.__refresh_shuffle_btn()

    def __on_layer_selected(self, current):
        self.__selected_layer = current.data(Qt.UserRole)
        self.__refresh_shuffle_btn()

    def __scan_layers(self):
        if self.__selected_unpack_mode is not None:
            self.__selected_unpack_mode.scan_layers(self.__shot_path)

    def __reinit_auto_comp(self):
        self.__retrieve_unpack_modes(_UNPACK_MODES_DIR)
        self.__retrieve_unpack_mode_prefs()
        self.__retrieve_selected_unpack_mode()
        self.__scan_layers()

    def __shuffle_layer(self):
        unpack_mode = AutoCompFactory.get_simple_shuffle_layer_mode(
            self.__selected_unpack_mode.get_config_path(), self.__selected_layer.get_name())
        unpack_mode.scan_layers(self.__shot_path)
        unpack_mode.unpack(self.__shot_path)
        self.__reinit_auto_comp()

    def __unpack(self):
        self.__prefs["unpack_mode"] = self.__selected_unpack_mode.get_name()
        self.__selected_unpack_mode.unpack(self.__shot_path)
        self.__reinit_auto_comp()
