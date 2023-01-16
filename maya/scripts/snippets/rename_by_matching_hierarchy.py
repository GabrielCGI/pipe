import pymel.core as pm

# Assume you have a selection of two nodes, with the first node being the source
# and the second node being the target
source_node, target_node = pm.ls(selection=True, type='transform')

# Get all descendants of the first node
source_descendants = pm.listRelatives(source_node, allDescendents=True, type='transform')

# Get all descendants of the second node
target_descendants = pm.listRelatives(target_node, allDescendents=True, type='transform')

# Iterate over the descendants of the second node and rename them by index number
for i, descendant in enumerate(target_descendants):
    pm.rename(descendant, source_descendants[i].name().split("|")[-1])
    