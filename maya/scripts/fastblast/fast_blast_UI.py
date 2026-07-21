from PySide6 import QtWidgets, QtCore, QtGui  # type: ignore
from . import fast_blast

from importlib import reload

from shiboken6 import wrapInstance
import maya.OpenMayaUI as omui  # type: ignore

import maya.cmds as cmds

WINDOW_TITLE = "Illogic WIP Blast V1"

OPTION_VAR_NAMES = {
    "prev" : "ill_fastblast_prev_shot_count",
    "next" : "ill_fastblast_next_shot_count",
    "cam"  : "ill_fastblast_current_cam_checked",
    "vp"   : "ill_fastblast_current_vp_settings_checked",
    "audio": "ill_fastblast_force_audio_setting",
}   


class FastBlastUI(QtWidgets.QMainWindow):
    def __init__(self, parent=None):

        reload(fast_blast)

        super(FastBlastUI, self).__init__(parent)

        # self.setWindowFlags(QtGui.Qt.Window)

        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(50, 50, 250, 50)

        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        # Blast
        blast_layout = QtWidgets.QHBoxLayout()

        self.previous_shots_box = QtWidgets.QComboBox()
        self.next_shots_box = QtWidgets.QComboBox()

        self.previous_shots_box.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.next_shots_box.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.previous_shots_box.customContextMenuRequested.connect(
            self.show_shot_menu_left
        )
        self.next_shots_box.customContextMenuRequested.connect(
            self.show_shot_menu_right
        )

        self.stylesheet = (
            "QComboBox { min-width: 40px; }"
            "QComboBox QAbstractItemView::item { min-width: 0px; }"
            "QPushButton {background-color: green}"
        )

        self.blast_button = QtWidgets.QPushButton("Blast")
        self.blast_button.clicked.connect(self.launch_playblast)

        previous_shots_values = ["-" + str(i) for i in range(6)]
        next_shots_values = ["+" + str(i) for i in range(6)]

        # Load option var
        self.prev_shots_ov = f"-{self.get_optionvar(OPTION_VAR_NAMES['prev'], int_value=1)}"
        self.next_shots_ov = f"+{self.get_optionvar(OPTION_VAR_NAMES['next'], int_value=1)}"

        if self.prev_shots_ov not in previous_shots_values:
            previous_shots_values.append(self.prev_shots_ov)

        if self.next_shots_ov not in next_shots_values:
            next_shots_values.append(self.next_shots_ov)

        self.previous_shots_box.addItems(previous_shots_values)
        self.next_shots_box.addItems(next_shots_values)

        self.previous_shots_box.setCurrentText(self.prev_shots_ov)
        self.next_shots_box.setCurrentText(self.next_shots_ov)

        self.previous_shots_box.currentTextChanged.connect(
            lambda text: self.set_optionvar(
                OPTION_VAR_NAMES['prev'], int_value=int(text.lstrip("-"))
            )
        )
        self.next_shots_box.currentTextChanged.connect(
            lambda text: self.set_optionvar(
                OPTION_VAR_NAMES['next'], int_value=int(text.lstrip("+"))
            )
        )

        # Options

        options_layout = QtWidgets.QHBoxLayout()
        self.current_cam_box = QtWidgets.QCheckBox("Cur Cam")
        self.current_viewport_settings_box = QtWidgets.QCheckBox("Cur VP Settings")

        is_cam_checked = self.get_optionvar(OPTION_VAR_NAMES['cam'], int_value=0)
        is_vp_checked = self.get_optionvar(OPTION_VAR_NAMES['vp'], int_value=0)

        self.current_cam_box.setChecked(is_cam_checked)
        self.current_viewport_settings_box.setChecked(is_vp_checked)

        self.current_cam_box.stateChanged.connect(
            lambda state: self.set_optionvar(OPTION_VAR_NAMES['cam'], int_value=state)
        )

        self.current_viewport_settings_box.stateChanged.connect(
            lambda state: self.set_optionvar(OPTION_VAR_NAMES['vp'], int_value=state)
        )

        self.default_audio_settings = ["Auto", "Off", "Trax"]
        self.createMenu()

        main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        main_widget.customContextMenuRequested.connect(self.show_menu)

        blast_layout.addWidget(self.previous_shots_box)
        blast_layout.addWidget(self.blast_button)
        blast_layout.addWidget(self.next_shots_box)

        blast_layout.setStretch(0, 1)
        blast_layout.setStretch(1, 5)
        blast_layout.setStretch(2, 1)

        options_layout.addWidget(self.current_cam_box)
        options_layout.addWidget(self.current_viewport_settings_box)

        layout.setSpacing(2)
        layout.addLayout(blast_layout)
        layout.addLayout(options_layout)

        self.setStyleSheet(self.stylesheet)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Initialize blast class
        self.blast = fast_blast.FastBlast(self)

    def get_optionvar(self, var="tmpVar", int_value=None, list_value=None, str_value=None):
        # var optionVar
        saved = cmds.optionVar(q=var)
        if not saved:
            self.set_optionvar(var, int_value, list_value, str_value)
        return saved

    def set_optionvar(
        self, var="tmpVar", int_value=None, list_value=None, str_value=None
    ):
        if int_value is not None:
            cmds.optionVar(intValue=(var, int_value))
        elif list_value is not None:
            cmds.optionVar(intArray=(var, list_value))
        elif str_value is not None:
            cmds.optionVar(stringValue=(var, str_value))

    def show_shot_menu_left(self, pos):
        self.show_shot_menu(pos, self.previous_shots_box)

    def show_shot_menu_right(self, pos):
        self.show_shot_menu(pos, self.next_shots_box)

    def show_shot_menu(self, pos, item):
        menu = QtWidgets.QMenu()
        custom_val_action = menu.addAction("Custom Value")
        action = menu.exec_(item.mapToGlobal(pos))
        if action == custom_val_action:
            self.set_custom_val(item)

    def set_custom_val(self, item: QtWidgets.QComboBox):
        item.setEditable(True)
        item.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.InsertAtBottom)

        # Only allow integers
        validator = QtGui.QIntValidator()
        item.lineEdit().setValidator(validator)

        # Confirm input and disable editing
        item.lineEdit().editingFinished.connect(lambda: item.setEditable(False))

    def createMenu(self):
        self.menu = QtWidgets.QMenu()
        self.refresh_action = self.menu.addAction("Refresh shot order")

        self.menu.addSeparator().setText(("Audio"))
        audio_list = self.get_audio_options()
        self.audio_settings_radio = self.create_audiosettings_radio(
            self.menu, audio_list
        )

    def show_menu(self, pos):
        action = self.menu.exec_(self.mapToGlobal(pos))
        if action == self.refresh_action:
            self.blast = fast_blast.FastBlast(self)

    def get_audio_options(self):
        options = self.default_audio_settings
        audios = cmds.ls(type="audio")
        options.extend(audios)
        return options

    def create_audiosettings_radio(self, menu, audio_list):

        self.audio_action_grp = QtGui.QActionGroup(menu)
        self.audio_action_grp.setExclusive(True)
        self.audio_action_grp.setEnabled(True)

        for audio in audio_list:
            audio_action = QtGui.QAction(audio)
            audio_action.setCheckable(True)
            audio_action.toggled.connect(self.save_selected_audio)
            menu.addAction(audio_action)
            self.audio_action_grp.addAction(audio_action)

        saved_audio_file = self.get_optionvar(OPTION_VAR_NAMES["audio"], str_value="Auto")
        try:
            action_group_text = [x.text() for x in self.audio_action_grp.actions()]
            print(f"actions: {action_group_text}, audio file: {saved_audio_file}")
            checked_audio_index = action_group_text.index(saved_audio_file)
            print(f"Index: {checked_audio_index}")
        except Exception:
            checked_audio_index = 0
            print(f"wraps: {checked_audio_index}")
        
        print(f"Final: {checked_audio_index}")
        self.audio_action_grp.actions()[checked_audio_index].setChecked(True)

        return self.audio_action_grp
    
    def save_selected_audio(self, checked):
        for action in self.audio_action_grp.actions():
           if action.isChecked():
            self.set_optionvar(OPTION_VAR_NAMES["audio"], str_value=action.text()) 

    def launch_playblast(self, event):

        previous_count = int(self.previous_shots_box.currentText())
        next_count = int(self.next_shots_box.currentText())

        keep_cam = self.current_cam_box.isChecked()
        keep_vp_settings = self.current_viewport_settings_box.isChecked()

        audio_setting = self.audio_settings_radio.checkedAction().text()

        self.blast.run(
            prev=previous_count,
            next=next_count,
            keep_cam=keep_cam,
            keep_vp_settings=keep_vp_settings,
            audio_setting=audio_setting,
        )

    def touch_warning(self):
        warning_dialogue = QtWidgets.QDialog(self)
        warning_dialogue.setWindowTitle("Warning")

        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(
            "Warning, blast file still open\n Please close last open blast"
        )
        button = QtWidgets.QPushButton("OK")
        button.clicked.connect(warning_dialogue.accept)

        layout.addWidget(label)
        layout.addWidget(button)
        warning_dialogue.setLayout(layout)
        warning_dialogue.exec()


def get_main_window():
    """Get the maya window pointer to parent this tool under."""

    ptr = omui.MQtUtil.mainWindow()
    maya_window = wrapInstance(int(ptr), QtWidgets.QWidget)
    return maya_window


def run_ui():

    tops = QtWidgets.QApplication.topLevelWidgets()
    for top in tops:
        if top.windowTitle() == WINDOW_TITLE:
            top.close()

    app = get_main_window()
    widget = FastBlastUI(app)
    widget.show()
