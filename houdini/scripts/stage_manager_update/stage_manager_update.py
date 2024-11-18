import hou

import re
import os
from glob import glob

print_debug=True
print_info=True
    
def pinfo(toPrint):
    if print_info is True:
        print("Info - " + str(toPrint))
    else:
        pass

def pdebug(toPrint):
    if print_debug is True:
        print("Debug - " + str(toPrint))
    else:
        pass
    
def get_latest_version(asset_path):
    """
    Get the last version of an asset.

    Parameters:
    asset_path (str) : Path to an asset

    Return : (str) Path to the last version of an asset
    """

    # Split the directory path and the file name
    directory_path, file_name = os.path.split(asset_path)
    
    ## Create a generic name for the asset by replacing
    # the version number and the extension 
    directory_pattern = re.sub(r'v\d{3,4}', 'v*', directory_path)
    file_pattern = re.sub(r'v\d{3,4}', 'v*', file_name)
    file_pattern = re.sub(r'\.(usdc|usd|usda)$', '.usd*', file_pattern)
    search_pattern = os.path.join(directory_pattern, file_pattern)

    # Search every differents versions of an asset
    matching_files = glob(search_pattern, recursive=True)
    
    matching_files = [f for f in matching_files if re.search(r'v(\d{3,4})', f)]
    matching_files.sort(
        key=lambda x: int(re.search(r'v(\d{3,4})', x).group(1)),
        reverse=True
    )
    if matching_files:
        pinfo("Matching files %s"%(matching_files[0]))
    else:
        pinfo("NO MATCHING FILE FOUND FOR %s"%asset_path)
    return matching_files[0] if matching_files else None

def checkUpdate():
    """
    Check for each asset if there is an uptade available,
    Then ask the user if he want to uptate them.
    
    """
    
    node = hou.selectedNodes()
    
    ## Check if a node is selected
    if (node and node[0].type().name()=="stagemanager"):      
        
        # Take the number of changes
        node = node[0]
        assets_update_dic = {}
        pdebug(f"Selected Node: {node.path()}")
        num_changes_parm = node.parm('num_changes')
        num_changes = num_changes_parm.eval()

        updates_info = ""
        
        # Check each asset
        for i in range(1, num_changes + 1):
            reffile_path_parm_name = f"reffilepath{i}"
            reffile_parm = node.parm(reffile_path_parm_name)
            asset_path = reffile_parm.eval()
            asset_path = asset_path.replace("\\", '/')
            
            # An asset is found
            if asset_path:
                
                # Check if it is the latest version of that asset
                latest_asset_path = get_latest_version(asset_path)
                if not latest_asset_path:
                    pinfo("Could not find latest asset path for %s"%(asset_path))
                    continue
                latest_asset_path = latest_asset_path.replace("\\",'/')
                if asset_path != latest_asset_path:
                    pdebug(f"Found at {reffile_path_parm_name}")
                    pdebug(asset_path)
                    pdebug(latest_asset_path)
                    updates_info += (f"{asset_path.split('/')[-1]}"
                                    + " --> " 
                                    +f"{latest_asset_path.split('/')[-1]}\n")
                    assets_update_dic[reffile_parm] = latest_asset_path
                    
        # Confirm updates with the user
        if assets_update_dic:
            confirmation_message = ("The following assets" 
                                    + "will be updated:\n\n" 
                                    + updates_info)
            user_choice = hou.ui.displayMessage(
                confirmation_message, buttons=('Confirm', 'Cancel'), 
                default_choice=0, close_choice=1)    
            
            if user_choice == 0:       
                # Update each assets
                for parm, new_path in assets_update_dic.items():
                    parm.set(new_path)
                    pinfo(f"Updated: {parm.name()} -> {new_path}")
            else:
                pinfo("Update cancelled by the user.")
        else:
            pinfo("No assets need updating.")
            hou.ui.displayMessage("No assets need updating.")
    else:
        print("No nodes selected.")
        hou.ui.displayMessage("No nodes selected.")
