import hou

# Replacement strings
old_prefix = "op:/stage/copnet_ROAD"
new_prefix = (
    "I:/renault_2411/03_Production/Shots/rollingShot/010/Scenefiles/"
    "Lighting/Lighting/render"
)
extension = ".exr"

# Get all selected nodes
selected_nodes = hou.selectedNodes()

for node in selected_nodes:
    # Convert tuple from allSubChildren() to a list to avoid the TypeError
    all_descendants = [node] + list(node.allSubChildren())

    for descendant in all_descendants:
        # Check if this node has a "file" parameter
        file_parm = descendant.parm("file")
        if file_parm is not None:
            current_value = file_parm.eval()

            # If it starts with the old prefix, replace it and append .exr
            if current_value.startswith(old_prefix):
                new_value = current_value.replace(old_prefix, new_prefix) + extension
                file_parm.set(new_value)
                print(f"Updated '{descendant.path()}' file parm: {new_value}")
