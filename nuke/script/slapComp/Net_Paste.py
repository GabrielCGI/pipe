active_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
location = active_pane.pwd()
filepath = hou.ui.selectFile(title="Select file to load",
                                  start_directory = 'D:/test',
                                  pattern="*.cpio",  # Filter to show only JSON files
                                  chooser_mode=hou.fileChooserMode.Read)

if filepath:  
    location.loadItemsFromFile(filepath)
else:
    hou.ui.displayMessage('No file selected')