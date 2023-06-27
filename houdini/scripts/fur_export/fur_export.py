import hou
import re
import os
import time
import importlib
import warnings
import _alembic_hom_extensions as ahe

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from utils import *


def print_log(msg, log_file):
    """
    Print log in console and also in a file
    :param msg
    :param log_file
    :return:
    """
    print(msg)
    log_file.write(msg + "\n")


def list_shots(current_project_dir):
    """
    Choose a list of shots
    :param current_project_dir
    :return:
    """
    file_dialog = QFileDialog()
    file_dialog.setDirectory(current_project_dir)
    file_dialog.setFileMode(QFileDialog.DirectoryOnly)
    file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
    file_view = file_dialog.findChild(QListView, 'listView')
    file_view.setSelectionMode(QAbstractItemView.MultiSelection)
    f_tree_view = file_dialog.findChild(QTreeView)
    f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)
    paths = []
    if file_dialog.exec():
        paths = file_dialog.selectedFiles()
    return paths


def list_abcs(shots, char_dict):
    """
    List the abcs contained in the shots
    :param shots
    :param char_dict
    :return:
    """
    abcs = {}
    for shot_path in shots:
        # Check if shot path is valid
        if not os.path.isdir(shot_path):
            continue

        abc_path = os.path.join(shot_path, "abc")
        # Check if abc folder exists
        if not os.path.exists(abc_path):
            continue

        chars = []
        for char in os.listdir(abc_path):
            # Check if the character is known and has fur to be exported
            if char not in char_dict:
                continue

            char_path = os.path.join(abc_path, char)
            versions = sorted(os.listdir(char_path), reverse=True)
            nb_versions = len(versions)
            index = 0
            # Check if the abc has a version available
            if nb_versions == 0:
                continue
            # Check each version (take the latest valid version)
            while nb_versions > index:
                curr_version = versions[index]
                abc_char_path = os.path.join(char_path, curr_version, char + ".abc").replace("\\", "/")
                if os.path.isfile(abc_char_path):
                    chars.append((char, curr_version, abc_char_path, char_dict[char]))
                    break
                else:
                    continue
        # Add the scene with the characters data if there are some
        if len(chars) > 0:
            abcs[shot_path] = chars
    return abcs


def create_fur(file_path, otl):
    """
    Create the fur node
    :param file_path
    :param otl
    :return:
    """
    obj_context = hou.node('/obj')
    fur = obj_context.createNode(otl)
    # Set the Animated Alembic to the latest character abc
    fur.parm("Anim_par").set(file_path)
    return fur


def export_fur(shot_path, char_name, fur):
    """
    Export the fur node
    :param shot_path
    :param char_name
    :param fur
    :return:
    """
    char_fur_path = os.path.join(shot_path, "abc_fur", char_name)
    version = 0
    # Find the latest fur version to increment it
    if os.path.exists(char_fur_path):
        versions_str = [child for child in os.listdir(char_fur_path) if
                        os.path.isdir(os.path.join(char_fur_path, child))]
        if len(versions_str) > 0:
            version = int(versions_str[-1])
    export_path = os.path.join(char_fur_path, str(version + 1).rjust(4, "0"), char_name + "_fur.abc")
    # Set the fur export path
    fur.parm("filename").set(export_path)
    # Create the version folder
    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    # Execute the export
    fur.parm("execute").pressButton()
    return export_path


def set_params(fur, options, abc_path):
    """
    Set some params
    :param fur
    :param options
    :param abc_path
    :return:
    """
    if "motion_blur" in options:
        fur.parm("motionBlur").set(options["motion_blur"])
    if "samples" in options:
        fur.parm("samples").set(options["samples"])
    if "shutter" in options and len(options["shutter"]) == 2:
        fur.parm("shutter1").set(options["shutter"][0])
        fur.parm("shutter2").set(options["shutter"][1])
    if "fps" in options:
        # Set the start frame and end frame
        fps = options["fps"]
        start_time, end_time = ahe.alembicTimeRange(abc_path)
        start_time = round(start_time * fps) - 1
        end_time = round(end_time * fps) + 1
        fur.parm("f1").setExpression('"%s"' % start_time)
        fur.parm("f2").setExpression('"%s"' % end_time)
    if "probability" in options:
        fur.parm("Probability_par").set(options["probability"])


def run(current_project_dir, char_dict, options, log_file_folder):
    """
    Run Fur Export
    :param current_project_dir
    :param char_dict
    :param options
    :param log_file_folder
    :return:
    """
    # Get the next log version
    version = 0
    if not os.path.exists(log_file_folder): os.makedirs(log_file_folder)
    for fur_export_log_name in os.listdir(log_file_folder):
        match = re.match(r"^fur_export_([0-9]+).log$", fur_export_log_name)
        if not match:
            continue
        curr_version = int(match.group(1))
        if curr_version > version:
            version = curr_version
    log_file_path = os.path.join(log_file_folder, "fur_export_" + str(version + 1) + ".log")
    # clear log if exists
    open(log_file_path, "w").close()
    # Open file in Append Mode
    with open(log_file_path, "a") as log_file:
        # Check if current project is valid
        if current_project_dir is None and os.path.exists(current_project_dir):
            print_log("CURRENT_PROJECT_DIR is not valid", log_file)
            return

        # Retrieve shots and the abcs in it
        shots = list_shots(current_project_dir)
        abcs = list_abcs(shots, char_dict)
        # Check if abcs found
        if len(abcs) == 0:
            print_log("No char found", log_file)
            return

        # Dialog for confirmation
        msg = "Do you want to export these furs ?\n\n"
        for shot, abcs_data in abcs.items():
            msg += shot + "\n"
            for abc_data in abcs_data:
                msg += "\t" + abc_data[0] + " [" + abc_data[1] + "]\n"
        ret = QtWidgets.QMessageBox().question(None, '', msg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        # Check if dialog has been confirmed
        if ret != QtWidgets.QMessageBox.Yes:
            print_log("Export cancelled", log_file)
            return

        for shot_path, abcs_data in abcs.items():
            msg = "+----- Exporting from shot : " + shot_path + " -----"
            print_log(msg, log_file)
            for abc_data in abcs_data:
                char_name = abc_data[0]
                fur_version = abc_data[1]
                abc_path = abc_data[2]
                otl = abc_data[3]
                time_log = "Time        : " + time.strftime("%d-%m-%Y %H:%M:%S")
                # Create the fur Node
                fur = create_fur(abc_path, otl)
                # Apply Options to the fur
                set_params(fur, options, abc_path)
                # Export the fur
                print_log("| Exporting " + char_name, log_file)
                new_export_path = export_fur(shot_path, char_name, fur).replace("\\", "/")
                print_log("|      +---> " + new_export_path, log_file)
                # Logs
                log_fur_path = os.path.join(
                    os.path.dirname(new_export_path), "export_"+time.strftime("%d_%m_%Y")+".log").replace("\\", "/")
                time_log += " --> " + time.strftime("%H:%M:%S") + "\n"
                char_log = "Char        : " + char_name + "\n"
                version_log = "Fur Version : " + str(fur_version) + "\n"
                abc_path_log = "ABC Path    : " + abc_path + "\n"
                export_path_log = "Export Path : " + new_export_path + "\n"
                with open(log_fur_path, "w") as log_fur_file:
                    log_fur_file.write(time_log + export_path_log + char_log + version_log + abc_path_log)

                # Delete the fur Node
                fur.destroy()
            print_log("+" + (len(msg) - 1) * "-" + "\n", log_file)
