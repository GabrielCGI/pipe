import importlib
import maya.mel as mel
import pymel.core as pm
from common.standin_utils import *
import collectMayaScene
importlib.reload(collectMayaScene)

import maya.OpenMayaUI as mui
from PySide2 import QtWidgets, QtGui, QtCore
import shiboken2

def maya_main_window():
    main_window_ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def add_separator_to_layout(layout):
    separator = QtWidgets.QFrame()
    separator.setFrameShape(QtWidgets.QFrame.HLine)
    separator.setFrameShadow(QtWidgets.QFrame.Sunken)
    layout.addWidget(separator)

def get_arnold_bucket_size():
    if pm.pluginInfo('mtoa', q=True, loaded=True):
        return pm.getAttr('defaultArnoldRenderOptions.bucketSize')
    else:
        raise Exception('Arnold plugin is not loaded!')

def set_slider_to_64(slider):
    slider.setValue(64)
    update_arnold_bucket_size(64)

def update_text_edit(slider_value, text_edit_widget):
    text_edit_widget.setText(str(slider_value))
    update_arnold_bucket_size(slider_value)

def update_slider_from_text(text_edit_widget, slider):
    value = int(text_edit_widget.text())
    slider.setValue(value)
    update_arnold_bucket_size(value)

def update_arnold_bucket_size(value):
    arnold_renderer = pm.ls(type="aiOptions")[0]
    pm.setAttr(arnold_renderer.bucketSize, value)

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
        "ignore Imagers",
        "enableProgressiveRender"
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



def run():
    execute_cleanup = False
    execute_standins = False

    def set_bucket_size(bucket_size):
        bucket_layout = QtWidgets.QHBoxLayout()

        bucket_label = QtWidgets.QLabel("Bucket Size")
        bucket_layout.addWidget(bucket_label)

        text_edit = QtWidgets.QLineEdit()
        text_edit.setText(str(bucket_size))  # Set valeur par défaut
        text_edit.setMaximumWidth(70)
        bucket_layout.addWidget(text_edit)

        bucket_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        bucket_slider.setRange(16, 256)
        bucket_slider.setValue(bucket_size)  # Set valeur par défaut
        bucket_layout.addWidget(bucket_slider)

        bucket_button = QtWidgets.QPushButton("64")
        bucket_button.setMaximumWidth(25)
        bucket_layout.addWidget(bucket_button)

        # Signaux et Slots
        bucket_button.clicked.connect(lambda: set_slider_to_64(bucket_slider))
        bucket_slider.valueChanged.connect(lambda value: update_text_edit(value, text_edit))
        text_edit.editingFinished.connect(lambda: update_slider_from_text(text_edit, bucket_slider))

        layout.addLayout(bucket_layout)

    def add_imagers_section():
        imagers_list_widget = QtWidgets.QListWidget()
        names = [imager.name() for imager in imagers]
        imagers_list_widget.addItems(names)

        # Ajustement de la hauteur en fonction du nombre d'éléments
        item_height = 15
        max_visible_items = 20
        total_height = min(len(names), max_visible_items) * item_height
        imagers_list_widget.setMaximumHeight(total_height)

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
    dialog.setMinimumSize(400, 300)
    layout = QtWidgets.QVBoxLayout()

    bucket_size = get_arnold_bucket_size()
    imagers = has_active_arnold_imager()
    checked_attributes = list_checked_overrides()


    layout.addStretch()


    if bucket_size != 64:
        set_bucket_size(bucket_size)
        execute_cleanup = True
    else:
        label = QtWidgets.QLabel("Correct Bucket Size")
        label.setStyleSheet("color: green;")
        layout.addWidget(label)


    layout.addStretch()
    add_separator_to_layout(layout)
    layout.addStretch()


    if imagers:
        add_imagers_section()
        execute_cleanup = True
    else:
        label = QtWidgets.QLabel("No Active Arnold Imager")
        label.setStyleSheet("color: green;")
        layout.addWidget(label)


    layout.addStretch()
    add_separator_to_layout(layout)
    layout.addStretch()


    if checked_attributes:
        add_checked_overrides_section()
        execute_cleanup = True
    else:
        label = QtWidgets.QLabel("No Checked Overrides")
        label.setStyleSheet("color: green;")
        layout.addWidget(label)


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


    # Set du layout au dialog
    dialog.setLayout(layout)

    # execute_standins=True si execute_cleanup==False ou si dialog_exec_ est accepté
    #(on exec le dialog, donc il s'affiche)
    execute_standins = not execute_cleanup or dialog.exec_() == QtWidgets.QDialog.Accepted


    collectMayaScene.run()


    pm.setAttr("defaultArnoldRenderOptions.procedural_searchpath", "X:/;Y:/;Z:/;I:/;B:/;R:/")
    pm.setAttr("defaultArnoldRenderOptions.texture_searchpath", "X:;Y:;Z:;I:;B:")
    pm.setAttr("defaultArnoldRenderOptions.absoluteTexturePaths", False)
    pm.setAttr("defaultArnoldRenderOptions.absoluteProceduralPaths", False)



    # Run modified submit to deadline
    pm.mel.eval('source "R:/deadline/submission/Maya/Main/SubmitMayaToDeadlineRanch.mel";SubmitMayaToDeadlineRanch;')
