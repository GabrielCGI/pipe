import sys
import pymel.core as pm
from maya import OpenMayaUI as omui
from PySide2.QtCore import Qt
from PySide2.QtGui import QIntValidator, QDoubleValidator
from PySide2.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout

class CustomUI(QWidget):
    def __init__(self, parent=None):
        super(CustomUI, self).__init__(parent)
        self.setWindowTitle("Sample UI")
        self.setWindowFlags(Qt.Window)

        self.setGeometry(100, 100, 250, 200)

        # Initialize default values
        self.start_loop_val = 100
        self.end_loop_val = 124
        self.FPS_maya_val = 24
        self.FPS_loop_val = 12
        self.samples_val = 12

        # Set main layout
        layout = QVBoxLayout()

        # Create loop QHBoxLayout
        loop_layout = QHBoxLayout()

        # Start Loop
        self.start_loop_label = QLabel("Start Loop")
        self.start_loop_input = QLineEdit(str(self.start_loop_val))
        self.start_loop_input.setValidator(QIntValidator())
        loop_layout.addWidget(self.start_loop_label)
        loop_layout.addWidget(self.start_loop_input)

        # End Loop
        self.end_loop_label = QLabel("End Loop")
        self.end_loop_input = QLineEdit(str(self.end_loop_val))
        self.end_loop_input.setValidator(QIntValidator())
        loop_layout.addWidget(self.end_loop_label)
        loop_layout.addWidget(self.end_loop_input)

        layout.addLayout(loop_layout)

        # Create FPS QHBoxLayout
        fps_layout = QHBoxLayout()

        # FPS Maya
        self.FPS_maya_label = QLabel("FPS Maya")
        self.FPS_maya_combobox = QComboBox()
        self.FPS_maya_combobox.addItems(['12', '24', '25'])
        self.FPS_maya_combobox.setCurrentText(str(self.FPS_maya_val))
        fps_layout.addWidget(self.FPS_maya_label)
        fps_layout.addWidget(self.FPS_maya_combobox)

        # FPS Loop
        self.FPS_loop_label = QLabel("FPS Loop")
        self.FPS_loop_combobox = QComboBox()
        self.FPS_loop_combobox.addItems(['12', '24', '25'])
        self.FPS_loop_combobox.setCurrentText(str(self.FPS_loop_val))
        fps_layout.addWidget(self.FPS_loop_label)
        fps_layout.addWidget(self.FPS_loop_combobox)

        layout.addLayout(fps_layout)

        samples_layout= QHBoxLayout()
        # Samples
        self.samples_label = QLabel("Anim Samples")
        self.samples_input = QLineEdit(str(self.samples_val))
        self.samples_input.setValidator(QDoubleValidator())
        samples_layout.addWidget(self.samples_label)
        samples_layout.addWidget(self.samples_input)
        layout.addLayout(samples_layout)


        #connect
        self.start_loop_input.textChanged.connect(self.update_samples)
        self.end_loop_input.textChanged.connect(self.update_samples)
        self.FPS_loop_combobox.currentIndexChanged.connect(self.update_samples)
        self.FPS_maya_combobox.currentIndexChanged.connect(self.update_samples)
        # Execute Button
        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self.run)
        layout.addWidget(self.execute_button)

        self.setLayout(layout)

    def update_samples(self):
        modulo, duration, samples, angle  = self.calculate_data()
        print(samples)
        if samples < 0:
            samples=0
        self.samples_input.setText(str(samples))

    def calculate_data(self):
        start_loop =int(self.start_loop_input.text())
        end_loop = int(self.end_loop_input.text())
        FPS_maya = int(self.FPS_maya_combobox.currentText())
        FPS_loop = int(self.FPS_loop_combobox.currentText())
        samples = float(self.samples_input.text())
        modulo = FPS_maya/FPS_loop
        duration = end_loop-start_loop
        samples = FPS_loop * (duration/FPS_maya)
        angle = 360/samples

        return modulo, duration, samples, angle

    def run(self):
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

        pm.undoInfo(openChunk=True)
        try:
            for obj in selected:
                self.duplicate_on_even_frames(obj)
        finally:
            pm.undoInfo(closeChunk=True)
            
    def duplicate_on_even_frames(self,obj):

        # Create the group, strip namespace from selected object's name if present
        parent_name = obj.getParent().split(':')[-1]
        group_name = "{}_LOOP".format(parent_name)

        if pm.objExists(group_name):
            pm.delete(group_name)

        group = pm.group(em=True, name=group_name)

        # Define rotation expression for the LOOP group

        modulo, duration, samples, angle  = self.calculate_data()
        rotation_expression = f"{group_name}.rotateY = floor(frame / {modulo}) * {angle};"
        rot_expression = pm.expression(s=rotation_expression)

        start_loop =int(self.start_loop_input.text())
        end_loop = int(self.end_loop_input.text())



        print("------ Begins ------")
        print (f"Generating {samples} samples")
        print (f"Speed Angle: {angle}")
        print("")
        # Loop through the frames
        for frame in range(start_loop, end_loop):
            # Check if the frame number is divisible by 2
            if frame % modulo == 0:
                # Set the current time to the current frame
                pm.currentTime(frame)

                # Duplicate the object
                duplicated = pm.duplicate(obj)
                renamed_duplicated = pm.rename(duplicated[0], "{}_{}".format(obj[0], frame))
                subGroup = pm.group(em=True, name=f"zeroOut_{renamed_duplicated.name()}")



                # Rename the duplcated object and parent to the group
                pm.parent(subGroup,group)
                pm.parent(renamed_duplicated,subGroup)
                print("Succes on time: " +str(frame))
        obj.getParent().visibility.set(0)
        print("------ End ------")

if __name__ == "__main__":
    custom_ui = CustomUI()
    custom_ui.show()
