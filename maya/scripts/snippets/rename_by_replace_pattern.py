import pymel.core as pm

# Get current selection
sel = pm.ls(selection=True)

# Iterate through each node in selection
for node in sel:
    # Get current node name
    name = node.name()
    # Replace "_R_" with "_L_" in the name
    new_name = name.replace("_L_","_R_")
    # Rename the node
    node.rename(new_name)