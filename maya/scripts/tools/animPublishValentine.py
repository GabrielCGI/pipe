import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import os
import shutil
from datetime import datetime

def build_lib_path_and_backup(extension):
    current_scene_path = pm.sceneName()
    # Parse the destination directory from the current scene path
    parent_directory = os.path.dirname(current_scene_path)
    grandparent_directory = os.path.dirname(parent_directory)
    destination_dir = os.path.join(grandparent_directory, 'abc')
    print("Destination: %s"%(destination_dir))
    # Ensure the destination directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Construct the file name based on the parent directory name
    scene_name = os.path.basename(grandparent_directory)
    destination_file_name = f'{scene_name}_anim_lib{extension}'
    # Full path for the destination file
    destination_path = os.path.join(destination_dir, destination_file_name)

    # Check if the file already exists
    if os.path.exists(destination_path):
        # Construct backup directory path
        backup_dir = os.path.join(destination_dir, 'oldLib')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Generate a timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        # Construct backup file path
        backup_file_name = f'{scene_name}_anim_lib_{timestamp}{extension}'
        backup_path = os.path.join(backup_dir, backup_file_name)

        # Move the existing file to the backup directory
        shutil.move(destination_path, backup_path)
        print(f'Existing file backed up to {backup_path}')
    return destination_path

def replace_references_path_with_variable():
    # Get all references in the scene
    all_references = cmds.ls(type='reference')

    for ref in all_references:
        # Skip the default reference and any reference not associated with a file
        if "sharedReferenceNode" in ref or "UNKNOWN" in ref:
            print("skip"+ref)
            continue

        ref_node = cmds.referenceQuery(ref, referenceNode=True)
        # Check if the reference is a top-level reference
        # If it has no parent reference, it's a top-level reference
        if cmds.referenceQuery(ref, parent=True, referenceNode=True) is None:
            # Get the file path of the reference
            ref_file = cmds.referenceQuery(ref, filename=True, unresolvedName=True)
            print (ref_file)

            # Replace "I:" with "$DISK_I" in the file path
            new_ref_file = ref_file.replace('I:', '$DISK_I')
            print(new_ref_file)
            if new_ref_file != ref_file:
                print ("Replaced ref path with: new_ref_file ")
                # Load the reference with the new path
                cmds.file(new_ref_file, loadReference=ref)

def abcExport(destination_path_abc):

    # Get the current scene name and replace its extension with .abc
    current_scene = pm.sceneName()
    abc_file_path = destination_path_abc
    abc_file_path= abc_file_path.replace("\\","/")

    # Get the current timeline's min and max frame range
    min_frame = pm.playbackOptions(query=True, minTime=True)
    max_frame = pm.playbackOptions(query=True, maxTime=True)

    # Get the current selection
    selected_geos = pm.ls(selection=True)

    # Construct the root part of the command based on the selection
    root_command = ""
    for geo in selected_geos:
        root_command += " -root {}".format(geo.fullPath())

    # Construct the full Alembic export command
    abc_export_command = '-frameRange {} {} -stripNamespaces -uvWrite -worldSpace -writeVisibility -dataFormat ogawa {} -file "{}"'.format(min_frame, max_frame, root_command, abc_file_path)
    print(abc_export_command)
    pm.AbcExport(j=abc_export_command)
    # Export the selected object as an Alembic file
def main():
    # Get the current scene path
    current_scene_path = pm.sceneName()
    current_selection = pm.ls(sl=True)
    # Selection to string
    selection_str = ', '.join([str(s) for s in current_selection]) if current_selection else "No selection"
    message = f"Current Selection: {selection_str}\n Do you want to proceed with the export?"
    result = pm.confirmDialog(title='Confirm Export', message=message, button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
    if result != 'Yes':
        print("Export cancelled.")
        pm.error("ABORT EXPORT")
        return


    destination_path = build_lib_path_and_backup(".mb")
    replace_references_path_with_variable()
    mel.eval('IncrementAndSave;')
    pm.exportSelected(destination_path, preserveReferences=True,type="mayaBinary")

    print("SUCCES !\n %s"%destination_path)
    destination_path_abc = build_lib_path_and_backup(".abc")
    print(destination_path_abc)
    #abcExport(destination_path_abc)
    #print("SUCCES !\n %s"%destination_path_abc)
    pm.warning("Export succes ! %s"%destination_path)
