import importlib
import maya.mel as mel
import pymel.core as pm
from common.standin_utils import *
import replace_by_tx
import file_collector_ranch_sender.CollectorCopier
from file_collector_ranch_sender.CollectorCopier import *

import maya.OpenMayaUI as mui
from PySide2 import QtWidgets, QtGui
import shiboken2

def maya_main_window():
    main_window_ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


def get_out_of_date_standins():
    standins = pm.ls(type="aiStandIn")
    out_of_date_standins = []
    for standin in standins:
        parsed_standin = parse_standin(standin)
        if parsed_standin["valid"]:
            object_name = parsed_standin["object_name"]
            active_variant = parsed_standin["active_variant"]
            standin_versions = parsed_standin["standin_versions"]
            active_version = parsed_standin["active_version"]
            last_version = standin_versions[active_variant][0][0]
            if active_version != last_version:
                out_of_date_standins.append((object_name, active_version, last_version))
    return out_of_date_standins

# IMAGERS
def has_active_arnold_imager():
    # Reference the defaultArnoldRenderOptions node
    arnold_render_options = pm.PyNode("defaultArnoldRenderOptions")

    # Check the 'imagers' attribute for connections
    imagers_connections = arnold_render_options.imagers.listConnections()

    # If any connections exist, it means there's an active Arnold Imager
    if imagers_connections:
        return imagers_connections
    return False

def remove_selected_imagers(imagers_list_widget):
    for item in imagers_list_widget.selectedItems():
        imager_node = pm.PyNode(item.text())
        
        try:
            pm.disconnectAttr(imager_node.message, 'defaultArnoldRenderOptions.imagers[0]')
        except:
            pass
        
        pm.delete(imager_node)
        imagers_list_widget.takeItem(imagers_list_widget.row(item))


# OVERRIDES
def list_checked_overrides():
    # Get the Arnold renderer node
    arnold_renderer = pm.ls(type="aiOptions")[0]

    # Define a list of attributes related to feature overrides
    attributes = [
        "ignore Textures",
        "ignore Shaders",
        "ignore Atmosphere",
        "ignore Lights",
        "ignore Shadows",
        "ignore Subdivision",
        "ignore Displacement",
        "ignore Bump",
        "ignore Smoothing",
        "ignore Motion",
        "ignore Dof",
        "ignore Sss",
        "ignore Operators",
        "force Translate Shading Engines",
        "ignore Imagers"
    ]

    checked_attributes = []

    # Check each attribute to see if it's checked
    for attr in attributes:
        if arnold_renderer.attr(attr).get():
            checked_attributes.append(attr)

    return checked_attributes

def checkbox_changed(cb):
    # Get the Arnold renderer node
    arnold_renderer = pm.ls(type="aiOptions")[0]
    attribute_name = cb.text()
    
    if cb.isChecked():
        arnold_renderer.setAttr(attribute_name, 1)
    else:
        arnold_renderer.setAttr(attribute_name, 0)

def select_all_changed(state, select_all_checkbox, all_checkboxes):
    is_checked = select_all_checkbox.isChecked()
    for checkbox in all_checkboxes:
        checkbox.setChecked(is_checked)



