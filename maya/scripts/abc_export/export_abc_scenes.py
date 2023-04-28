import os
import sys
import re
import importlib
import subprocess
from threading import Thread

import pymel.core as pm
import pymel.all as pmall

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

from common.utils import *
from .ABCExport import *


def export_set(frame):
    scene_name = pm.sceneName()
    if len(scene_name) > 0 and len(pm.ls("_____SET_____")) > 0:
        path = ".".join(scene_name.split(".")[:-1]) + "_set.abc"
        pm.refresh(suspend=True)
        pm.AbcExport(j="-frameRange %s %s -writeVisibility -worldSpace -dataFormat ogawa -root "
                    "|_____SET_____ -file \"%s\"" % (frame, frame, path))
        pm.refresh(suspend=False)


def export_cam(start_frame, end_frame):
    scene_name = pm.sceneName()
    cams = pm.ls("*:rendercam")
    if len(scene_name) > 0 and len(cams) > 0:
        match = re.match(r"^(.*[\\/]shots[\\/][a-zA-Z0-9_-]*)\/.*$", scene_name)
        if match:
            shot_folder = match.group(1)
            cam_folder = os.path.join(shot_folder, "abc/cam")
            os.makedirs(cam_folder, exist_ok=True)

            # Find new version
            version_max = 1
            for cam_file in os.listdir(cam_folder):
                if os.path.isfile(os.path.join(cam_folder, cam_file)):
                    match_version_cam = re.match(r"^cam\.([0-9]{3})\.abc", cam_file)
                    if match_version_cam:
                        version = int(match_version_cam.group(1))
                        if version_max <= version: version_max = version + 1

            cam_file_path = os.path.join(cam_folder,  "cam."+ str(version_max).zfill(3) + ".abc").replace("\\","/")
            name = cams[0].longName()
            pm.refresh(suspend=True)
            pm.AbcExport(j="-frameRange %s %s -writeVisibility -worldSpace -dataFormat ogawa -root "
                        "%s -file \"%s\"" % (start_frame, end_frame, name, cam_file_path))
            pm.refresh(suspend=False)


def list_scenes(current_project_dir, folder_type):
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

    version_folders = []

    for path in paths:
        for folder in os.listdir(path):
            if re.match(folder_type, folder):
                folder_path = os.path.join(path, folder)
                for version_folder in sorted(os.listdir(folder_path), reverse=True):
                    if re.match(r"^([0-9]+)$", version_folder):
                        version_folders.append(os.path.join(folder_path, version_folder))
                        break

    scene_paths = []
    for version_folder in version_folders:
        for file in sorted(os.listdir(version_folder), reverse=True):
            file_path = os.path.join(version_folder, file).replace("\\", "/")
            if os.path.isfile(file_path) and re.match(r".*\.m[ab]$", file_path):
                scene_paths.append(file_path)
                break

    scene_paths = sorted(scene_paths)
    return scene_paths


def print_scene(log_file, messages):
    str_msg = "+------------------------------------------------------------------------------------------------\n"
    for m in messages:
        str_msg+="| "+m+"\n"
    str_msg+= "+------------------------------------------------------------------------------------------------\n\n"
    print(str_msg)
    log_file.write(str_msg)


def export_char_in_scene(scene_path, database_path, abc_path, nb, nb_tot, filter_char, subsample, log_file):
    os.system("cls")

    filter_char_enabled = len(filter_char) > 0

    print_scene(log_file, ["Opening the scene : " + scene_path])
    pm.openFile(scene_path, force=True)

    abcs = ABCExport.retrieve_abcs(database_path)
    start_frame = int(pm.playbackOptions(min=True, query=True)) - 5
    end_frame = int(pm.playbackOptions(max=True, query=True)) + 5

    if not filter_char_enabled:
        os.system("cls")
        print_scene(log_file, ["Exporting : _____SET_____", "From scene : " + scene_path, "Scene " + nb + " on " + nb_tot])
        export_set(start_frame)

        os.system("cls")
        print_scene(log_file, ["Exporting : rendercam", "From scene : " + scene_path, "Scene " + nb + " on " + nb_tot])
        export_cam(start_frame, end_frame)

    abc_exported = []
    for abc in abcs:
        if not filter_char_enabled or filter_char == abc.get_name():
            name_num = abc.get_name_with_num()
            asset_dir_path = os.path.join(abc_path, name_num)
            next_version = str(ABCExportAsset.next_version(asset_dir_path)).zfill(4)
            os.system("cls")
            print_scene(log_file, ["Exporting : " + name_num, "Version : " + next_version, "from scene : " + scene_path,
                         "Scene " + nb + " on " + nb_tot])
            abc_exported.append((name_num, next_version))
            try:
                abc.export(abc_path, start_frame, end_frame, len(subsample)>0, subsample, True)
            except Exception as e:
                log_file.write(str(e))
    return abc_exported


