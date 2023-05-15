import maya.cmds as cmds
import os
import sys
import re
import importlib

# Load Abc Plugins
cmds.loadPlugin("AbcImport.mll", quiet=True)
cmds.loadPlugin("AbcExport.mll", quiet=True)

def create_char_standin(anim_abc_path,abc_char_name, mod_folder, operator_folder):
    # Find mod abc file
    mod_files = []
    for file in os.listdir(mod_folder):
        file_path = os.path.join(mod_folder, file)
        if os.path.isfile(file_path) and re.match(r".*mod(\.v[0-9]+)?\.abc", file, re.IGNORECASE):
            mod_files.append(file_path)
    mod_files = sorted(mod_files, reverse=True)

    if len(mod_files) == 0:
        raise Exception("No mod file found in " + mod_folder)

    operator_files = []
    for file in os.listdir(operator_folder):
        file_path = os.path.join(operator_folder, file)
        if os.path.isfile(file_path) and re.match(r".*\.ass", file, re.IGNORECASE):
            operator_files.append(file_path)
    operator_files = sorted(operator_files, reverse=True)

    if len(operator_files) == 0:
        raise Exception("No operator file found in " + operator_folder)

    mod_file_path = mod_files[0]
    operator_file_path = operator_files[0]
    print("mod file           \t", mod_file_path)
    print("operator file      \t", operator_file_path)

    standin_name = abc_char_name + "_00"
    standin_shape_name = standin_name + "Shape"

    if cmds.objExists(standin_name):
        result = cmds.confirmDialog(title='Confirm', message='The character already exist: %s' % standin_name,
                                    button=['Delete manually later', "Delete now"])
        if result == "Delete now":
            cmds.delete(standin_name)
    standin_shape_node = cmds.createNode("aiStandIn", n=standin_shape_name)
    standin_node = cmds.listRelatives(standin_shape_node, parent=True)
    standin_node = cmds.rename(standin_node, standin_name)

    cmds.setAttr(standin_node + ".dso", mod_file_path, type="string")
    cmds.setAttr(standin_node + ".useFrameExtension", 1)
    cmds.setAttr(standin_node + ".abc_layers", anim_abc_path, type="string")
    set_shader = cmds.createNode("aiIncludeGraph", n="aiIncludeGraph_" + abc_char_name)

    cmds.setAttr(set_shader + ".filename", operator_file_path, type="string")
    cmds.connectAttr(set_shader + ".out", standin_node + ".operators[0]", f=True)

    return standin_node


def load_abc(anim_abc_path, assets_dir):
    """Import Abc from a directory"""
    abc_filename = anim_abc_path.split("/")[-1]
    abc_char_name = abc_filename[:-len(abc_filename.split("_")[-1]) - 1]
    mod_folder = assets_dir + "\\" + abc_char_name + "\\abc"
    operator_folder = assets_dir + "\\" + abc_char_name + "\\publish"
    print("abc_filename       \t", abc_filename)
    print("abc_char_name      \t", abc_char_name)
    print("assets_dir         \t", assets_dir, os.path.exists(assets_dir))
    print("mod_folder         \t", mod_folder, os.path.exists(mod_folder))
    print("operator_folder    \t", operator_folder, os.path.exists(operator_folder))

    return create_char_standin(anim_abc_path,abc_char_name, mod_folder, operator_folder)


def import_anim():
    """Import selected alembic in the file dialog"""

    assets_dir = os.getenv("ASSETS_DIR")

    if assets_dir is None:
        raise Exception("Assets dir environment variable not found : Use an Illogic Launcher")

    list_abc = cmds.fileDialog2(fileFilter="*.abc", dialogStyle=2, fileMode=4)
    list_selected = []
    for abc_path in list_abc:
        standin = load_abc(abc_path, assets_dir)
        list_selected.append(standin)
    cmds.select(list_selected)
