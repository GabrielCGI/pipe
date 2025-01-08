import hou
import os
import subprocess
import sys

def restart_houdini():
    # Save the current file
    current_file = hou.hipFile.name()
    
    if not current_file or current_file == "untitled.hip":
        hou.ui.displayMessage("Please save your file before restarting Houdini.")
        return
    
    try:
        hou.hipFile.save()
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