def run(force_override_ass_paths_files):
    execute_cleanup = False
    execute_standins = False

    def add_imagers_section():
        # Add a QListWidget for imagers
        imagers_list_widget = QtWidgets.QListWidget()
        names = [imager.name() for imager in imagers]
        imagers_list_widget.addItems(names)

        imagers_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        layout.addWidget(QtWidgets.QLabel("Active Arnold Imagers:"))
        layout.addWidget(imagers_list_widget)

        remove_button = QtWidgets.QPushButton("Remove Selected Imagers")
        remove_button.clicked.connect(lambda: remove_selected_imagers(imagers_list_widget))
        layout.addWidget(remove_button)

    def add_checked_overrides_section():
        all_checkboxes = []

        layout.addWidget(QtWidgets.QLabel("Checked Overrides:"))

        select_all_checkbox = QtWidgets.QCheckBox("")
        select_all_checkbox.setChecked(True)
        select_all_checkbox.stateChanged.connect(lambda state: select_all_changed(state, select_all_checkbox, all_checkboxes))
        layout.addWidget(select_all_checkbox)

        for check in checked_attributes:
            checkbox = QtWidgets.QCheckBox(check)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, cb=checkbox: checkbox_changed(cb))
            layout.addWidget(checkbox)
            all_checkboxes.append(checkbox)

    dialog = QtWidgets.QDialog(maya_main_window())
    dialog.setWindowTitle("Cleanup")
    layout = QtWidgets.QVBoxLayout()

    imagers = has_active_arnold_imager()
    checked_attributes = list_checked_overrides()

    
    if imagers:
        add_imagers_section()
        execute_cleanup = True
    else:
        layout.addWidget(QtWidgets.QLabel("No Active Arnold Imager"))

    separator = QtWidgets.QFrame()
    separator.setFrameShape(QtWidgets.QFrame.HLine)
    separator.setFrameShadow(QtWidgets.QFrame.Sunken)
    layout.addWidget(separator)

    if checked_attributes:
        add_checked_overrides_section()
        execute_cleanup = True
    else:
        layout.addWidget(QtWidgets.QLabel("No Checked Overrides"))


    # Ajout des boutons "Continue" et "Cancel"
    continue_button = QtWidgets.QPushButton("Continue")
    cancel_button = QtWidgets.QPushButton("Cancel")

    # Connexion des boutons à leurs actions
    continue_button.clicked.connect(dialog.accept)
    cancel_button.clicked.connect(dialog.reject)

    # Ajout des boutons au layout
    button_layout = QtWidgets.QHBoxLayout()
    button_layout.addWidget(continue_button)
    button_layout.addWidget(cancel_button)

    layout.addLayout(button_layout)



    # Set the layout to the dialog and show it
    dialog.setLayout(layout)
    execute_standins = not execute_cleanup or dialog.exec_() == QtWidgets.QDialog.Accepted



    if execute_standins == True:
        out_of_date_standins = get_out_of_date_standins()
        if len(out_of_date_standins) > 0:
            max_display_standins = 15
            msg = "You have out of date Standin(s) :\n\n"
            for index, standin_data in enumerate(out_of_date_standins):
                if index == max_display_standins:
                    nb_remaining = len(out_of_date_standins) - max_display_standins
                    msg += "\n" + str(nb_remaining) + " other(s) standins ...\n"
                    break
                msg += str(standin_data[0]) + " : \n        actual : " + str(standin_data[1]) + \
                    "\n        latest : " + str(standin_data[2]) + "\n"
            msg += "\nYou should update them with the Asset Loader.\nDo you want to continue ?"
            answer_out_of_date_standins = pm.confirmDialog(
                title='Out of date StandIn(s)',
                icon="question",
                message=msg,
                button=['Continue', 'Cancel'],
                defaultButton='Continue',
                dismissString='Cancel',
                cancelButton='Cancel')
            if answer_out_of_date_standins != "Continue":
                return

        pm.setAttr("defaultArnoldRenderOptions.procedural_searchpath", "X:/;Y:/;Z:/;I:/;B:/;R:/")
        pm.setAttr("defaultArnoldRenderOptions.texture_searchpath", "X:;Y:;Z:;I:;B:")
        pm.setAttr("defaultArnoldRenderOptions.absoluteTexturePaths", False)
        pm.setAttr("defaultArnoldRenderOptions.absoluteProceduralPaths", False)

        print("Start replacing by tx")
        replace_by_tx.replace_by_tx()

        # Collect all the paths in the scene and copy them to RANCH
        collector_copier = CollectorCopier(force_override_ass_paths_files)
        collector_copier.run_collect()

        # Run modified submit to deadline
        pm.mel.eval('source "R:/deadline/submission/Maya/Main/SubmitMayaToDeadlineRanch.mel";SubmitMayaToDeadlineRanch;')