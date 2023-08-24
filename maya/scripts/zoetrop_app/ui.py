import sys
import pymel.core as pm
from zoetrop_app import logic
import importlib
importlib.reload(logic)
from maya import OpenMayaUI as omui
from PySide2.QtCore import Qt, QStringListModel, QItemSelectionModel
from PySide2.QtGui import QIntValidator, QDoubleValidator
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout,QListWidget, QListWidgetItem, QAbstractItemView



class CustomUI(QWidget):
    def __init__(self, parent=None):
        super(CustomUI, self).__init__(parent)
        self.setWindowTitle("Sample UI")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setGeometry(100, 100,450, 180)

        # Initialize default values
        self.start_loop_val = 100
        self.end_loop_val = 124
        self.FPS_maya_val = 24
        self.FPS_loop_val = 12
        self.samples_val = 12


        # Set main layout
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()


        # Start Loop
        self.start_loop_input = QLineEdit(str(self.start_loop_val))
        self.start_loop_input.setValidator(QIntValidator())

        # End Loop
        self.end_loop_input = QLineEdit(str(self.end_loop_val))
        self.end_loop_input.setValidator(QIntValidator())

        #Start End layout:

        self.start_end_layout = QHBoxLayout()
        self.start_end_label = QLabel("Start/End")
        self.start_end_layout.addWidget(self.start_end_label)
        self.start_end_layout.addWidget(self.start_loop_input)
        self.start_end_layout.addWidget(self.end_loop_input)
        left_layout.addLayout(self.start_end_layout)
        # FPS Maya
        self.FPS_maya_label = QLabel("FPS Maya")
        self.FPS_maya_combobox = QComboBox()
        self.FPS_maya_combobox.addItems(['12', '24', '25'])
        self.FPS_maya_combobox.setCurrentText(str(self.FPS_maya_val))
        left_layout.addWidget(self.FPS_maya_label)
        left_layout.addWidget(self.FPS_maya_combobox)

        # FPS Loop
        self.FPS_loop_label = QLabel("FPS Loop")
        self.FPS_loop_combobox = QComboBox()
        self.FPS_loop_combobox.addItems(['12', '24', '25'])
        self.FPS_loop_combobox.setCurrentText(str(self.FPS_loop_val))
        left_layout.addWidget(self.FPS_loop_label)
        left_layout.addWidget(self.FPS_loop_combobox)

        # Samples
        self.samples_label = QLabel("Anim Samples")
        self.samples_input = QLineEdit(str(self.samples_val))
        self.samples_input.setValidator(QDoubleValidator())
        left_layout.addWidget(self.samples_label)
        left_layout.addWidget(self.samples_input)

        # Execute Button
        self.execute_button = QPushButton("Create Loop")
        self.execute_button.clicked.connect(self.run)
        #left_layout.addStretch(1)
        left_layout.addWidget(self.execute_button)


        self.hide_rig_button = QPushButton("Hide rig")
        self.hide_rig_button .clicked.connect(self.hide_rig)
        self.show_rig_button = QPushButton("Show rig")
        self.show_rig_button .clicked.connect(self.show_rig)
        self.rig_layout = QHBoxLayout()
        self.rig_layout.addWidget(self.hide_rig_button)
        self.rig_layout.addWidget(self.show_rig_button)

        # Update Button
        self.update_button = QPushButton("Update Loop")
        self.update_button.clicked.connect(self.update_loop)
        # Clear Button
        self.clear_button = QPushButton("Clear Loop")
        self.clear_button.clicked.connect(self.clear_loop)

        #left_frame = QFrame()
        #left_frame.setLayout(left_layout)


        self.loop_set_list_widget = QListWidget()  # Note: Changed the variable name for clarity
        self.loop_set_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)


        self.rigth_layout= QVBoxLayout()
        self.rigth_layout.addWidget(self.loop_set_list_widget)
        self.rigth_layout.addLayout(self.rig_layout)
        self.rigth_layout.addWidget(self.update_button)
        self.rigth_layout.addWidget(self.clear_button)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(self.rigth_layout, 3)

        self.setLayout(main_layout)

        # Connect
        self.start_loop_input.textChanged.connect(self.update_samples)
        self.end_loop_input.textChanged.connect(self.update_samples)
        self.FPS_loop_combobox.currentIndexChanged.connect(self.update_samples)
        self.FPS_maya_combobox.currentIndexChanged.connect(self.update_samples)
        self.zoetrop = logic.Zoetrop(self.get_loop_params())
        self.update_list_widget()


    def update_samples(self):
        data = self.get_loop_params()
        start_loop = data[0]
        end_loop = data[1]
        FPS_maya = data[2]
        FPS_loop = data[3]
        samples = FPS_loop * ((end_loop - start_loop)/ FPS_maya)
        if samples < 0:
            samples = 0
        else:
            samples = samples
        self.samples_input.setText(str(samples))

    def update_list_widget(self):
        # Store the names of currently selected items for later restoration
        selected_names_set = {item.text() for item in self.loop_set_list_widget.selectedItems()}

        # Clear and repopulate the list widget
        self.loop_set_list_widget.clear()
        for loop in self.zoetrop.loops:
            item = QListWidgetItem(loop.loop_set_name)
            item.setData(Qt.UserRole, loop)  # Store the Loop object with the item
            self.loop_set_list_widget.addItem(item)

        # Restore selections
        for index in range(self.loop_set_list_widget.count()):
            item = self.loop_set_list_widget.item(index)
            if item.text() in selected_names_set:
                item.setSelected(True)

    def get_loop_params(self):
        return [
            int(self.start_loop_input.text()),
            int(self.end_loop_input.text()),
            int(self.FPS_maya_combobox.currentText()),
            int(self.FPS_loop_combobox.currentText())
        ]

    def run(self):
        # Get the current selected object

        data= self.get_loop_params()
        self.zoetrop = logic.Zoetrop(data)
        self.zoetrop.create_loop_from_selection()
        self.update_list_widget()

    def hide_rig(self):
        # Get the current selected object
        items = [item for item in self.loop_set_list_widget.selectedItems()]
        for i in items:
            loop= i.data(Qt.UserRole)
            loop.rig_visibility(0)
    def show_rig(self):
        # Get the current selected object
        items = [item for item in self.loop_set_list_widget.selectedItems()]
        for i in items:
            loop= i.data(Qt.UserRole)
            loop.rig_visibility(1)

    def update_loop(self):
        items = [item for item in self.loop_set_list_widget.selectedItems()]
        data= self.get_loop_params()
        for i in items:
            loop= i.data(Qt.UserRole)
            loop.update_data(data)
            loop.create_loop()

    def clear_loop(self):
        items = [item for item in self.loop_set_list_widget.selectedItems()]
        for i in items:
            loop= i.data(Qt.UserRole)
            loop.delete_loop()
