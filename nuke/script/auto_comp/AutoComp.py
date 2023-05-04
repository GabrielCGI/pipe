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
import nuke
from nukescripts import panels
from .UnpackMode import UnpackMode
from .ShuffleMode import MergeShuffleMode
from .MergeMode import MergeMode

# ######################################################################################################################

_UNPACk_MODES = [
    UnpackMode("Classic Unpack Mode",MergeShuffleMode(), MergeMode("test")),
    UnpackMode("Other Unpack Mode",MergeShuffleMode(), MergeMode("test"))
]

# ######################################################################################################################

class AutoComp(QWidget):

    def __init__(self, prt=None):
        super(AutoComp, self).__init__(prt)

        # Model attributes
        self.__shot_path = ""
        self.__unpack_mode=None

        # UI attributes
        self.__ui_width = 400
        self.__ui_height = 150
        self.__ui_min_width = 250
        self.__ui_min_height = 150
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2

        # name the window
        self.setWindowTitle("AutoComp")
        # make the window a "tool" in Maya's eyes so that it stays on top when you click off
        self.setWindowFlags(QtCore.Qt.Tool)
        # Makes the object get deleted from memory, not just hidden, when it is closed.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Create the layout, linking it to actions and refresh the display
        self.__create_ui()
        self.__refresh_ui()

    # Create the ui
    def __create_ui(self):
        # Reinit attributes of the UI
        self.setMinimumSize(self.__ui_min_width, self.__ui_min_height)
        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

        browse_icon_path = os.path.dirname(__file__) + "/assets/browse.png"

        # Main Layout
        main_lyt = QVBoxLayout()
        main_lyt.setContentsMargins(8, 10, 8, 10)
        main_lyt.setSpacing(8)
        main_lyt.setAlignment(Qt.AlignTop)
        self.setLayout(main_lyt)

        shot_path_lyt = QVBoxLayout()
        shot_path_lyt.setAlignment(Qt.AlignCenter)
        main_lyt.addLayout(shot_path_lyt)

        lbl_shot_to_autocomp = QLabel("Shot to AutoComp")
        shot_path_lyt.addWidget(lbl_shot_to_autocomp)

        browse_shot_path_lyt = QHBoxLayout()
        shot_path_lyt.addLayout(browse_shot_path_lyt)

        self.__ui_shot_path = QLineEdit()
        self.__ui_shot_path.setPlaceholderText("Path of the shot to AutoComp")
        self.__ui_shot_path.textChanged.connect(self.__on_folder_changed)
        browse_shot_path_lyt.addWidget(self.__ui_shot_path)

        browse_btn = QPushButton()
        browse_btn.setIconSize(QtCore.QSize(18, 18))
        browse_btn.setFixedSize(QtCore.QSize(24, 24))
        browse_btn.setIcon(QIcon(QPixmap(browse_icon_path)))
        browse_btn.clicked.connect(partial(self.__browse_folder))
        browse_shot_path_lyt.addWidget(browse_btn)

        unpack_lyt = QVBoxLayout()
        unpack_lyt.setAlignment(Qt.AlignVCenter)
        main_lyt.addLayout(unpack_lyt)

        lbl_unpack_mode = QLabel("Unpack Mode")
        unpack_lyt.addWidget(lbl_unpack_mode)

        self.__ui_unpack_mode = QComboBox()
        self.__ui_unpack_mode.setStyleSheet("width:1000px")
        for unpack_mode in _UNPACk_MODES:
            self.__ui_unpack_mode.addItem(unpack_mode.get_name(), userData=unpack_mode)
        self.__ui_unpack_mode.currentIndexChanged.connect(self.__on_unpack_mode_changed)
        unpack_lyt.addWidget(self.__ui_unpack_mode)

        self.__ui_autocomp_btn = QPushButton("AutoComp")
        main_lyt.addWidget(self.__ui_autocomp_btn)

    # Refresh the ui according to the model attribute
    def __refresh_ui(self):
        self.__refresh_btn()
        self.__refresh_unpack_modes()

    def __refresh_btn(self):
        self.__ui_autocomp_btn.setEnabled(os.path.isdir(os.path.join(self.__shot_path, "render_out")))

    def __refresh_unpack_modes(self):
        for index in range(self.__ui_unpack_mode.count()):
            if self.__ui_unpack_mode.itemData(index, Qt.UserRole) == self.__unpack_mode:
                self.__ui_unpack_mode.setCurrentIndex(index)

    # Browse a new abc folder
    def __browse_folder(self):
        dirname = nuke.root()['name'].value()
        shot_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Shot Directory", dirname)
        self.__set_shot_path(shot_path)

    def __set_shot_path(self, shot_path):
        if os.path.isdir(os.path.join(shot_path, "render_out")) and shot_path != self.__shot_path:
            self.__ui_shot_path.setText(shot_path)

    # Retrieve the folder path on folder linedit change
    def __on_folder_changed(self):
        self.__shot_path = self.__ui_shot_path.text()
        self.__refresh_btn()

    def __on_unpack_mode_changed(self, index):
        self.__unpack_mode = self.__ui_unpack_mode.itemData(index, Qt.UserRole)
        print(self.__unpack_mode.get_shuffle_mode(),self.__unpack_mode.get_merge_mode())