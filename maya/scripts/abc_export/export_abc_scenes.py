import os
import sys
import re
import importlib
import subprocess
from threading import Thread

from pymel.core import *
from pymel.all import *

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *

modules = ["ABCExport", "ABCExportAsset"]
from utils import *

unload_packages(silent=True, packages=modules)
for module in modules: importlib.import_module(module)

from ABCExport import *


def export_set(frame):
    scene_name = sceneName()
    if len(scene_name) > 0 and len(ls("_____SET_____")) > 0:
        path = ".".join(scene_name.split(".")[:-1]) + "_set.abc"
        refresh(suspend=True)
        AbcExport(j="-frameRange %s %s -writeVisibility -worldSpace -dataFormat ogawa -root "
                    "|_____SET_____ -file \"%s\"" % (frame, frame, path))
        refresh(suspend=False)


def export_cam(start_frame, end_frame):
    scene_name = sceneName()
    cams = ls("*:rendercam")
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
            refresh(suspend=True)
            AbcExport(j="-frameRange %s %s -writeVisibility -worldSpace -dataFormat ogawa -root "
                        "%s -file \"%s\"" % (start_frame, end_frame, name, cam_file_path))
            refresh(suspend=False)


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


def print_scene(messages):
    print(
        "\n#################################################################################################\n")
    for m in messages:
        print(m)
    print(
        "\n#################################################################################################\n\n\n")


def export_char_in_scene(scene_path, database_path, abc_path, nb, nb_tot, filter_char):
    os.system("cls")

    filter_char_enabled = len(filter_char) > 0

    print_scene(["Opening the scene : " + scene_path])
    openFile(scene_path, force=True)

    abcs = ABCExport.retrieve_abcs(database_path)
    start_frame = int(playbackOptions(min=True, query=True))
    end_frame = int(playbackOptions(max=True, query=True))

    if not filter_char_enabled:
        os.system("cls")
        print_scene(["Exporting : _____SET_____", "From scene : " + scene_path, "Scene " + nb + " on " + nb_tot])
        export_set(start_frame)

        os.system("cls")
        print_scene(["Exporting : rendercam", "From scene : " + scene_path, "Scene " + nb + " on " + nb_tot])
        export_cam(start_frame, end_frame)

    abc_exported = []
    for abc in abcs:
        if not filter_char_enabled or filter_char == abc.get_name():
            name_num = abc.get_name_with_num()
            asset_dir_path = os.path.join(abc_path, name_num)
            next_version = str(ABCExportAsset.next_version(asset_dir_path))
            os.system("cls")
            print_scene(["Exporting : " + name_num, "Version : " + next_version, "from scene : " + scene_path,
                         "Scene " + nb + " on " + nb_tot])
            abc_exported.append((name_num, next_version))
            abc.export(abc_path, start_frame, end_frame)
    return abc_exported


def export_abcs_from_scenes(list_scenes, current_project_dir, filter_char):
    database_path = os.path.join(current_project_dir, "assets/_database")
    scene_abc_exported = {}
    nb_scenes = len(list_scenes)
    i = 1
    for file_path in list_scenes:
        print(i, os.path.isfile(file_path), file_path)
        if os.path.isfile(file_path):
            match = re.match(r"^(" + current_project_dir + r"\/shots\/[a-zA-Z0-9_\- \.]+)\/.*$", file_path)
            if match:
                shot_folder = match.group(1)
                abc_export_path = os.path.join(shot_folder, "abc")
                os.makedirs(abc_export_path, exist_ok=True)
                scene_abc_exported[file_path] = export_char_in_scene(file_path, database_path, abc_export_path, str(i),
                                                                     str(nb_scenes),filter_char)
        i += 1

    os.system("cls")
    messages = ["ABC Exported by scene :"]
    for scene_path, abcs in scene_abc_exported.items():
        messages.append("\n" + scene_path + " :")
        for abc, version in abcs:
            messages.append("\t" + abc + " [" + version + "]")
    print_scene(messages)


def export_all(current_project_dir, scenes, filter_char):
    subprocess.check_call(
        [r"C:\Program Files\Autodesk\Maya2022\bin\mayapy.exe", __file__, current_project_dir, filter_char] + scenes)


def run_export_abc_scenes(folder_type, filter_char):
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
        thread = Thread(target=export_all, args=(current_project_dir, scenes, filter_char))
        thread.start()


if __name__ == '__main__':
    export_abcs_from_scenes(sys.argv[3:], sys.argv[1], sys.argv[2])
    os.system("pause")
    print("wait a few seconds")
