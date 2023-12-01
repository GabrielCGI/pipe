import pymel.core as pm
import os
import shutil
from datetime import datetime

def main():
    # Get the current scene path
    current_scene_path = pm.sceneName()
    current_selection = pm.ls(sl=True)
    # Selection to string
    selection_str = ', '.join([str(s) for s in current_selection]) if current_selection else "No selection"
    message = f"Current Selection: {selection_str}\n Do you want to proceed with the export?"
    result = pm.confirmDialog(title='Confirm Export', message=message, button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
    if result == 'Yes':
        # Export the selected objects to the new location

        print(f'Animation published start')
    else:
        print("Export cancelled.")
        pm.error("ABORT EXPORT")
        return

    # Parse the destination directory from the current scene path
    parent_directory = os.path.dirname(current_scene_path)
    grandparent_directory = os.path.dirname(parent_directory)
    destination_dir = os.path.join(grandparent_directory, 'abc')

    # Ensure the destination directory exists
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Construct the file name based on the parent directory name
    scene_name = os.path.basename(grandparent_directory)
    destination_file_name = f'{scene_name}_anim_lib.mb'  # Maya binary format

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
        backup_file_name = f'{scene_name}_anim_lib_{timestamp}.mb'
        backup_path = os.path.join(backup_dir, backup_file_name)

        # Move the existing file to the backup directory
        shutil.move(destination_path, backup_path)
        print(f'Existing file backed up to {backup_path}')
        pm.exportSelected(destination_path, preserveReferences=True,type="mayaBinary")
        print("SUCCES !\n %s"%destination_path)
        pm.warning("Export succes ! %s"%destination_path)
