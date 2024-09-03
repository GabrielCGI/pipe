tocopy = hou.selectedItems()
p = tocopy[0].parent()
result, name = hou.ui.readInput('ClipBoard Name:')

if name:
    filepath = 'I:\tmp\houdini_Clipboard'+ name + '.cpio'
    p.saveItemsToFile(tocopy, filepath)
    hou.ui.displayMessage('Clipboard Saved as : '+ filepath)
else:
    hou.ui.displayMessage('Canceled / No name Set')