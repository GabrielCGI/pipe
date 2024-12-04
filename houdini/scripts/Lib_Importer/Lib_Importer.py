import os
import re
from tkinter import Tk
import hou

def libImport():
    r = Tk()
    filepath = r.clipboard_get()
    filepath = '/'.join(filepath.split('\\'))

    filepath = filepath+'/Export/MAT/'

    def find_versions(directory):
        if not os.path.exists(directory):
            print(f"Error: The directory '{directory}' does not exist.")
            return None, 0
        versions = {}
        folder_count = 0  # Initialize the counter

        pattern = re.compile(r'^v(\d+)$')
        
        for item in os.listdir(directory):
            sub_dir = os.path.join(directory, item)
            if os.path.isdir(sub_dir):
                folder_count +=1
                current_folder = os.path.basename(os.path.normpath(sub_dir)).upper()
                versions[current_folder] = []
                iteration = 0
                for dir_name in os.listdir(sub_dir):              
                    dir_path = os.path.join(sub_dir, dir_name)
                    if os.path.isdir(dir_path):
                        match = pattern.match(dir_name)
                        if match:
                            version_number = int(match.group(1))
                            folder_path = dir_path.replace('\\', '/')
                            versions[current_folder].append((version_number, folder_path))
                            print('coucou'+versions)

                            

        for folder in versions:
            

            versions[folder].sort(reverse=True)
            # Sort by version number descending
        folder = folder.lower()


        return folder # Return both the versions dictionary and the folder count
    version = find_versions(filepath)

    file = filepath + '/'+ version + '/'
    finalFile = file + os.listdir(file)[0]


    print(finalFile)
    active_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    location = active_pane.pwd()

    location.loadItemsFromFile(finalFile)
    active_pane.homeToSelection()

