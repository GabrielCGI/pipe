import sys

from . import logic

import pymel.core as pm
from maya import OpenMayaUI as omui
from PySide2.QtCore import Qt, QStringListModel, QItemSelectionModel, QPoint
from PySide2.QtGui import QIntValidator, QDoubleValidator, QCloseEvent
from PySide2.QtWidgets import QWidget, QDesktopWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout,QListWidget, QListWidgetItem, QAbstractItemView

from common.utils import *
from common.Prefs import *

# ######################################################################################################################

_FILE_NAME_PREFS = "zoetrop"

# ######################################################################################################################


class CustomUI(QWidget):
    def __init__(self, parent=None):
        super(CustomUI, self).__init__(parent)

        # Common Preferences (common preferences on all tools)
        self.__common_prefs = Prefs()
        # Preferences for this tool
        self.__prefs = Prefs(_FILE_NAME_PREFS)

        self.__ui_updating = False

        self.setWindowTitle("Sample UI")
        self.__ui_width = 450
        self.__ui_height = 180
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2
        self.setWindowFlags(Qt.Tool)


        # Initialize default values
        self.start_loop_val = 100
        self.end_loop_val =  136
        self.FPS_maya_val =  24
        self.FPS_loop_val =  12
        self.motion_val = 0
        self.samples_val = 12

        self.retrieve_prefs()
        self.compute_samples()

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

        self.motion_label = QLabel("Motion direction")
        self.motion_combobox = QComboBox()
        self.motion_combobox.addItems(["0", '1', '-1'])
        self.motion_combobox.setCurrentText(str(self.motion_val))

        left_layout.addWidget(self.motion_label)
        left_layout.addWidget(self.motion_combobox)

        # Samples
        self.samples_label = QLabel("Anim Samples")
        self.samples_input = QLineEdit(str(self.samples_val))
        self.samples_input.setReadOnly(True)
        self.samples_input.setValidator(QDoubleValidator())
        left_layout.addWidget(self.samples_label)
        left_layout.addWidget(self.samples_input)

        # Execute Button
        self.get_button_layout = QHBoxLayout()
        self.get_button = QPushButton("Get")
        self.get_button.clicked.connect(self.get_clicked)

        self.get_button_layout.addWidget(self.get_button)

        self.to_key_button = QPushButton("to key")
        self.to_key_button.clicked.connect(self.to_key_clicked)
        self.get_button_layout.addWidget(self.to_key_button)


        self.automation_button = QPushButton("123")
        self.automation_button.clicked.connect(self.automation_clicked)
        self.get_button_layout.addWidget(self.automation_button)
        self.get_button_layout.addStretch(1)

        left_layout.addLayout(self.get_button_layout)

        # Execute Button
        self.setup_hierarchy_button = QPushButton("Setup Hierarchy")
        self.setup_hierarchy_button.clicked.connect(self.setup_hierarchy)
        left_layout.addWidget(self.setup_hierarchy_button)



        # Execute Button
        self.execute_button = QPushButton("Create Loop")
        self.execute_button.clicked.connect(self.run)
        left_layout.addWidget(self.execute_button)
        left_layout.addStretch(1)

        #Clean expression
        self.freeze_button = QPushButton("Freeze all loops (f100)")
        self.freeze_button.clicked.connect(self.freeze_clicked)
        left_layout.addWidget(self.freeze_button)


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
        self.loop_set_list_widget.itemSelectionChanged.connect(self.list_widget_selection_changed)

        self.rigth_layout= QVBoxLayout()
        self.rigth_layout.addWidget(self.loop_set_list_widget)
        self.rigth_layout.addLayout(self.rig_layout)
        self.rigth_layout.addWidget(self.update_button)
        self.rigth_layout.addWidget(self.clear_button)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(self.rigth_layout, 3)

        self.setLayout(main_layout)

        # Connect
        self.start_loop_input.textChanged.connect(self.update_params)
        self.end_loop_input.textChanged.connect(self.update_params)
        self.FPS_loop_combobox.currentIndexChanged.connect(self.update_params)
        self.FPS_maya_combobox.currentIndexChanged.connect(self.update_params)
        self.motion_combobox.currentIndexChanged.connect(self.update_params)
        self.zoetrop = logic.Zoetrop(self.get_loop_params())
        self.update_list_widget()

        self.resize(self.__ui_width, self.__ui_height)
        self.move(self.__ui_pos)

    # Save preferences
    def save_prefs(self):
        size = self.size()
        self.__prefs["window_size"] = {"width": size.width(), "height": size.height()}
        pos = self.pos()
        self.__prefs["window_pos"] = {"x": pos.x(), "y": pos.y()}

        self.__prefs["start_loop_val"] = self.start_loop_val
        self.__prefs["end_loop_val"] = self.end_loop_val
        self.__prefs["FPS_maya_val"] = self.FPS_maya_val
        self.__prefs["FPS_loop_val"] = self.FPS_loop_val
        self.__prefs["motion_val"] = self.motion_val

    # Remove callbacks
    def hideEvent(self, arg__1: QCloseEvent) -> None:
        self.save_prefs()


    def retrieve_prefs(self):
        """
        Retrieve preferences
        :return:
        """
        if "window_pos" in self.__prefs:
            pos = self.__prefs["window_pos"]
            self.__ui_pos = QPoint(pos["x"], pos["y"])

        if "start_loop_val" in self.__prefs:
            self.start_loop_val = self.__prefs["start_loop_val"]

        if "end_loop_val" in self.__prefs:
            self.end_loop_val = self.__prefs["end_loop_val"]

        if "FPS_maya_val" in self.__prefs:
            self.FPS_maya_val = self.__prefs["FPS_maya_val"]

        if "FPS_loop_val" in self.__prefs:
            self.FPS_loop_val = self.__prefs["FPS_loop_val"]

        if "motion_val" in self.__prefs:
            self.motion_val = self.__prefs["motion_val"]

    def freeze_clicked(self):


        # Set the current frame to 100
        pm.currentTime(100)

        for transform in pm.ls('LOOP*', type='transform'):
            if transform.ry.isConnected():
                transform.ry.disconnect()
    def to_key_clicked(self):
        selection = pm.selected()
        if not selection:
            pm.warning("Nothing selected.")
            return
        loop_param = self.get_loop_params()
        self.zoetrop.set_key(selection[0],loop_param)

    def automation_clicked(self):
        selection = pm.selected()
        for s in selection:
            try:
                pm.select(s)
                self.get_clicked()
                self.setup_hierarchy()
                self.run()
            except Exception as e:
                print("Faile"+s.name())
                print(e)


    def get_clicked(self):
        selection = pm.selected()
        if not selection:
            pm.warning("Nothing selected.")
            return

        loop_attributes= self.zoetrop.read_loop_attributs_from_standIn(selection[0])
        if not loop_attributes:
            pm.warning("Fail to read alembic attribut on: "+selection)
            return
        print (loop_attributes)

        # Update the Start Loop input field
        start_loop_val = loop_attributes.get('data_start_loop')
        if start_loop_val is not None:
            self.start_loop_val = int(start_loop_val)
            self.start_loop_input.setText(str(self.start_loop_val))

        # Update the End Loop input field
        end_loop_val = loop_attributes.get('data_end_loop')
        if end_loop_val is not None:
            self.end_loop_val = int(end_loop_val)
            self.end_loop_input.setText(str(self.end_loop_val))

        # Update the FPS Maya combobox
        FPS_maya_val = loop_attributes.get('data_FPS_maya')
        if FPS_maya_val is not None:
            self.FPS_maya_val = int(FPS_maya_val)
            self.FPS_maya_combobox.setCurrentText(str(self.FPS_maya_val))

        # Update the FPS Loop combobox
        FPS_loop_val = loop_attributes.get('data_FPS_loop')
        if FPS_loop_val is not None:
            self.FPS_loop_val = int(FPS_loop_val)
            self.FPS_loop_combobox.setCurrentText(str(self.FPS_loop_val))

        motion_loop_val = loop_attributes.get('data_motion')
        if motion_loop_val is not None:
            self.motion_val = int(motion_loop_val)
            self.motion_combobox.setCurrentText(str(self.motion_val))

        pm.select(selection)
    def retrieve_loop_params(self):
        """
        Retrieve the parameters from inpute fields and combobox (only if the UI isn't updating)
        """
        if self.__ui_updating: return
        start_loop= self.start_loop_input.text()
        self.start_loop_val = int(start_loop) if len(start_loop)>0 else 0
        end_loop= self.end_loop_input.text()
        self.end_loop_val = int(end_loop) if len(end_loop)>0 else 0
        self.FPS_maya_val = int(self.FPS_maya_combobox.currentText())
        self.FPS_loop_val = int(self.FPS_loop_combobox.currentText())
        self.motion_val = int(self.motion_combobox.currentText())

    def update_params(self):
        """
        Retrieve the parameters from input fields and combobox, compute the samples then update in the UI
        """
        self.retrieve_loop_params()
        self.compute_samples()
        self.update_ui_params()

    def update_ui_params(self):
        """
        Update the param field UI according to model attribute
        """
        self.__ui_updating = True
        self.start_loop_input.setText(str(self.start_loop_val))
        self.end_loop_input.setText(str(self.end_loop_val))
        self.FPS_maya_combobox.setCurrentText(str(self.FPS_maya_val))
        self.FPS_loop_combobox.setCurrentText(str(self.FPS_loop_val))
        self.motion_combobox.setCurrentText(str(self.motion_val))
        self.samples_input.setText(str(self.samples_val))
        self.__ui_updating = False

    def compute_samples(self):
        """
        Compute the samples thanks the other param
        """
        samples = self.FPS_loop_val * ((self.end_loop_val - self.start_loop_val)/ self.FPS_maya_val)
        if samples < 0:
            self.samples_val = 0
        else:
            self.samples_val = samples

    @staticmethod
    def pretty_display(name, existing_names=None):
        element_name = name.split('NS')[-1]

        if existing_names is None:
            existing_names = set()

        base_name = element_name
        increment = 1

        while element_name in existing_names:
            element_name = f"{base_name}_{increment}"
            increment += 1

        return element_name

    def list_widget_selection_changed(self):
        items = [item for item in self.loop_set_list_widget.selectedItems()]
        geo_list = [geo.data(Qt.UserRole).geo for geo in items]

        # Fetching loop_group_name from each QListWidgetItem
        for geo in items:
            loop_group_name = geo.data(Qt.UserRole).loop_group_name
            if loop_group_name and pm.objExists(loop_group_name):
                geo_list.append(pm.PyNode(loop_group_name))

        if len(geo_list)>0:
            pm.select(geo_list)
            geo_with_attr = geo_list[0]
            # ['data_start_loop', 'data_end_loop', 'data_FPS_maya', 'data_FPS_loop', 'data_motion']
            self.start_loop_val = int(geo_with_attr.getAttr("data_start_loop"))
            self.end_loop_val = int(geo_with_attr.getAttr("data_end_loop"))
            self.FPS_maya_val = int(geo_with_attr.getAttr("data_FPS_maya"))
            self.FPS_loop_val = int(geo_with_attr.getAttr("data_FPS_loop"))
            self.motion_val = int(geo_with_attr.getAttr("data_motion"))
            self.compute_samples()
            self.update_ui_params()


    def update_list_widget(self):
        # Store the names of currently selected items for later restoration
        selected_names_set = {item.text() for item in self.loop_set_list_widget.selectedItems()}

        # Clear and repopulate the list widget
        self.loop_set_list_widget.clear()
        existing_names = set()
        for loop in self.zoetrop.loops:
            print (loop.loop_set_name)
            pretty_name = self.pretty_display(loop.loop_set_name, existing_names)
            loop.pretty_name = pretty_name
            existing_names.add(pretty_name)
            item = QListWidgetItem(pretty_name)
            item.setData(Qt.UserRole, loop)  # Store the Loop object with the item
            self.loop_set_list_widget.addItem(item)

        # Restore selections
        for index in range(self.loop_set_list_widget.count()):
            item = self.loop_set_list_widget.item(index)
            if item.text() in selected_names_set:
                item.setSelected(True)


    def get_loop_params(self):
        self.retrieve_loop_params()
        return [
            self.start_loop_val,
            self.end_loop_val,
            self.FPS_maya_val,
            self.FPS_loop_val,
            self.motion_val
            ]

    def setup_hierarchy(self):
        selection = pm.ls(sl = True)
        for sl in selection:
            pm.group(sl, name=sl.name()+'_grp')
        pm.select(selection)


    def run(self):
        # Get the current selected object

        data=self.get_loop_params()
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
        new_data= self.get_loop_params()
        for i in items:
            loop= i.data(Qt.UserRole)
            loop.check_data_difference(new_data)
            #loop.update_data(data)
            loop.create_loop()

    def clear_loop(self):
        items = [item for item in self.loop_set_list_widget.selectedItems()]
        for i in items:
            loop= i.data(Qt.UserRole)
            loop.delete_loop()
