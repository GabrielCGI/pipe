import hou
import os
import getpass  # For getting the current user name

def paste():
    """Paste an item from I:/tmp/houdini_Clipboard"""
    active_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    location = active_pane.pwd()
    project_path = hou.hipFile.path().split('/')[1]+'/'

    filepath = hou.ui.selectFile(
        title="Load Clipboard File",
        start_directory="I:/tmp/houdini_Clipboard/"+project_path,
        pattern="*.cpio",  # Filter only CPIO files
        chooser_mode=hou.fileChooserMode.Read
    )

    if filepath:
        location.loadItemsFromFile(filepath)
        hou.ui.displayMessage(f"Items loaded from {filepath}")
    else:
        hou.ui.displayMessage("No file selected")

def copy():
    """Copy an item to I:/tmp/houdini_Clipboard"""
    # Get the selected items in Houdini
    tocopy = hou.selectedItems()
    project_path = hou.hipFile.path().split('/')[1]+'/'
    # Check if there is anything selected
    if tocopy:
        # Ensure directory exists
        clipboard_dir = "I:/tmp/houdini_Clipboard/"+ project_path
        if not os.path.exists(clipboard_dir):
            os.makedirs(clipboard_dir)

        # Get the current user name
        user_name = getpass.getuser()
        user_name = user_name.replace('.', '_')

        # Open a file dialog to choose the name and location of the clipboard file
        file_path = hou.ui.selectFile(
            start_directory=clipboard_dir,
            title="Save Clipboard File",
            chooser_mode=hou.fileChooserMode.Write
        )

        # Check if a file path was provided
        if file_path:
            # Extract the base file name without extension
            base_name, file_extension = os.path.splitext(file_path)

            # Add the user's name to the file name
            base_name = base_name.replace('_'+user_name, '')
            base_name += f"_{user_name}"
            

            # Automatically replace any extension with ".cpio"
            if file_extension:
                file_path = base_name + ".cpio"
            elif not file_extension:
                # If no extension, append ".cpio"
                file_path = base_name + ".cpio"
            
            
            
            # Save the selected items to the file
            p = tocopy[0].parent()
            p.saveItemsToFile(tocopy, file_path)
            hou.ui.displayMessage(f"Clipboard saved as: {file_path}")
        else:
            hou.ui.displayMessage("Canceled / No name set")
    else:
        hou.ui.displayMessage("No item selected")
