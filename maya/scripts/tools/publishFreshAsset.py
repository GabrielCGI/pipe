import os
import pymel.core as pm
from PySide2 import QtWidgets, QtCore

def list_directories(path):
    """ List only the directories in the specified path. """
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

def run():
    def export(version,export_type):
        scene_name = pm.system.sceneName()
        asset_dir = os.path.dirname(os.path.dirname(scene_name))
        asset_name = asset_dir.split("/")[-1]
        if export_type == "abc":
            abc_dir = os.path.join(asset_dir, "abc")
        else:
            abc_dir = os.path.join(asset_dir,"houdini","sources")
        if not os.path.exists(abc_dir):
            os.makedirs(abc_dir)

        var_name = asset_name + "_" + version
        var_dir = os.path.join(abc_dir, var_name)
        version_list = list_directories(var_dir)
        print(version_list)
        latest_version = version_list[-1]

        next_version = "{:04d}".format(int(latest_version) + 1)
        next_version_dir = os.path.join(var_dir,next_version)
        print(next_version_dir)
        if not os.path.exists(next_version_dir):
            os.makedirs(next_version_dir)

        # Get the current scene's start and end frame range
        start_frame = pm.playbackOptions(query=True, min=True)
        end_frame = pm.playbackOptions(query=True, max=True)

        # Gather geometry to export from the current selection
        geo_list_to_export = [s.longName() for s in pm.ls(selection=True)]
        geo_string_to_export = " -root ".join(geo_list_to_export)
        abc_path = os.path.join(next_version_dir, var_name + ".abc").replace("\\","/")
        print(abc_path)

        # Construct the Alembic export job string
        job = '-frameRange {} {} -stripNamespaces -uvWrite -writeColorSets -worldSpace -writeFaceSets -dataFormat ogawa -root {} -file "{}"'.format(
            start_frame, end_frame, geo_string_to_export, abc_path
        )
        print(job)
        pm.AbcExport(j=job)

    def on_export_clicked():
        version = version_dropdown.currentText()
        export_type = export_type_dropdown.currentText().lower()
        export(version, export_type)
        window.close()
    # UI Setup
    app = QtWidgets.QApplication.instance()  # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QtWidgets.QApplication([])

    window = QtWidgets.QWidget()
    window.setWindowTitle('Export Version Selector')
    layout = QtWidgets.QVBoxLayout(window)

    # Dropdown for version selection
    version_dropdown = QtWidgets.QComboBox()
    version_options = ["00", "10", "20", "30", "40", "50", "60", "70", "80", "90"]
    version_dropdown.addItems(version_options)
    layout.addWidget(version_dropdown)

    # Dropdown for type of export
    export_type_dropdown = QtWidgets.QComboBox()
    export_type_dropdown.addItems(["ABC", "Source"])
    layout.addWidget(export_type_dropdown)

    # Button to trigger export
    export_button = QtWidgets.QPushButton("Export")
    export_button.clicked.connect(on_export_clicked)
    layout.addWidget(export_button)

    window.show()

# Example usage
run()
