import os
import pymel.core as pm
import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore

def list_directories(path):
    """ List only the directories in the specified path. """
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
def find_root_object(target_name):
    root_objects = pm.ls(assemblies=True)
    for root_object in root_objects:
        if root_object.nodeName() == target_name:
            return root_object
    return None

def confirm_creation(directory):
    message = "  Publish new version ? \n %s" %(directory)
    return cmds.confirmDialog(title='Confirm Creation',
                              message=message,
                              button=['Yes', 'Cancel'],
                              defaultButton='Yes',
                              cancelButton='Cancel',
                              dismissString='Cancel')



def run():
    def export_proxy(version,export_type):

        scene_name = pm.system.sceneName()
        asset_dir = os.path.dirname(os.path.dirname(scene_name))
        asset_name = asset_dir.split("/")[-1]
        if export_type == "abc":
            abc_dir = os.path.join(asset_dir, "abc")
        else:
            abc_dir = os.path.join(asset_dir,"houdini","sources")


        var_name = asset_name + "_" + version
        var_dir = os.path.join(abc_dir, var_name)
        if not os.path.exists(var_dir):
            os.makedirs(var_dir)
        version_list = list_directories(var_dir)

        try:
            latest_version = version_list[-1]
            next_version = "{:04d}".format(int(latest_version))
        except:
            print("use default version number 0000")
            next_version="0000"


        next_version_dir = os.path.join(var_dir,next_version)
        print(next_version_dir)
        user_choice = confirm_creation(next_version_dir)
        if user_choice != 'Yes':
            print("Abort by user")
            return

        if not os.path.exists(next_version_dir):
            os.makedirs(next_version_dir)

        # Get the current scene's start and end frame range
        start_frame = pm.playbackOptions(query=True, min=True)
        end_frame = pm.playbackOptions(query=True, max=True)

        selected = pm.selected()[0]
        # Gather geometry to export from the current selection
        geo_list_to_export = [selected.longName()]
        geo_string_to_export = " -root ".join(geo_list_to_export)
        abc_path = os.path.join(next_version_dir, var_name + "_proxy.abc").replace("\\","/")
        print(abc_path)

        # Construct the Alembic export job string
        job = '-frameRange {} {} -stripNamespaces -uvWrite -writeColorSets -worldSpace -writeFaceSets -dataFormat ogawa -root {} -file "{}"'.format(
            start_frame, end_frame, geo_string_to_export, abc_path
        )
        print(job)
        pm.AbcExport(j=job)
        selected.setParent(original_parent)

    def export(version,export_type):

        scene_name = pm.system.sceneName()
        asset_dir = os.path.dirname(os.path.dirname(scene_name))
        asset_name = asset_dir.split("/")[-1]
        if export_type == "abc":
            abc_dir = os.path.join(asset_dir, "abc")
        else:
            abc_dir = os.path.join(asset_dir,"houdini","sources")


        var_name = asset_name + "_" + version
        var_dir = os.path.join(abc_dir, var_name)
        if not os.path.exists(var_dir):
            os.makedirs(var_dir)
        version_list = list_directories(var_dir)
        print(version_list)
        try:
            latest_version = version_list[-1]

            next_version = "{:04d}".format(int(latest_version) + 1)
        except:
            print("use default version number 0000")
            next_version="0000"


        next_version_dir = os.path.join(var_dir,next_version)
        print(next_version_dir)
        user_choice = confirm_creation(next_version_dir)
        if user_choice != 'Yes':
            print("Abort by user")
            return

        if not os.path.exists(next_version_dir):
            os.makedirs(next_version_dir)

        # Get the current scene's start and end frame range
        start_frame = pm.playbackOptions(query=True, min=True)
        end_frame = pm.playbackOptions(query=True, max=True)

        selected = pm.selected()[0]
        original_parent = selected.getParent()

        if original_parent:
            short_name = selected.nodeName()
            root_object = find_root_object(short_name)
            if root_object:
                pm.rename(root_object, short_name + "_TMP_")

            selected.setParent(world=True)

        # Gather geometry to export from the current selection
        geo_list_to_export = [selected.longName()]
        geo_string_to_export = " -root ".join(geo_list_to_export)
        abc_path = os.path.join(next_version_dir, var_name + ".abc").replace("\\","/")
        print(abc_path)

        # Construct the Alembic export job string
        job = '-frameRange {} {} -stripNamespaces -uvWrite -writeColorSets -worldSpace -writeFaceSets -dataFormat ogawa -root {} -file "{}"'.format(
            start_frame, end_frame, geo_string_to_export, abc_path
        )
        print(job)
        pm.AbcExport(j=job)
        selected.setParent(original_parent)

    def on_export_clicked():
        version = version_dropdown.currentText()
        export_type = export_type_dropdown.currentText().lower()
        if proxy_checkbox.isChecked():
            export_proxy(version, export_type)
        else:
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

    proxy_checkbox = QtWidgets.QCheckBox("Proxy")
    layout.addWidget(proxy_checkbox)

    # Button to trigger export
    export_button = QtWidgets.QPushButton("Export")
    export_button.clicked.connect(on_export_clicked)
    layout.addWidget(export_button)

    window.show()

# Example usage
run()
