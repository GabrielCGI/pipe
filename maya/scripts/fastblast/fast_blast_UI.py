from PySide6 import QtWidgets, QtCore, QtGui# type: ignore
from . import fast_blast

from importlib import reload

from shiboken6 import wrapInstance
import maya.OpenMayaUI as omui # type: ignore

WINDOW_TITLE = "Illogic WIP Blast V1"

class FastBlastUI(QtWidgets.QMainWindow):

    def __init__(self, parent=None):

        reload(fast_blast)

        super(FastBlastUI,self).__init__(parent)

        # self.setWindowFlags(QtGui.Qt.Window)

        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(50,50,250,50)

        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
    
        # Blast
        blast_layout = QtWidgets.QHBoxLayout()

        self.previous_shots_box = QtWidgets.QComboBox()
        self.next_shots_box = QtWidgets.QComboBox()
        
        self.previous_shots_box.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.next_shots_box.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.previous_shots_box.customContextMenuRequested.connect(self.show_shot_menu_left)
        self.next_shots_box.customContextMenuRequested.connect(self.show_shot_menu_right)

        self.stylesheet = "QComboBox { min-width: 40px; }" \
                     "QComboBox QAbstractItemView::item { min-width: 0px; }" \
                     "QPushButton {background-color: green}"

        self.blast_button = QtWidgets.QPushButton("Blast")
        self.blast_button.clicked.connect(self.launch_playblast)

        previous_shots_values = ["-" + str(i) for i in range(6)]
        next_shots_values = ["+" + str(i) for i in range(6)]
        self.previous_shots_box.addItems(previous_shots_values)
        self.next_shots_box.addItems(next_shots_values)

        self.previous_shots_box.setCurrentText("-1")
        self.next_shots_box.setCurrentText("+1")

        # Options 
        options_layout = QtWidgets.QHBoxLayout()
        self.current_cam_box = QtWidgets.QCheckBox("Cur Cam")
        self.current_viewport_settings_box = QtWidgets.QCheckBox("Cur VP Settings")

        main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        main_widget.customContextMenuRequested.connect(self.show_menu)

        blast_layout.addWidget(self.previous_shots_box)
        blast_layout.addWidget(self.blast_button)
        blast_layout.addWidget(self.next_shots_box)

        blast_layout.setStretch(0,1)
        blast_layout.setStretch(1,5)
        blast_layout.setStretch(2,1)

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

    def show_shot_menu_left(self,pos):
        self.show_shot_menu(pos, self.previous_shots_box)
    def show_shot_menu_right(self,pos):
        self.show_shot_menu(pos,self.next_shots_box)
    
    def show_shot_menu(self,pos,item):
        menu = QtWidgets.QMenu()
        custom_val_action = menu.addAction("Custom Value")
        action = menu.exec_(item.mapToGlobal(pos))
        if action == custom_val_action:
            self.set_custom_val(item)

    def set_custom_val(self, item : QtWidgets.QComboBox):
        item.setEditable(True)
        item.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.InsertAtBottom)
        
        # Only allow integers
        validator = QtGui.QIntValidator()
        item.lineEdit().setValidator(validator)
        
        # Confirm input and disable editing
        item.lineEdit().editingFinished.connect(lambda: item.setEditable(False))

    def show_menu(self,pos):
        menu = QtWidgets.QMenu()
        refresh_action = menu.addAction("Refresh shot order")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == refresh_action:
            self.blast = fast_blast.FastBlast(self)

    def launch_playblast(self, event):
        
        previous_count = int(self.previous_shots_box.currentText())
        next_count = int(self.next_shots_box.currentText())

        keep_cam = self.current_cam_box.isChecked()
        keep_vp_settings = self.current_viewport_settings_box.isChecked()

        self.blast.run(prev=previous_count, 
                  next=next_count, 
                  keep_cam=keep_cam, 
                  keep_vp_settings=keep_vp_settings
                  )

    def touch_warning(self):
        warning_dialogue = QtWidgets.QDialog(self)
        warning_dialogue.setWindowTitle("Warning")
        
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("Warning, blast file still open\n Please close last open blast")
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