import hou
import re
from glob import glob
import os

def update_path_to_project_relative(original_path):
    target_path_pattern = re.compile(r"(?i)I:/interior/assets/houdini/usd/")
    replacement = "$HIP/"
    updated_path = target_path_pattern.sub(replacement, original_path, count=1)
    print(updated_path)
    return updated_path

def standardize_path_separators(path):
    return path.replace("\\", '/')

def get_latest_version(asset_directory):
    directory_path, file_name = os.path.split(asset_directory)
    directory_pattern = re.sub(r'v\d{4}', 'v*', directory_path)
    file_pattern = re.sub(r'v\d{4}', 'v*', file_name)
    file_pattern = re.sub(r'\.(usdc|usd|usda)$', '.usd*', file_pattern)
    search_pattern = os.path.join(directory_pattern, file_pattern)
    matching_files = glob(search_pattern, recursive=True)
    matching_files.sort(key=lambda x: int(re.search(r'v(\d{4})', x).group(1)), reverse=True)
    return matching_files[0] if matching_files else None

def run():
    node = hou.selectedNodes()[0]
    assets_update_dic = {}
    print(f"Selected Node: {node.path()}")
    num_changes_parm = node.parm('num_changes')
    num_changes = num_changes_parm.eval()

    updates_info = ""
    for i in range(1, num_changes + 1):
        reffile_path_parm_name = f"reffilepath{i}"
        reffile_parm = node.parm(reffile_path_parm_name)
        asset_path = reffile_parm.eval()
        asset_path = standardize_path_separators(asset_path)
        if asset_path:
            latest_asset_path = standardize_path_separators(get_latest_version(asset_path))
            if asset_path != latest_asset_path:
                print("Found at %s "%reffile_path_parm_name)
                print(asset_path)
                print(latest_asset_path)
                updates_info += f"{asset_path.split('/')[-1]} --> {latest_asset_path.split('/')[-1]}\n"
                assets_update_dic[reffile_parm] = latest_asset_path

    # Confirm updates with the user
    if assets_update_dic:
        confirmation_message = "The following assets will be updated:\n\n" + updates_info
        user_choice = hou.ui.displayMessage(confirmation_message, buttons=('Confirm', 'Cancel'), default_choice=0, close_choice=1)
        if user_choice == 0:
            for parm, new_path in assets_update_dic.items():
                parm.set(new_path)
                print(f"Updated: {parm.name()} -> {new_path}")
        else:
            print("Update cancelled by the user.")
    else:
        hou.ui.displayMessage("No assets need updating.")