def export_abcs_from_scenes(list_scenes, current_project_dir, filter_char, subsample, log_file_folder):
    database_path = os.path.join(current_project_dir, "assets/_database")
    scene_abc_exported = {}
    scene_abc_empty = []
    nb_scenes = len(list_scenes)
    # Get the next log version
    version = 0
    if not os.path.exists(log_file_folder): os.makedirs(log_file_folder)
    for abc_export_log_name in os.listdir(log_file_folder):
        match = re.match(r"^abc_export_([0-9]+).log$", abc_export_log_name)
        if not match:
            continue
        curr_version = int(match.group(1))
        if curr_version > version:
            version = curr_version
    log_file_path = os.path.join(log_file_folder, "abc_export_" + str(version + 1) + ".log")

    open(log_file_path, "w").close()

    i = 1
    with open(log_file_path, "a") as log_file:
        for file_path in list_scenes:
            if os.path.isfile(file_path):
                match = re.match(r"^(" + current_project_dir + r"\/shots\/[a-zA-Z0-9_\- \.]+)\/.*$", file_path)
                if match:
                    shot_folder = match.group(1)
                    abc_export_path = os.path.join(shot_folder, "abc")
                    os.makedirs(abc_export_path, exist_ok=True)
                    abc_exported = export_char_in_scene(file_path, database_path, abc_export_path,
                                                        str(i), str(nb_scenes),filter_char, subsample, log_file)
                    if len(abc_exported) > 0:
                        scene_abc_exported[file_path] = abc_exported
                    else:
                        scene_abc_empty.append(file_path)
            i += 1

        os.system("cls")
        scene_exported_filled = len(scene_abc_exported) >0
        scene_empty_filled = len(scene_abc_empty) >0
        if scene_exported_filled or scene_empty_filled:
            messages = []
            if scene_empty_filled:
                messages.append("ABC scene without exports:")
                for scene_path in scene_abc_empty:
                    messages.append(scene_path)
                if scene_exported_filled:
                    messages.append("\n")
            if scene_exported_filled:
                messages.append("ABC Exported by scene :")
                for scene_path, abcs in scene_abc_exported.items():
                    messages.extend(["",scene_path + " :"])
                    for abc, version in abcs:
                        messages.append("\t" + abc + " [" + version + "]")
            print_scene(log_file, messages)
        else:
            print_scene(log_file, ["Nothing have been exported"])

def export_all(current_project_dir, scenes, filter_char, subsample, log_file_folder):
    subprocess.check_call(
        [r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe", __file__, current_project_dir,
         filter_char, subsample, log_file_folder] + scenes)


def run_export_abc_scenes(folder_type, filter_char, subsample, log_file_folder):
    filter_char_enabled = len(filter_char) > 0
    current_project_dir = os.getenv("CURRENT_PROJECT_DIR")
    if current_project_dir is None:
        print_warning("CURRENT_PROJECT_DIR has not been found")
        return
    scenes = list_scenes(current_project_dir, folder_type)
    if len(scenes) == 0:
        print_warning("No scene found")
        return
    scenes_cpd_stripped = [s.replace(current_project_dir, "") for s in scenes]
    scenes_str = "\n".join(scenes_cpd_stripped)
    if filter_char_enabled:
        msg = "Are you sure to export all "+filter_char+" from these scenes ?\n\n" + scenes_str
    else:
        msg = "Are you sure to export all abcs from these scenes ?\n\n" + scenes_str
    ret = QtWidgets.QMessageBox().question(None, '', msg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    if ret == QtWidgets.QMessageBox.Yes:
        thread = Thread(target=export_all, args=(current_project_dir, scenes, filter_char, subsample, log_file_folder))
        thread.start()


if __name__ == '__main__':
    pm.loadPlugin('AbcExport', quiet =True)
    export_abcs_from_scenes(sys.argv[5:], sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    os.system("pause")
    print("wait a few seconds")
