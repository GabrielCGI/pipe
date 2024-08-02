import hou

import re

def update_path(original_path):
    # Define the part to replace (case-insensitive)
    part_to_replace = re.compile(r"(?i)I:/interior/assets/houdini/usd/")
    replacement = "$HIP/"

    # Replace the part with $HIP
    new_path = part_to_replace.sub(replacement, original_path, count=1)
    print(new_path)
    return new_path


def stage_manager_update():
    print("yo")
    # Iterate over all selected nodes
    node = hou.selectedNodes()[0]
        # Print the path of the selected node
    print(f"Selected Node: {node.path()}")

    numChanges_parm = node.parm('num_changes')
    count = numChanges_parm.valueAsData()
    for i in range(1,count+1):
        reffilepath_str= f"reffilepath{i}"
        reffilepath = node.parm(reffilepath_str)
        if reffilepath:
            updated_path =  update_path(reffilepath.valueAsData())
            reffilepath.set(updated_path)


# Execute the function
stage_manager_update()