import os
import re
import hou

def get_latest_version_folder(base_path, filename):
    """
    Scans the given base path to find the most recent folder containing the specified file.
    """
    # Regular expression to match the version number (v0001, v0002, etc.)
    version_regex = re.compile(r'v(\d{4})')
    
    # Get all versioned directories in the textures folder
    version_folders = [folder for folder in os.listdir(base_path) if version_regex.match(folder)]
    
    if not version_folders:
        return None

    # Sort folders by version number in descending order (latest version first)
    version_folders.sort(key=lambda x: int(version_regex.search(x).group(1)), reverse=True)

    # Check each version folder for the existence of the file
    for folder in version_folders:
        folder_path = os.path.join(base_path, folder)
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            return file_path

    # If no matching file is found, return None
    return None

def update_path(path):
    """
    Updates the texture path to the latest available version, checking each newer version until the file is found.
    """
    # Split the path into directory and file
    dir_path, filename = os.path.split(path)

    # Get the base path up to the version folder
    base_dir = os.path.dirname(dir_path)

    # Find the latest version folder that contains the texture file
    latest_texture_path = get_latest_version_folder(base_dir, filename)

    if latest_texture_path:
        # Return the new path if a newer texture was found
        return latest_texture_path
    else:
        # If no newer version is found with the file, return the original path
        return path

def run():
    """
    Updates texture file paths in mtlximage nodes to point to the latest available version.
    """
    # Dictionary to store old and new texture paths
    news_textures_dic = {}
    updates_info = ""

    # Iterate over all selected nodes
    for node in hou.selectedNodes():
        print(f"Selected Node: {node.path()}")

        # Iterate over all sub-nodes within the selected node
        for subnode in node.allSubChildren():
            if subnode.type().name() == "mtlximage":
                filename_parm = subnode.parm('file')
                if filename_parm:
                    path = filename_parm.eval()
                    new_path = update_path(path)
                    
                    # If the path has changed, prepare for the update
                    if path != new_path:
                        news_textures_dic[filename_parm] = new_path
                        updates_info += f"{path.split('/')[-1]} --> {new_path.split('/')[-1]}\n"
                        print(f"\nNode to update: '{subnode.path()}' \nOld: {path} \nNew: {new_path}")

    # Confirm updates with the user
    if news_textures_dic:
        confirmation_message = "The following textures will be updated:\n\n" + updates_info
        user_choice = hou.ui.displayMessage(confirmation_message, buttons=('Confirm', 'Cancel'), default_choice=0, close_choice=1)
        
        if user_choice == 0:
            # Apply updates if user confirms
            for parm, new_path in news_textures_dic.items():
                parm.set(new_path)
                print(f"Updated: {parm.name()} -> {new_path}")
        else:
            print("Update cancelled by the user.")
    else:
        hou.ui.displayMessage("No textures need updating.")

