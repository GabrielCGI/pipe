import pymel.core as pm
from PySide2 import QtWidgets
from PySide2.QtWidgets import QWidget, QDesktopWidget, QLabel
from PySide2.QtCore import Qt, QPoint

# Your createGarland function here...

def createGarland(curve, bulb, num_bulbs=20):
    """
    Create a garland along the curve using the provided bulb mesh.

    Args:
        curve (pm.nt.Transform): The curve along which the garland is created.
        bulb (pm.nt.Transform): The bulb mesh to duplicate and place along the curve.
        num_bulbs (int): The number of bulbs to place on the curve.
    """

    # Create a list to hold all bulb instances
    bulbs = []

    # List to store the motion paths for deletion
    motionPaths = []

    # Loop through each bulb position
    for i in range(num_bulbs):
        # Find the parameter along the curve for the current bulb
        param = float(i) / (num_bulbs - 1)

        # Duplicate the bulb mesh
        new_bulb = pm.duplicate(bulb)[0]

        # Create a motion path and attach the bulb to it
        mp = pm.pathAnimation(
            new_bulb,
            c=curve,
            fractionMode=True,
            follow=True,              # Make the bulb's front axis follow the curve's tangent
            followAxis="z",          # Assuming "y" axis of the bulb should be tangent to the curve. Adjust if needed.
            upAxis="y",              # Assuming "z" axis of the bulb should point upwards. Adjust if needed.
            worldUpType="vector",    # Use a defined vector for the world up direction
            worldUpVector=[0, -1, 0]  # Use the Y-axis as the world up direction
        )
        pm.setAttr(mp + ".uValue", param)

        bulbs.append(new_bulb)
        motionPaths.append(mp)  # Add the motion path to the list

    # Group all bulbs under one node for easier manipulation
    garland_group = pm.group(em=True, name="garland_grp")
    for bulb_instance in bulbs:
        pm.parent(bulb_instance, garland_group)
        # Delete the history of each bulb instance
        pm.delete(bulb_instance, constructionHistory=True)

    # Delete all motion paths
    pm.delete(motionPaths)
    pm.select(curve)
    pm.sweepMeshFromCurve()
    sweep= pm.selected()[0]
    sweep.scaleProfileX.set(0.1)

    return garland_group

class CustomUI(QWidget):
    def __init__(self, parent=None):
        super(CustomUI, self).__init__(parent)

        self.setWindowTitle("Garland Creator")
        self.__ui_width = 450
        self.__ui_height = 180
        self.__ui_pos = QDesktopWidget().availableGeometry().center() - QPoint(self.__ui_width, self.__ui_height) / 2
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)

        # Set the window geometry
        self.setGeometry(self.__ui_pos.x(), self.__ui_pos.y(), self.__ui_width, self.__ui_height)

        # Create and set the layout
        layout = QtWidgets.QVBoxLayout()

        # Create and add a label for instructions on using the script
        instruction_label = QLabel("1. Select a curve .\n2. Select bulb")
        layout.addWidget(instruction_label)

        # Create a label and a spin box for setting the number of bulbs
        label = QtWidgets.QLabel("Number of Bulbs:")
        self.spin_box = QtWidgets.QSpinBox()
        self.spin_box.setMinimum(1)
        self.spin_box.setMaximum(100)
        self.spin_box.setValue(35)  # Default value

        # Create a button to trigger the garland creation
        button = QtWidgets.QPushButton("Create Garland")
        button.clicked.connect(self.createGarlandWithSelectedObjects)

        # Add the widgets to the layout
        layout.addWidget(label)
        layout.addWidget(self.spin_box)
        layout.addWidget(button)

        # Set the layout on the window
        self.setLayout(layout)

    def createGarlandWithSelectedObjects(self):
        selected = pm.selected()
        if len(selected) == 2:
            pm.undoInfo(openChunk=True)
            createGarland(selected[0], selected[1], self.spin_box.value())
            cmds.undoInfo(closeChunk=True)
        else:
            pm.warning("Please select a curve and a bulb mesh.")

# Run the UI
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])
    ui = CustomUI()
    ui.show()
    app.exec_()
