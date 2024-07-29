import hou



def update_path(path):
    # Define the part of the path to replace and what to replace it with
    old_base = "I:/2406_chickenverse"
    new_base = "$PRISM_JOB"

    # Replace the old base with the new base in the path
    updated_path = path.replace(old_base, new_base)
    return updated_path

def list_mtlximage_filenames():
    # Iterate over all selected nodes
    for node in hou.selectedNodes():
        # Print the path of the selected node
        print(f"Selected Node: {node.path()}")

        # Iterate over all sub-nodes within the selected node
        for subnode in node.allSubChildren():
            # Check if the subnode is an mtlximage node
            if subnode.type().name() == "mtlximage":
                # Try to access the filename parameter
                filename_parm = subnode.parm('file')
                if filename_parm:
                    path = filename_parm.eval()
                    new_path = update_path(path)
                    filename_parm.set(new_path)
                    # Print the filename
                    print(f"\nNode updated '{subnode.path()}' \nOld: {path} \nNew: {new_path}")

# Execute the function
list_mtlximage_filenames()
