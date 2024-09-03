
import hou

def paste():
    """Paste an item from I:/tmp/houdini_Clipboard"""
    active_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    location = active_pane.pwd()
    filepath = hou.ui.selectFile(title="Load Clipboard File",
                                 start_directory = "I:/tmp/houdini_Clipboard/",
                                 pattern="*.cpio",  # Filter only JSON files
                                 chooser_mode=hou.fileChooserMode.Read)

    if filepath:  
        location.loadItemsFromFile(filepath)
    else:
        hou.ui.displayMessage("No file selected")

def copy():
    """Copy an item in I:/tmp/houdini_Clipboard"""
    # Get the selected items in Houdini
    tocopy = hou.selectedItems()

# Check if there is anything selected
    if tocopy:
        p = tocopy[0].parent()

    # Open a file dialog to choose the name and location of the clipboard file
        file_path = hou.ui.selectFile(start_directory="I:/tmp/houdini_Clipboard", 
                                    title="Save Clipboard File", 
                                    pattern="*.cpio", 
                                    chooser_mode=hou.fileChooserMode.Write)

    # Check if a file path was provided (i.e., the user did not cancel the dialog)
        if file_path:
            p.saveItemsToFile(tocopy, file_path)
            hou.ui.displayMessage("Clipboard Saved as: " + file_path)
        else:
            hou.ui.displayMessage("Canceled / No name Set")
    else:
        hou.ui.displayMessage("No item selected")