import sys
import pymel.core as pm
from maya import OpenMayaUI as omui
from PySide2.QtCore import Qt, QStringListModel, QItemSelectionModel
from PySide2.QtGui import QIntValidator, QDoubleValidator
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QListView, QAbstractItemView,QFrame


class LoopParameters:
    def __init__(self, start_loop, end_loop, FPS_maya, FPS_loop):
        self.start_loop = start_loop
        self.end_loop = end_loop
        self.FPS_maya = FPS_maya
        self.FPS_loop = FPS_loop

    @property
    def modulo(self):
        return self.FPS_maya / self.FPS_loop

    @property
    def duration(self):
        return self.end_loop - self.start_loop

    @property
    def samples(self):
        return self.FPS_loop * (self.duration / self.FPS_maya)

    @property
    def angle(self):
        return 360 / self.samples


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

        # Update Button
        self.update_button = QPushButton("Update Loop")
        self.update_button.clicked.connect(self.update_loop)
        # Clear Button
        self.clear_button = QPushButton("Clear Loop")
        self.clear_button.clicked.connect(self.clear_loop)

        #left_frame = QFrame()
        #left_frame.setLayout(left_layout)


        self.loop_set_list_view = QListView()
        list_model = QStringListModel()
        self.loop_set_list_view.setModel(list_model)
        self.loop_set_list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.rigth_layout= QVBoxLayout()
        self.rigth_layout.addWidget(self.loop_set_list_view)
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

        self.update_list_view()
    def update_samples(self):
        loop = self.get_loop_params()
        if loop.samples < 0:
            samples = 0
        else:
            samples = loop.samples
        self.samples_input.setText(str(samples))

    def update_list_view(self):
        #Store selection
        selected_items = [index.data() for index in self.loop_set_list_view.selectionModel().selectedIndexes()]

        #Rebuild
        loop_set_names = [set_obj.name() for set_obj in pm.ls(type='objectSet') if set_obj.name().startswith('LP')]
        list_model = QStringListModel(loop_set_names)
        self.loop_set_list_view.setModel(list_model)

        #Restore selection
        for row in range(list_model.rowCount()):
            item_data = list_model.data(list_model.index(row, 0))
            if item_data in selected_items:
                self.loop_set_list_view.selectionModel().select(list_model.index(row, 0), QItemSelectionModel.Select)
    def get_loop_params(self):
        return LoopParameters(
            int(self.start_loop_input.text()),
            int(self.end_loop_input.text()),
            int(self.FPS_maya_combobox.currentText()),
            int(self.FPS_loop_combobox.currentText())
        )

    def run(self):
        current_frame = pm.currentTime(query=True)

        # Get the current selected object
        selected = pm.selected()
        if not selected:
            pm.warning("Please select a geometry to duplicate.")
            return

        # Check if all selected objects have a parent
        for obj in selected:
            if not obj.getParent():
                pm.warning(f"{obj} does not have a parent. Aborting.")
                return


        try:
            pm.undoInfo(state=False)
            for obj in selected:
                self.duplicate_on_even_frames(obj)
                self.update_list_view()
            pm.currentTime(current_frame, edit=True)
            pm.select(clear=True)
        except Exception as e:
            print("Exception occurred:", e)
            pm.warning("Something went wrong")
        finally:
            pm.undoInfo(state=True)

    def duplicate_on_even_frames(self, obj):
        loop = self.get_loop_params()

        group = self.create_or_replace_group(obj)
        self.apply_rotation_expression(group, loop)

        self.print_duplication_start_info(loop)
        self.duplicate_for_frames(obj, group, loop)
        self.create_set_figurine(obj)
        self.setup_visibility(obj, loop)

        print("------ End ------")

    def get_selected_set_names(self):
        """Helper function to retrieve selected set names from the view."""
        selection_model = self.loop_set_list_view.selectionModel()
        selected_indexes = selection_model.selectedIndexes()
        if not selected_indexes:
            pm.warning("Nothing selected to update.")
            return []

        # Extract the names of the sets from the selection
        return [index.data() for index in selected_indexes]

    def get_objects_to_select(self, set_names):
        """Helper function to retrieve objects from the provided set names."""
        objects_to_select = []

        for set_name in set_names:
            if not pm.objExists(set_name):
                pm.warning("Set does not exist")
                self.update_list_view()
                return []

            set_node = pm.PyNode(set_name)
            members = pm.sets(set_node, query=True)

            # Add the first member to our list if it exists
            if members:
                objects_to_select.append(members[0])
            else:
                print(f"The set {set_name} is empty.")

        return objects_to_select

    def update_loop(self):
        selected_sets_names = self.get_selected_set_names()
        if not selected_sets_names:
            return

        objects_to_select = self.get_objects_to_select(selected_sets_names)
        pm.select(objects_to_select)
        self.run()

    def clear_loop(self):
        selected_sets_names = self.get_selected_set_names()
        if not selected_sets_names:
            return

        objects_to_select = self.get_objects_to_select(selected_sets_names)

        for obj in objects_to_select:
            parent = obj.getParent()
            if parent:
                parent_name = parent.replace(':', "NS")
                group_name = f"LOOP_{parent_name}"
                try:
                    pm.delete(group_name)
                except:
                    pm.warning(f"Fail to delete {group_name}")

    def create_or_replace_group(self, obj):
        """Creates a new group or replaces if it exists."""
        parent_name = obj.getParent().replace(':',"NS")
        group_name = f"LOOP_{parent_name}"

        if pm.objExists(group_name):
            pm.delete(group_name)

        return pm.group(em=True, name=group_name)

    def apply_rotation_expression(self, group, loop):
        """Applies rotation expression to the given group."""
        rotation_expression = f"{group.name()}.rotateY = floor(frame / {loop.modulo}) * {loop.angle};"
        pm.expression(s=rotation_expression)

    def print_duplication_start_info(self, loop):
        """Prints the starting information of the duplication process."""
        print("------ Begins ------")
        print(f"Generating {loop.samples} samples")
        print(f"Speed Angle: {loop.angle}\n")

    def duplicate_for_frames(self, obj, group, loop):
        """Duplicates the given object for specified frames and groups them."""
        for frame in range(loop.start_loop, loop.end_loop):
            if frame % loop.modulo == 0:
                pm.currentTime(frame)
                duplicated = pm.duplicate(obj)
                renamed_duplicated = pm.rename(duplicated[0], f"sample_{frame}")
                subGroup = pm.group(em=True, name=f"rotor_{renamed_duplicated.name()}")

                pm.parent(subGroup, group)
                pm.parent(renamed_duplicated, subGroup)
                self.setup_visibility_sample(subGroup,frame,loop.modulo)
                print(f"Succes on time: {frame}")

    def force_visibility_all_children(self, obj):
        # Set the visibility of the main object

        # Get the children of the object and set their visibility
        children = obj.getChildren()  # This will fetch all children including nested ones.
        for child in children:
            print(child)
            if child.hasAttr('visibility'):
                child.visibility.set(1)


    def setup_visibility_sample(self,sample,start_range, loop_modulo):

        #Force restore visibility to 1
        print(sample)
        self.force_visibility_all_children(sample)
        expression_name = f"{sample.name()}_visExpression"
        end_range = start_range + loop_modulo - 1
        expression_str = f"""
        if (frame >= {start_range} && frame <= {end_range})
            {sample.nodeName()}.visibility = 0;
        else
            {sample.nodeName()}.visibility  = 1;
        """

        if pm.objExists(expression_name):
            pm.expression(expression_name, edit=True, s=expression_str)
        else:
            pm.expression(name=expression_name, s=expression_str)


    def create_set_figurine(self, obj):
        parent_obj = obj.getParent()
        object_set_name = "LP_"+parent_obj.name().replace(":","_")

        if pm.objExists(object_set_name):
            pm.delete(object_set_name)
        obj_set = pm.sets(name=object_set_name, empty=True)
        obj_set.addMember(obj)

    def setup_visibility(self, obj, loop):
        """Configures visibility settings for the given object."""

        target = obj.getParent().visibility

        expression_name = f"{target}_visExpression".replace(".","_")
        expression_str = f"""

        if (frame >= {loop.end_loop})
            {target} = 0;
        else
            {target} = 1;
        """

        if pm.objExists(expression_name):
            pm.expression(expression_name, edit=True, s=expression_str)
        else:
            if target.isDestination():
                source_attr = target.getInput(p=True)
                if source_attr:
                    print("disconet")
                    pm.disconnectAttr(source_attr, target)
            pm.expression(name=expression_name, s=expression_str)
        print (f"Visibility set on {target}")



if __name__ == "__main__":
    custom_ui = CustomUI()
    custom_ui.show()
