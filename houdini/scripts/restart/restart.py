import hou
import os
import subprocess
import sys

def restart_houdini():
    """
    Routine to save the current houdini session then restart it.
    """
    # Save the current file
    current_file = hou.hipFile.name()
    
    if not current_file or current_file == "untitled.hip":
        hou.ui.displayMessage("Please save your file before restarting Houdini.")
        return
    
    # Ask the user if he really want to restart
    user_choice = hou.ui.displayMessage(
                f"Do you really want to restart houdini ?\n{current_file}", buttons=('Confirm', 'Cancel'), 
                default_choice=0, close_choice=1)    
            
    if user_choice != 0:
        hou.ui.displayMessage("Restart cancelled by user")
        return
    
    try:
        hou.hipFile.save()
        print('Scene saved.')
    except hou.Error as e:
        hou.ui.displayMessage(f"Failed to save file: {str(e)}")
        return
    
    # Get the Houdini executable and arguments
    houdini_executable = sys.executable

    # Relaunch Houdini with the current file
    try:
        subprocess.Popen([houdini_executable] + [current_file])
    except Exception as e:
        hou.ui.displayMessage(f"Failed to restart Houdini: {str(e)}")
        return
    
    # Close the current Houdini instance
    hou.exit()